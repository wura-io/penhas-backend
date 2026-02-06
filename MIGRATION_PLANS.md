# 🏗️ Perl → Python FastAPI Migration Plan
## **Agent.MD Format** | **Stack: Cucumber.js + Supertest + Testcontainers**

---

## 📋 Executive Summary

**Objective**: Migrate Perl Mojolicious API to Python FastAPI using **Cucumber.js Gherkin tests** as golden master contract. Tests written against Perl first, then drive Python TDD.

**Tech Stack**:
- ✅ **Cucumber.js** (Gherkin `.feature` files)
- ✅ **Supertest** (HTTP assertions)
- ✅ **Testcontainers** (isolated PostgreSQL/Redis)
- ✅ **TypeScript** (type-safe step definitions)
- ✅ **Zero boilerplate** (minimal config, pure Gherkin)

---

## 📁 Repository Structure

```
institutoazmina-penhas-backend/
├── api/                          # 🟠 LEGACY Perl Mojolicious
│   ├── lib/Penhas/
│   ├── t/api/*.t
│   └── deploy_db/                # Sqitch migrations
│
├── api-v2/                       # 🟢 NEW Python FastAPI
│   ├── app/
│   ├── tests/
│   └── ...
│
└── api-contract-tests/           # 🟡 Cucumber.js Contract Tests
    ├── features/
    │   ├── auth.feature
    │   ├── timeline.feature
    │   ├── ponto-apoio.feature
    │   └── ...
    ├── step-definitions/
    │   ├── api-steps.ts          # HTTP steps (Supertest)
    │   ├── db-steps.ts           # Database steps
    │   ├── hooks.ts              # Before/After hooks
    │   └── world.ts              # Shared context
    ├── support/
    │   ├── testcontainers.ts     # Testcontainers manager
    │   ├── helpers.ts            # Utilities
    │   └── schema-loader.ts      # Load Perl schema
    ├── cucumber.js               # Cucumber config
    ├── tsconfig.json
    ├── package.json
    └── README.md
```

---

## 🎯 Phase 1: Setup Cucumber.js + Testcontainers

### Step 1.1: Initialize Project

```bash
cd api-contract-tests
npm init -y

# Core dependencies
npm install @cucumber/cucumber supertest axios @testcontainers/postgresql @testcontainers/redis pg

# Dev dependencies
npm install -D typescript ts-node @types/node @types/supertest @types/pg nodemon

# Optional: LLM helpers
npm install -D @faker-js/faker
```

---

### Step 1.2: TypeScript Configuration

**File**: `api-contract-tests/tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": ".",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "moduleResolution": "node",
    "types": ["node", "@cucumber/cucumber"]
  },
  "include": [
    "**/*.ts",
    "**/*.feature"
  ],
  "exclude": [
    "node_modules",
    "dist"
  ]
}
```

---

### Step 1.3: Cucumber Configuration

**File**: `api-contract-tests/cucumber.js`
```javascript
export default {
  // Gherkin feature files
  paths: ['features/**/*.feature'],
  
  // Step definitions
  require: [
    'step-definitions/**/*.ts',
    'support/**/*.ts'
  ],
  
  // TypeScript support
  requireModule: ['ts-node/register'],
  
  // Formatters
  format: [
    'progress',
    'html:reports/report.html',
    'json:reports/report.json'
  ],
  
  // Tags filtering
  tags: 'not @wip',
  
  // Timeouts
  timeout: 30000,
  
  // Publish report (optional)
  publishQuiet: true
};
```

---

### Step 1.4: Package Scripts

**File**: `api-contract-tests/package.json`
```json
{
  "name": "penhas-contract-tests",
  "version": "1.0.0",
  "scripts": {
    "build": "tsc",
    "test": "cucumber-js",
    "test:perl": "TARGET=perl cucumber-js --tags '@perl'",
    "test:python": "TARGET=python cucumber-js --tags '@python'",
    "test:auth": "cucumber-js --tags '@auth'",
    "test:timeline": "cucumber-js --tags '@timeline'",
    "test:stable": "for i in {1..100}; do npm run test:perl || exit 1; done",
    "test:watch": "nodemon --watch 'features/**/*.feature' --watch 'step-definitions/**/*.ts' --exec 'npm test'",
    "report": "open reports/report.html"
  },
  "devDependencies": {
    "@cucumber/cucumber": "^10.0.1",
    "@faker-js/faker": "^8.4.1",
    "@testcontainers/postgresql": "^10.0.0",
    "@testcontainers/redis": "^10.0.0",
    "@types/pg": "^8.10.9",
    "@types/supertest": "^6.0.2",
    "axios": "^1.6.7",
    "nodemon": "^3.0.3",
    "pg": "^8.11.3",
    "supertest": "^6.3.4",
    "ts-node": "^10.9.2",
    "typescript": "^5.3.3"
  }
}
```

