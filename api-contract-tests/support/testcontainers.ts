import { PostgreSqlContainer } from '@testcontainers/postgresql';
import { RedisContainer } from '@testcontainers/redis';
import { Client } from 'pg';
import * as fs from 'fs/promises';
import * as path from 'path';

interface DbConfig {
  postgres: {
    host: string;
    port: number;
    db: string;
    user: string;
    password: string;
  };
  redis: {
    host: string;
    port: number;
  };
}

class TestContainersManager {
  private static instance: TestContainersManager;
  private postgres?: PostgreSqlContainer;
  private redis?: RedisContainer;
  private started = false;

  private constructor() {}

  static getInstance(): TestContainersManager {
    if (!TestContainersManager.instance) {
      TestContainersManager.instance = new TestContainersManager();
    }
    return TestContainersManager.instance;
  }

  async start() {
    if (this.started) return this.getConfig();

    console.log('🚀 Starting Testcontainers...');
    console.log('   This may take 30-60 seconds on first run (downloading images)...');

    try {
      // Start PostgreSQL with PostGIS
      // Bind to all interfaces (0.0.0.0) so containers can reach it
      this.postgres = await new PostgreSqlContainer('postgis/postgis:13-3.1')
        .withDatabase('penhas_test')
        .withUsername('postgres')
        .withPassword('trustme')
        .withReuse()
        .start();

      console.log(`✅ PostgreSQL started: ${this.postgres.getHost()}:${this.postgres.getPort()}`);

      // Start Redis
      this.redis = await new RedisContainer('redis:7-alpine')
        .withReuse()
        .start();

      console.log(`✅ Redis started: ${this.redis.getHost()}:${this.redis.getPort()}`);
    } catch (error: any) {
      console.error('❌ Error starting Testcontainers:', error.message);
      console.error('   Make sure Docker is running: docker ps');
      throw error;
    }

    // Initialize database schema
    await this.initializeSchema();

    this.started = true;
    return this.getConfig();
  }

  async stop() {
    if (!this.started) return;

    console.log('🛑 Stopping Testcontainers...');
    await this.postgres?.stop();
    await this.redis?.stop();
    this.started = false;
    console.log('✅ Testcontainers stopped');
  }

  private async initializeSchema() {
    const client = new Client({
      host: this.postgres!.getHost(),
      port: this.postgres!.getPort(),
      database: 'penhas_test',
      user: 'postgres',
      password: 'trustme',
    });

    try {
      await client.connect();
      
      // Enable PostGIS
      await client.query('CREATE EXTENSION IF NOT EXISTS postgis');
      console.log('✅ PostGIS extension enabled');
      
      // Load schema from Perl Sqitch migrations
      const schemaLoaded = await this.loadSqitchSchema(client);
      
      if (!schemaLoaded) {
        console.log('⚠️  Sqitch migrations not found, using minimal schema');
        await this.createMinimalSchema(client);
      }
      
      console.log('✅ Database schema initialized');
    } finally {
      await client.end();
    }
  }

  private async loadSqitchSchema(_client: Client): Promise<boolean> {
    try {
      // Try to load from Perl project
      const sqitchDir = path.join(process.cwd(), '..', 'api', 'deploy_db');
      const planFile = path.join(sqitchDir, 'sqitch.plan');

      // Check if plan file exists
      try {
        await fs.access(planFile);
      } catch {
        return false;
      }

      // Read sqitch.plan to get deployment order
      const planContent = await fs.readFile(planFile, 'utf-8');
      const deployFiles: string[] = [];

      // Parse sqitch.plan format
      // Format: migration_name [dependencies] date author # comment
      const lines = planContent.split('\n');
      for (const line of lines) {
        const trimmed = line.trim();
        // Skip comments and empty lines
        if (!trimmed || trimmed.startsWith('%') || trimmed.startsWith('#')) {
          continue;
        }

        // Extract migration name (first word)
        const match = trimmed.match(/^(\S+)/);
        if (match) {
          const migrationName = match[1];
          const deployFile = path.join(sqitchDir, 'deploy', `${migrationName}.sql`);
          deployFiles.push(deployFile);
        }
      }

      // Execute each migration in its own connection.
      // Migration .sql files use BEGIN/COMMIT blocks — if any statement fails
      // inside a transaction, PostgreSQL aborts the entire transaction and all
      // subsequent queries on that connection return "current transaction is
      // aborted". A fresh connection per file isolates these failures.
      for (const file of deployFiles) {
        try {
          await fs.access(file);
        } catch {
          console.warn(`⚠️  Migration file not found: ${path.basename(file)}`);
          continue;
        }

        const migrationClient = new Client({
          host: this.postgres!.getHost(),
          port: this.postgres!.getPort(),
          database: 'penhas_test',
          user: 'postgres',
          password: 'trustme',
        });

        try {
          await migrationClient.connect();
          const sql = await fs.readFile(file, 'utf-8');
          await migrationClient.query(sql);
          console.log(`✅ Applied migration: ${path.basename(file)}`);
        } catch (error: any) {
          if (!error.message.includes('already exists') &&
              !error.message.includes('does not exist') &&
              !error.message.includes('duplicate key')) {
            console.warn(`⚠️  Warning in ${path.basename(file)}: ${error.message.substring(0, 200)}`);
          } else {
            console.log(`✅ Applied migration: ${path.basename(file)} (idempotent)`);
          }
        } finally {
          await migrationClient.end();
        }
      }

      return true;
    } catch (error: any) {
      console.log(`⚠️  Error loading Sqitch schema: ${error.message}`);
      return false;
    }
  }

  private async createMinimalSchema(client: Client) {
    // Essential tables matching Perl schema
    await client.query(`
      -- clientes table
      CREATE TABLE IF NOT EXISTS clientes (
        id BIGSERIAL PRIMARY KEY,
        cpf_hash VARCHAR(200) NOT NULL,
        email VARCHAR(200) NOT NULL,
        nome_completo VARCHAR(200) NOT NULL,
        apelido VARCHAR(200) NOT NULL,
        genero VARCHAR(100) NOT NULL,
        status VARCHAR(20) DEFAULT 'active',
        login_status VARCHAR(20) DEFAULT 'OK',
        senha_sha256 VARCHAR(200) NOT NULL,
        dt_nasc DATE NOT NULL,
        cep VARCHAR(8) NOT NULL,
        created_on TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );
      CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes(email);
      CREATE INDEX IF NOT EXISTS idx_clientes_cpf_hash ON clientes(cpf_hash);
      
      -- clientes_active_sessions table
      CREATE TABLE IF NOT EXISTS clientes_active_sessions (
        id BIGSERIAL PRIMARY KEY,
        cliente_id BIGINT NOT NULL REFERENCES clientes(id)
      );
      
      -- login_logs table
      CREATE TABLE IF NOT EXISTS login_logs (
        id BIGSERIAL PRIMARY KEY,
        remote_ip VARCHAR(200) NOT NULL,
        cliente_id BIGINT REFERENCES clientes(id),
        app_version VARCHAR(800),
        created_at TIMESTAMP WITH TIME ZONE
      );
    `);
  }

  getConfig(): DbConfig {
    if (!this.postgres || !this.redis) {
      throw new Error('Containers not started. Call start() first.');
    }
    
    return {
      postgres: {
        host: this.postgres.getHost(),
        port: this.postgres.getPort(),
        db: 'penhas_test',
        user: 'postgres',
        password: 'trustme',
      },
      redis: {
        host: this.redis.getHost(),
        port: this.redis.getPort(),
      },
    };
  }
}

export const testContainers = TestContainersManager.getInstance();

