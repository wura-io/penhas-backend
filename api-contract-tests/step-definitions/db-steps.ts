import { Given, Then } from '@cucumber/cucumber';
import { expect } from 'chai';
import { CustomWorld } from './world';
import { Client } from 'pg';
import { testContainers } from '../support/testcontainers';
import * as crypto from 'crypto';

// ============================================================================
// DATABASE SETUP STEPS
// ============================================================================

// Helper function to calculate CPF hash (matching Perl cpf_hash_with_salt)
// Perl does: sha256_hex($cpf_salt . encode_utf8($str))
// Note: Perl strips formatting from CPF before hashing (line 73: $params->{cpf} =~ s/[^\d]//ga;)
// But the hash is calculated on the original CPF string with formatting
// Actually, looking at the code, it strips AFTER getting the CPF, so hash uses formatted version
function cpfHashWithSalt(cpf: string, salt: string): string {
  // Perl's encode_utf8 ensures UTF-8 encoding, which is default in Node.js
  // The CPF is hashed as-is (with formatting) before it's stripped
  // But actually, let's check - the hash is used for lookup, and CPF is stripped before lookup
  // So we should hash the digits-only version to match what Perl does
  const cpfDigits = cpf.replace(/\D/g, '');
  // Perl: sha256_hex($salt . encode_utf8($cpf))
  return crypto.createHash('sha256').update(salt + cpfDigits, 'utf8').digest('hex');
}

// Helper function to calculate name hash (matching Perl cpf_hash_with_salt)
function nameHashWithSalt(name: string, salt: string): string {
  // Perl uppercases and removes accents, then hashes
  // For simplicity, we'll just uppercase and hash (salt first, then name)
  const upperName = name.toUpperCase();
  return crypto.createHash('sha256').update(salt + upperName).digest('hex');
}

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
    
    // Get all table names
    const result = await client.query(`
      SELECT tablename 
      FROM pg_tables 
      WHERE schemaname = 'public'
      AND tablename NOT LIKE 'pg_%'
      AND tablename NOT LIKE 'sql_%'
    `);
    
    const tables = result.rows.map(row => row.tablename);
    
    if (tables.length > 0) {
      // Truncate all tables and reset sequences
      await client.query(`
        TRUNCATE TABLE ${tables.map(t => `"${t}"`).join(', ')} 
        RESTART IDENTITY CASCADE;
      `);
    }
    
    // Pre-populate CPF cache for test CPF (544.340.690-63)
    // This prevents the API from trying to call external CPF validation service
    // Note: The salt must match what's set in the Perl API container
    // The perl-api-manager uses: 'test-salt-fixed-for-contract-tests' as default
    const cpfSalt = process.env.CPF_CACHE_HASH_SALT || 'test-salt-fixed-for-contract-tests';
    const testCpf = '54434069063'; // Remove formatting for hashing
    const testCpfHash = cpfHashWithSalt(testCpf, cpfSalt);
    // For name, Perl uses unaccented uppercase - "MARIA SILVA" should work
    const testNameHash = nameHashWithSalt('MARIA SILVA', cpfSalt);
    
    try {
      await client.query(`
        INSERT INTO cpf_cache (cpf_hashed, dt_nasc, nome_hashed, situacao, genero)
        VALUES ($1, $2, $3, '', 'F')
        ON CONFLICT (cpf_hashed, dt_nasc) DO UPDATE
        SET nome_hashed = EXCLUDED.nome_hashed
      `, [testCpfHash, '1990-01-15', testNameHash]);
      console.log(`✅ Pre-populated CPF cache for test CPF (hash: ${testCpfHash.substring(0, 16)}...)`);
    } catch (error: any) {
      // Table might not exist yet, ignore
      console.log('⚠️  Could not pre-populate CPF cache:', error.message);
    }
    
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
    
    // Generate random CPF hash (matching Perl format - SHA256)
    const cpfHash = crypto.createHash('sha256').update(Date.now().toString()).digest('hex');
    
    // Generate password hash (SHA256)
    const passwordHash = crypto.createHash('sha256').update('password123').digest('hex');
    
    await client.query(`
      INSERT INTO clientes (
        cpf_hash, email, nome_completo, apelido, genero, 
        status, login_status, senha_sha256, dt_nasc, cep, created_on
      )
      VALUES ($1, $2, $3, $4, $5, 'active', 'OK', $6, '1990-01-01', '01310100', NOW())
      ON CONFLICT DO NOTHING
    `, [cpfHash, email.toLowerCase(), 'Test User', 'TestUser', 'Feminino', passwordHash]);
    
    console.log(`👤 Created user: ${email}`);
  } finally {
    await client.end();
  }
});

Given('the database has a user with email {string} and password {string}', async function (this: CustomWorld, email: string, password: string) {
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
    
    // Generate random CPF hash
    const cpfHash = crypto.createHash('sha256').update(Date.now().toString()).digest('hex');
    
    // Generate password hash (SHA256)
    const passwordHash = crypto.createHash('sha256').update(password).digest('hex');
    
    await client.query(`
      INSERT INTO clientes (
        cpf_hash, email, nome_completo, apelido, genero, 
        status, login_status, senha_sha256, dt_nasc, cep, created_on
      )
      VALUES ($1, $2, $3, $4, $5, 'active', 'OK', $6, '1990-01-01', '01310100', NOW())
      ON CONFLICT DO NOTHING
    `, [cpfHash, email.toLowerCase(), 'Test User', 'TestUser', 'Feminino', passwordHash]);
    
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
    const result = await client.query('SELECT * FROM clientes WHERE email = $1', [email.toLowerCase()]);
    
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
    const result = await client.query('SELECT * FROM clientes WHERE email = $1', [email.toLowerCase()]);
    
    expect(result.rows).to.have.lengthOf(0);
    console.log(`✅ User ${email} does not exist in database`);
  } finally {
    await client.end();
  }
});