---

## 🗄️ Phase 2: Testcontainers Setup (Isolated Database)

### Step 2.1: Testcontainers Manager

**File**: `api-contract-tests/support/testcontainers.ts`
```typescript
import { PostgreSqlContainer } from '@testcontainers/postgresql';
import { RedisContainer } from '@testcontainers/redis';
import { Client } from 'pg';

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

    // Start PostgreSQL with PostGIS
    this.postgres = await new PostgreSqlContainer('postgis/postgis:13-3.1')
      .withDatabase('penhas_test')
      .withUsername('postgres')
      .withPassword('trustme')
      .start();

    console.log(`✅ PostgreSQL started: ${this.postgres.getHost()}:${this.postgres.getPort()}`);

    // Start Redis
    this.redis = await new RedisContainer()
      .withImage('redis:7-alpine')
      .start();

    console.log(`✅ Redis started: ${this.redis.getHost()}:${this.redis.getPort()}`);

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
      
      // Load schema from Perl Sqitch migrations (if available)
      const schemaLoaded = await this.loadSqitchSchema(client);
      
      if (!schemaLoaded) {
        // Fallback: minimal schema
        console.log('⚠️  Sqitch migrations not found, using minimal schema');
        await this.createMinimalSchema(client);
      }
      
      console.log('✅ Database schema initialized');
    } finally {
      await client.end();
    }
  }

  private async loadSqitchSchema(client: Client): Promise<boolean> {
    try {
      // Try to load from Perl project
      const fs = await import('fs/promises');
      const path = await import('path');
      
      const sqitchDir = path.join(process.cwd(), '..', 'api', 'deploy_db');
      const planFile = path.join(sqitchDir, 'sqitch.plan');
      
      if (!fs.existsSync(planFile)) {
        return false;
      }
      
      // Read sqitch.plan to get deployment order
      const plan = await fs.readFile(planFile, 'utf-8');
      const deployFiles = plan
        .split('\n')
        .filter(line => !line.startsWith('#') && line.trim())
        .map(line => {
          const match = line.match(/^(\S+)/);
          return match ? `${sqitchDir}/deploy/${match[1]}.sql` : null;
        })
        .filter(Boolean) as string[];
      
      // Execute each migration
      for (const file of deployFiles) {
        if (fs.existsSync(file)) {
          const sql = await fs.readFile(file, 'utf-8');
          await client.query(sql);
          console.log(`✅ Applied migration: ${path.basename(file)}`);
        }
      }
      
      return true;
    } catch (error) {
      console.log(`⚠️  Error loading Sqitch schema: ${error}`);
      return false;
    }
  }

  private async createMinimalSchema(client: Client) {
    // Essential tables matching Perl schema
    await client.query(`
      -- clientes table
      CREATE TABLE IF NOT EXISTS clientes (
        id BIGSERIAL PRIMARY KEY,
        cpf_hash VARCHAR(64) NOT NULL,
        email VARCHAR(255) NOT NULL,
        nome_completo VARCHAR(255) NOT NULL,
        apelido VARCHAR(100),
        genero VARCHAR(50),
        status VARCHAR(20) DEFAULT 'active',
        login_status VARCHAR(20) DEFAULT 'OK',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );
      CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes(email);
      CREATE INDEX IF NOT EXISTS idx_clientes_cpf_hash ON clientes(cpf_hash);
      
      -- ponto_apoio_categoria table
      CREATE TABLE IF NOT EXISTS ponto_apoio_categoria (
        id SERIAL PRIMARY KEY,
        label VARCHAR(255) NOT NULL,
        color VARCHAR(50),
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );
      
      -- ponto_apoio table
      CREATE TABLE IF NOT EXISTS ponto_apoio (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(255) NOT NULL,
        categoria_id INTEGER REFERENCES ponto_apoio_categoria(id),
        endereco VARCHAR(500),
        latitude NUMERIC(10, 8),
        longitude NUMERIC(11, 8),
        descricao TEXT,
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );
      
      -- timeline_tweets table
      CREATE TABLE IF NOT EXISTS timeline_tweets (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        content TEXT NOT NULL,
        tweet_type VARCHAR(50) DEFAULT 'tweet',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );
      CREATE INDEX IF NOT EXISTS idx_timeline_user ON timeline_tweets(user_id);
    `);
  }

  getConfig(): DbConfig {
    return {
      postgres: {
        host: this.postgres!.getHost(),
        port: this.postgres!.getPort(),
        db: 'penhas_test',
        user: 'postgres',
        password: 'trustme',
      },
      redis: {
        host: this.redis!.getHost(),
        port: this.redis!.getPort(),
      },
    };
  }
}

export const testContainers = TestContainersManager.getInstance();
```

---

### Step 2.2: Global Setup/Teardown

**File**: `api-contract-tests/support/global-hooks.ts`
```typescript
import { AfterAll, BeforeAll } from '@cucumber/cucumber';
import { testContainers } from './testcontainers';

// Start containers before ALL tests
BeforeAll(async function () {
  const config = await testContainers.start();
  
  // Set environment variables for backends to connect
  process.env.POSTGRES_HOST = config.postgres.host;
  process.env.POSTGRES_PORT = config.postgres.port.toString();
  process.env.POSTGRES_DB = config.postgres.db;
  process.env.POSTGRES_USER = config.postgres.user;
  process.env.POSTGRES_PASSWORD = config.postgres.password;
  
  process.env.REDIS_HOST = config.redis.host;
  process.env.REDIS_PORT = config.redis.port.toString();
  
  console.log('🔧 Test environment configured');
});

// Stop containers after ALL tests
AfterAll(async function () {
  await testContainers.stop();
});
```

---

## 🧪 Phase 3: Cucumber World & Step Definitions

### Step 3.1: World Context (Shared State)

**File**: `api-contract-tests/step-definitions/world.ts`
```typescript
import { setWorldConstructor, World } from '@cucumber/cucumber';
import * as supertest from 'supertest';
import { faker } from '@faker-js/faker';

export class CustomWorld extends World {
  // HTTP client (Supertest)
  request!: supertest.SuperTest<supertest.Test>;
  
  // Test context
  testData: {
    userId?: number;
    sessionId?: string;
    email?: string;
    [key: string]: any;
  } = {};
  
  // Faker instance
  faker = faker;
  
  // Response storage
  response?: supertest.Response;
  
  constructor() {
    super();
  }
  
  // Initialize HTTP client based on target
  initClient() {
    const target = process.env.TARGET || 'perl';
    const baseUrl = target === 'perl' 
      ? process.env.PERL_URL || 'http://host.testcontainers.internal:8080'
      : process.env.PYTHON_URL || 'http://host.testcontainers.internal:8000';
    
    this.request = supertest(baseUrl);
  }
  
  // Generate unique test email
  generateTestEmail(prefix: string = 'test'): string {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).substring(2, 8)}@example.com`;
  }
  
  // Store response for assertions
  setResponse(response: supertest.Response) {
    this.response = response;
  }
  
  // Get last response
  getResponse(): supertest.Response {
    if (!this.response) {
      throw new Error('No response available. Make a request first.');
    }
    return this.response;
  }
}

// Register world constructor
setWorldConstructor(CustomWorld);
```

---

### Step 3.2: API Step Definitions (Supertest)

**File**: `api-contract-tests/step-definitions/api-steps.ts`
```typescript
import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from 'chai';
import { CustomWorld } from './world';
import { faker } from '@faker-js/faker';

// ============================================================================
// HTTP REQUEST STEPS
// ============================================================================

Given('I am testing the {string} backend', function (this: CustomWorld, target: string) {
  process.env.TARGET = target;
  this.initClient();
});

When('I send a {string} request to {string}', async function (this: CustomWorld, method: string, path: string) {
  const request = this.request[method.toLowerCase()](path);
  this.setResponse(await request);
});

When('I send a {string} request to {string} with body:', async function (this: CustomWorld, method: string, path: string, body: string) {
  // Replace placeholders like <random> or <timestamp>
  const processedBody = this.processBody(body);
  
  const request = this.request[method.toLowerCase()](path)
    .set('Content-Type', 'application/json')
    .send(processedBody);
  
  this.setResponse(await request);
});

When('I send a {string} request to {string} with query parameters:', async function (this: CustomWorld, method: string, path: string, dataTable: DataTable) {
  const queryParams: Record<string, any> = {};
  for (const [key, value] of dataTable.rows()) {
    queryParams[key] = this.processValue(value);
  }
  
  const request = this.request[method.toLowerCase()](path).query(queryParams);
  this.setResponse(await request);
});

When('I send a {string} request to {string} with headers:', async function (this: CustomWorld, method: string, path: string, dataTable: DataTable) {
  const headers: Record<string, string> = {};
  for (const [key, value] of dataTable.rows()) {
    headers[key] = value;
  }
  
  const request = this.request[method.toLowerCase()](path).set(headers);
  this.setResponse(await request);
});

When('I send a {string} request to {string} with body and headers:', async function (this: CustomWorld, method: string, path: string, body: string, dataTable: DataTable) {
  const processedBody = this.processBody(body);
  
  const headers: Record<string, string> = {};
  for (const [key, value] of dataTable.rows()) {
    headers[key] = value;
  }
  
  const request = this.request[method.toLowerCase()](path)
    .set(headers)
    .set('Content-Type', 'application/json')
    .send(processedBody);
  
  this.setResponse(await request);
});

// ============================================================================
// RESPONSE ASSERTION STEPS
// ============================================================================

Then('the response status should be {int}', function (this: CustomWorld, statusCode: number) {
  expect(this.getResponse().status).to.equal(statusCode);
});

Then('the response status should be {int} or {int}', function (this: CustomWorld, code1: number, code2: number) {
  const status = this.getResponse().status;
  expect([code1, code2]).to.include(status);
});

Then('the response should contain JSON:', function (this: CustomWorld, expectedJson: string) {
  const responseJson = this.getResponse().body;
  const expected = JSON.parse(expectedJson);
  
  this.validatePartialMatch(responseJson, expected);
});

Then('the response should match schema:', function (this: CustomWorld, schemaJson: string) {
  const responseJson = this.getResponse().body;
  const schema = JSON.parse(schemaJson);
  
  this.validateSchema(responseJson, schema);
});

Then('the response {string} should be {string}', function (this: CustomWorld, fieldPath: string, expectedValue: string) {
  const value = this.getNestedValue(this.getResponse().body, fieldPath);
  expect(value).to.equal(expectedValue);
});

Then('the response {string} should be a number', function (this: CustomWorld, fieldPath: string) {
  const value = this.getNestedValue(this.getResponse().body, fieldPath);
  expect(value).to.be.a('number');
});

Then('the response {string} should match regex {string}', function (this: CustomWorld, fieldPath: string, regexPattern: string) {
  const value = this.getNestedValue(this.getResponse().body, fieldPath);
  const regex = new RegExp(regexPattern);
  expect(value).to.match(regex);
});

Then('the response should have field {string}', function (this: CustomWorld, fieldPath: string) {
  const value = this.getNestedValue(this.getResponse().body, fieldPath);
  expect(value).to.not.be.undefined;
});

Then('the response should not have field {string}', function (this: CustomWorld, fieldPath: string) {
  const value = this.getNestedValue(this.getResponse().body, fieldPath);
  expect(value).to.be.undefined;
});

// ============================================================================
// RESPONSE DATA STORAGE STEPS
// ============================================================================

Then('I store the response {string} as {string}', function (this: CustomWorld, fieldPath: string, variableName: string) {
  const value = this.getNestedValue(this.getResponse().body, fieldPath);
  this.testData[variableName] = value;
  console.log(`💾 Stored ${variableName} = ${value}`);
});

Then('I store the response body as {string}', function (this: CustomWorld, variableName: string) {
  this.testData[variableName] = this.getResponse().body;
  console.log(`💾 Stored entire response as ${variableName}`);
});

// ============================================================================
// HELPER METHODS (attached to World prototype)
// ============================================================================

CustomWorld.prototype.processBody = function(body: string): any {
  try {
    let processed = body;
    
    // Replace <random> with random string
    processed = processed.replace(/<random>/g, Math.random().toString(36).substring(2, 10));
    
    // Replace <timestamp> with current timestamp
    processed = processed.replace(/<timestamp>/g, Date.now().toString());
    
    // Replace <uuid> with UUID
    processed = processed.replace(/<uuid>/g, this.faker.string.uuid());
    
    // Replace <email> with unique email
    processed = processed.replace(/<email>/g, this.generateTestEmail('auto'));
    
    return JSON.parse(processed);
  } catch (error) {
    console.error('Error processing body:', error);
    return JSON.parse(body);
  }
};

CustomWorld.prototype.processValue = function(value: string): any {
  if (value === '<random>') return Math.random().toString(36).substring(2, 10);
  if (value === '<timestamp>') return Date.now();
  if (value === '<uuid>') return this.faker.string.uuid();
  if (value === '<email>') return this.generateTestEmail('auto');
  return value;
};

CustomWorld.prototype.validatePartialMatch = function(actual: any, expected: any) {
  for (const [key, expectedValue] of Object.entries(expected)) {
    const actualValue = actual[key];
    
    // Handle special matchers
    if (typeof expectedValue === 'string') {
      if (expectedValue.startsWith('#regex ')) {
        const pattern = expectedValue.substring(7);
        const regex = new RegExp(pattern);
        expect(actualValue).to.match(regex, `Field ${key} should match ${pattern}`);
        continue;
      }
      if (expectedValue === '#number') {
        expect(actualValue).to.be.a('number', `Field ${key} should be a number`);
        continue;
      }
      if (expectedValue === '#string') {
        expect(actualValue).to.be.a('string', `Field ${key} should be a string`);
        continue;
      }
      if (expectedValue === '#boolean') {
        expect(actualValue).to.be.a('boolean', `Field ${key} should be a boolean`);
        continue;
      }
      if (expectedValue === '#array') {
        expect(actualValue).to.be.an('array', `Field ${key} should be an array`);
        continue;
      }
      if (expectedValue === '#object') {
        expect(actualValue).to.be.an('object', `Field ${key} should be an object`);
        continue;
      }
      if (expectedValue === '#null') {
        expect(actualValue).to.be.null;
        continue;
      }
      if (expectedValue === '#notnull') {
        expect(actualValue).to.not.be.null;
        continue;
      }
    }
    
    // Regular equality check
    expect(actualValue).to.deep.equal(expectedValue, `Field ${key} mismatch`);
  }
};

CustomWorld.prototype.validateSchema = function(actual: any, schema: any) {
  this.validatePartialMatch(actual, schema);
};

CustomWorld.prototype.getNestedValue = function(obj: any, path: string): any {
  return path.split('.').reduce((current, key) => {
    return current?.[key];
  }, obj);
};
```

---

### Step 3.3: Database Step Definitions

**File**: `api-contract-tests/step-definitions/db-steps.ts`
```typescript
import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from 'chai';
import { CustomWorld } from './world';
import { Client } from 'pg';
import { testContainers } from '../support/testcontainers';

// ============================================================================
// DATABASE SETUP STEPS
// ============================================================================

Given('I have a clean database', async function (this: CustomWorld) {
  const config = testContainers.getConfig();
  const client = new Client({
    host: config.postgres.host,
    port: config.postgres.port,
    database: config.postgres.db,
    user: config.postgres.user,
    password: config.postgres.password,
  });
  
  try {
    await client.connect();
    
    // Truncate all tables and reset sequences
    await client.query(`
      TRUNCATE TABLE 
        clientes,
        ponto_apoio,
        ponto_apoio_categoria,
        timeline_tweets
      RESTART IDENTITY CASCADE;
    `);
    
    console.log('🧹 Database cleaned');
  } finally {
    await client.end();
  }
});

Given('the database has a user with email {string}', async function (this: CustomWorld, email: string) {
  const config = testContainers.getConfig();
  const client = new Client({
    host: config.postgres.host,
    port: config.postgres.port,
    database: config.postgres.db,
    user: config.postgres.user,
    password: config.postgres.password,
  });
  
  try {
    await client.connect();
    
    // Generate random CPF hash (matching Perl format)
    const cpfHash = require('crypto').createHash('sha256').update(Date.now().toString()).digest('hex');
    
    await client.query(`
      INSERT INTO clientes (cpf_hash, email, nome_completo, genero, status, login_status)
      VALUES ($1, $2, $3, $4, 'active', 'OK')
    `, [cpfHash, email, 'Test User', 'Feminino']);
    
    console.log(`👤 Created user: ${email}`);
  } finally {
    await client.end();
  }
});

// ============================================================================
// DATABASE ASSERTION STEPS
// ============================================================================

Then('the database should have {int} users', async function (this: CustomWorld, expectedCount: number) {
  const config = testContainers.getConfig();
  const client = new Client({
    host: config.postgres.host,
    port: config.postgres.port,
    database: config.postgres.db,
    user: config.postgres.user,
    password: config.postgres.password,
  });
  
  try {
    await client.connect();
    const result = await client.query('SELECT COUNT(*) as count FROM clientes');
    const actualCount = parseInt(result.rows[0].count);
    
    expect(actualCount).to.equal(expectedCount);
    console.log(`📊 Database has ${actualCount} users`);
  } finally {
    await client.end();
  }
});

Then('the user with email {string} should exist in the database', async function (this: CustomWorld, email: string) {
  const config = testContainers.getConfig();
  const client = new Client({
    host: config.postgres.host,
    port: config.postgres.port,
    database: config.postgres.db,
    user: config.postgres.user,
    password: config.postgres.password,
  });
  
  try {
    await client.connect();
    const result = await client.query('SELECT * FROM clientes WHERE email = $1', [email]);
    
    expect(result.rows).to.have.lengthOf(1);
    console.log(`✅ User ${email} exists in database`);
  } finally {
    await client.end();
  }
});

Then('the user with email {string} should not exist in the database', async function (this: CustomWorld, email: string) {
  const config = testContainers.getConfig();
  const client = new Client({
    host: config.postgres.host,
    port: config.postgres.port,
    database: config.postgres.db,
    user: config.postgres.user,
    password: config.postgres.password,
  });
  
  try {
    await client.connect();
    const result = await client.query('SELECT * FROM clientes WHERE email = $1', [email]);
    
    expect(result.rows).to.have.lengthOf(0);
    console.log(`✅ User ${email} does not exist in database`);
  } finally {
    await client.end();
  }
});
```

---

### Step 3.4: Hooks (Before/After Each Scenario)

**File**: `api-contract-tests/step-definitions/hooks.ts`
```typescript
import { Before, After, Status } from '@cucumber/cucumber';
import { CustomWorld } from './world';

// Clean database before each scenario
Before({ tags: '@clean' }, async function (this: CustomWorld) {
  console.log('🧹 Cleaning database before scenario');
  // Database cleanup handled by step: "Given I have a clean database"
});

// Log failed scenarios
After(async function (this: CustomWorld, scenario) {
  if (scenario.result?.status === Status.FAILED) {
    console.log(`❌ Scenario failed: ${scenario.pickle.name}`);
    if (this.response) {
      console.log('Response:', JSON.stringify(this.response.body, null, 2));
    }
  }
});

// Auto-cleanup for scenarios that create users
After({ tags: '@creates-user' }, async function (this: CustomWorld) {
  if (this.testData.userId) {
    console.log(`🗑️  Cleanup: User ID ${this.testData.userId}`);
    // Cleanup would happen via database truncate in next scenario
  }
});
```

---

## 📝 Phase 4: Gherkin Feature Files (Golden Master Tests)

### Feature 1: Authentication API

**File**: `api-contract-tests/features/auth.feature`
```gherkin
@perl @auth @clean
Feature: Authentication API - Golden Master (Perl Mojolicious)
  All tests capture exact behavior of Perl backend.
  DO NOT MODIFY after baseline established.

  Background:
    Given I am testing the "perl" backend
    And I have a clean database

  @creates-user
  Scenario: POST /sign-up creates new user successfully
    When I send a POST request to "/sign-up" with body:
      """
      {
        "email": "newuser_<random>@example.com",
        "password": "SecurePass123!",
        "nome_completo": "New User",
        "genero": "Feminino"
      }
      """
    Then the response status should be 200
    And the response should contain JSON:
      """
      {
        "ok": "1",
        "session": "#regex [a-f0-9]{64}",
        "_test_only_id": "#number"
      }
      """
    And I store the response "_test_only_id" as "userId"
    And the database should have 1 users

  @creates-user
  Scenario: POST /sign-up with duplicate email returns 400
    # Create first user
    When I send a POST request to "/sign-up" with body:
      """
      {
        "email": "dupe_<random>@example.com",
        "password": "Pass123!",
        "nome_completo": "First User",
        "genero": "Feminino"
      }
      """
    Then the response status should be 200
    And I store the response "_test_only_id" as "firstUserId"

    # Try to create duplicate
    When I send a POST request to "/sign-up" with body:
      """
      {
        "email": "dupe_<random>@example.com",
        "password": "Pass123!",
        "nome_completo": "Second User",
        "genero": "Feminino"
      }
      """
    Then the response status should be 400
    And the response should contain JSON:
      """
      {
        "ok": "0",
        "message": "Email já cadastrado"
      }
      """
    And the database should have 1 users

  @creates-user
  Scenario: POST /login with valid credentials
    # Create user first
    Given the database has a user with email "test_login@example.com"
    
    When I send a POST request to "/login" with body:
      """
      {
        "email": "test_login@example.com",
        "senha": "password123"
      }
      """
    Then the response status should be 200
    And the response should contain JSON:
      """
      {
        "ok": "1",
        "session": "#regex [a-f0-9]{64}",
        "user": {
          "id": "#number",
          "email": "test_login@example.com",
          "apelido": "#string",
          "nome_completo": "#string",
          "genero": "#string",
          "status": "active"
        }
      }
      """
    And I store the response "session" as "sessionId"

  Scenario: POST /login with invalid credentials returns 401
    When I send a POST request to "/login" with body:
      """
      {
        "email": "nonexistent@example.com",
        "senha": "wrongpassword"
      }
      """
    Then the response status should be 401
    And the response should contain JSON:
      """
      {
        "ok": "0",
        "message": "Email ou senha inválidos"
      }
      """

  @creates-user
  Scenario: POST /logout invalidates session
    # Create and login user
    When I send a POST request to "/sign-up" with body:
      """
      {
        "email": "logout_test_<random>@example.com",
        "password": "LogoutPass123!",
        "nome_completo": "Logout Test",
        "genero": "Feminino"
      }
      """
    Then the response status should be 200
    And I store the response "session" as "sessionId"

    # Logout
    When I send a POST request to "/logout" with headers:
      | x-api-key | <sessionId> |
    Then the response status should be 204

    # Verify session is invalid
    When I send a GET request to "/me" with headers:
      | x-api-key | <sessionId> |
    Then the response status should be 403
```

---

### Feature 2: Timeline API

**File**: `api-contract-tests/features/timeline.feature`
```gherkin
@perl @timeline @clean
Feature: Timeline API - Golden Master (Perl Mojolicious)

  Background:
    Given I am testing the "perl" backend
    And I have a clean database

  @creates-user
  Scenario: GET /timeline returns user's timeline
    # Create authenticated user
    When I send a POST request to "/sign-up" with body:
      """
      {
        "email": "timeline_user_<random>@example.com",
        "password": "TimelinePass123!",
        "nome_completo": "Timeline User",
        "genero": "Feminino"
      }
      """
    Then the response status should be 200
    And I store the response "session" as "sessionId"

    # Get timeline
    When I send a GET request to "/timeline" with headers:
      | x-api-key | <sessionId> |
    Then the response status should be 200
    And the response should contain JSON:
      """
      {
        "tweets": "#array",
        "has_more": "#boolean"
      }
      """

  @creates-user
  Scenario: POST /timeline creates new tweet
    # Create authenticated user
    When I send a POST request to "/sign-up" with body:
      """
      {
        "email": "tweet_user_<random>@example.com",
        "password": "TweetPass123!",
        "nome_completo": "Tweet User",
        "genero": "Feminino"
      }
      """
    Then the response status should be 200
    And I store the response "session" as "sessionId"

    # Create tweet
    When I send a POST request to "/timeline" with body and headers:
      """
      {
        "content": "Test tweet from Cucumber <random>"
      }
      """
      | x-api-key | <sessionId> |
    Then the response status should be 200
    And the response should contain JSON:
      """
      {
        "id": "#number",
        "type": "tweet",
        "content": "#string",
        "created_at": "#notnull",
        "user": {
          "id": "#number",
          "apelido": "#string"
        }
      }
      """
    And I store the response "id" as "tweetId"

    # Verify tweet appears in timeline
    When I send a GET request to "/timeline" with headers:
      | x-api-key | <sessionId> |
    Then the response status should be 200
    And the response "tweets.0.id" should be "<tweetId>"
```

---

### Feature 3: Ponto de Apoio API

**File**: `api-contract-tests/features/ponto-apoio.feature`
```gherkin
@perl @ponto-apoio @clean
Feature: Ponto de Apoio API - Golden Master (Perl Mojolicious)

  Background:
    Given I am testing the "perl" backend
    And I have a clean database

  Scenario: GET /ponto-apoio-unlimited returns nearby locations
    When I send a GET request to "/ponto-apoio-unlimited" with query parameters:
      | token         | validtoken |
      | latitude      | -23.51934  |
      | longitude     | -46.53918  |
      | rows          | 10         |
      | max_distance  | 50         |
    Then the response status should be 200
    And the response should contain JSON:
      """
      {
        "rows": "#array",
        "total": "#number"
      }
      """
    And the response "rows" should be an array

  @creates-user
  Scenario: POST /me/sugerir-pontos-de-apoio creates suggestion
    # Create authenticated user
    When I send a POST request to "/sign-up" with body:
      """
      {
        "email": "suggestion_user_<random>@example.com",
        "password": "SuggestPass123!",
        "nome_completo": "Suggestion User",
        "genero": "Feminino"
      }
      """
    Then the response status should be 200
    And I store the response "session" as "sessionId"

    # Create suggestion
    When I send a POST request to "/me/sugerir-pontos-de-apoio" with body and headers:
      """
      {
        "endereco_ou_cep": "Rua Augusta, 123",
        "nome": "Test Location <random>",
        "categoria": 1,
        "descricao_servico": "Test description"
      }
      """
      | x-api-key | <sessionId> |
    Then the response status should be 200
    And the response should contain JSON:
      """
      {
        "ok": "1",
        "message": "#string"
      }
      """
```

---

## 🔄 Phase 5: TDD Workflow (Perl → Python)

### Step 5.1: Run Tests Against Perl Backend

**Start Perl backend with Testcontainers DB**:

**File**: `api-contract-tests/docker-compose.perl.yml`
```yaml
version: '3.8'

services:
  perl-backend:
    build: ../api
    ports:
      - "8080:3000"
    environment:
      POSTGRES_HOST: host.testcontainers.internal
      POSTGRES_PORT: ${POSTGRES_PORT:-5432}
      POSTGRES_DB: penhas_test
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: trustme
      REDIS_HOST: host.testcontainers.internal
      REDIS_PORT: ${REDIS_PORT:-6379}
      # Add other Perl env vars as needed
    extra_hosts:
      - "host.testcontainers.internal:host-gateway"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 5s
      timeout: 3s
      retries: 5
```

**Start and run tests**:
```bash
#!/bin/bash
# scripts/start-perl-and-test.sh

# Start Testcontainers and get ports
export POSTGRES_PORT=$(node -e "const {testContainers} = require('./support/testcontainers'); testContainers.start().then(c => console.log(c.postgres.port))")
export REDIS_PORT=$(node -e "const {testContainers} = require('./support/testcontainers'); testContainers.start().then(c => console.log(c.redis.port))")

# Start Perl backend
docker-compose -f docker-compose.perl.yml up -d

# Wait for backend to be ready
sleep 5

# Run contract tests
TARGET=perl PERL_URL=http://localhost:8080 npm run test:perl

# Cleanup
docker-compose -f docker-compose.perl.yml down
```

---

### Step 5.2: Establish Baseline (100% Pass Rate)

```bash
# Run all tests 100 times to verify stability
for i in {1..100}; do
  echo "Run $i..."
  npm run test:perl || exit 1
done

echo "✅ All 100 runs passed - tests are stable!"
```

---

### Step 5.3: Freeze Tests (Golden Master)

```bash
# Tag the commit
git tag -a perl-golden-master-v1.0 -m "Golden master tests for Perl backend - READ ONLY"

# Mark feature files as read-only
chmod -R a-w features/

# Document freeze
cat > features/README.md <<EOF
⚠️  TEST FREEZE NOTICE

These Gherkin feature files capture the EXACT behavior of the Perl/Mojolicious backend.

DO NOT MODIFY after Perl baseline established.

Purpose: Contract between legacy and new Python implementation.

If API behavior must change:
1. Update Perl backend first
2. Update tests to match new behavior  
3. Re-freeze test suite
4. Update Python to match
EOF
```

---

### Step 5.4: TDD Python Implementation

**Workflow for each endpoint**:

```bash
# 1. Run tests against Python (expect failures)
TARGET=python PYTHON_URL=http://localhost:8000 npm run test:auth

# ❌ Tests fail - expected

# 2. Implement minimal endpoint in Python FastAPI
# (see api-v2/app/main.py)

# 3. Run tests again
TARGET=python PYTHON_URL=http://localhost:8000 npm run test:auth

# ✅ Tests pass - endpoint complete!
```

**Example Python implementation**:

```python
# api-v2/app/main.py
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

app = FastAPI()

class SignUpRequest(BaseModel):
    email: str
    password: str
    nome_completo: str
    genero: str

@app.post("/sign-up")
async def sign_up(user: SignUpRequest, db: Session = Depends(get_db)):
    # Check duplicate email
    existing = db.query(Cliente).filter(Cliente.email == user.email).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail={"ok": "0", "message": "Email já cadastrado"}
        )
    
    # Create user
    db_user = Cliente(
        email=user.email,
        nome_completo=user.nome_completo,
        genero=user.genero,
        cpf_hash=generate_cpf_hash(),
        status="active",
        login_status="OK"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Generate session token
    session_token = generate_session_token()
    
    return {
        "ok": "1",
        "session": session_token,
        "_test_only_id": db_user.id
    }
```

---

## 📊 Phase 6: Progress Tracking

**File**: `MIGRATION_PROGRESS.md`
```markdown
# Migration Progress Tracker

## Endpoint Coverage

| Endpoint                           | Perl Tests    | Python Status | Notes              |
| ---------------------------------- | ------------- | ------------- | ------------------ |
| `POST /sign-up`                    | ✅ 3 scenarios | ✅ PASS        | Complete           |
| `POST /login`                      | ✅ 2 scenarios | ✅ PASS        | Complete           |
| `POST /logout`                     | ✅ 1 scenario  | ✅ PASS        | Complete           |
| `GET /me`                          | ✅ 2 scenarios | 🟡 IN PROGRESS | Session validation |
| `GET /timeline`                    | ✅ 4 scenarios | 🔴 FAIL        | Pagination         |
| `POST /timeline`                   | ✅ 2 scenarios | 🔴 FAIL        | Not started        |
| `GET /ponto-apoio-unlimited`       | ✅ 2 scenarios | 🔴 FAIL        | Distance calc      |
| `POST /me/sugerir-pontos-de-apoio` | ✅ 1 scenario  | 🔴 FAIL        | Not started        |

## Overall Stats

- **Total Features**: 15
- **Completed**: 5 (33%)
- **In Progress**: 3 (20%)
- **Not Started**: 7 (47%)
- **Test Pass Rate**: 28/85 (33%)

## Next Priorities

1. Complete `/me` endpoint
2. Implement timeline pagination
3. Add Ponto de Apoio distance calculation
```

---

## 🚀 Quick Start Commands

```bash
# Clone repository
git clone <repository-url>
cd institutoazmina-penhas-backend/api-contract-tests

# Install dependencies
npm install

# Build TypeScript
npm run build

# Run tests against Perl
TARGET=perl PERL_URL=http://localhost:8080 npm run test:perl

# Run specific feature
npm run test:auth

# Watch mode (auto-reload on changes)
npm run test:watch

# Verify stability (100 runs)
npm run test:stable

# Generate HTML report
npm run report
```

---