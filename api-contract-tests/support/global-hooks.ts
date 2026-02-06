import { AfterAll, BeforeAll } from '@cucumber/cucumber';
import { testContainers } from './testcontainers';
import { perlApi } from './perl-api-manager';

// Start containers and Perl API before ALL tests
// Note: This hook has a longer timeout (120s) configured in cucumber.js
BeforeAll({ timeout: 360000 }, async function () {
  try {
    console.log('⏳ Starting Testcontainers (this may take a while on first run)...');
    const config = await testContainers.start();
    
    // Set environment variables for backends to connect
    process.env.POSTGRES_HOST = config.postgres.host;
    process.env.POSTGRES_PORT = config.postgres.port.toString();
    process.env.POSTGRES_DB = config.postgres.db;
    process.env.POSTGRES_USER = config.postgres.user;
    process.env.POSTGRES_PASSWORD = config.postgres.password;
    
    process.env.REDIS_HOST = config.redis.host;
    process.env.REDIS_PORT = config.redis.port.toString();
    
    // Set test environment flag
    process.env.IS_TEST = '1';
    
    console.log('🔧 Test environment configured');
    console.log(`   PostgreSQL: ${config.postgres.host}:${config.postgres.port}`);
    console.log(`   Redis: ${config.redis.host}:${config.redis.port}`);
    
    // Start Perl API
    try {
      const apiConfig = await perlApi.start();
      // Set the dynamic URL so world.ts picks it up
      process.env.PERL_URL = `http://${apiConfig.host}:${apiConfig.port}`;
      console.log(`   Perl API: ${process.env.PERL_URL}`);
    } catch (error: any) {
      console.error('⚠️  Failed to start Perl API:', error.message);
      console.error('   Tests will fail with connection errors.');
      console.error('   To fix:');
      console.error('   1. Install Mojolicious: cpanm Mojolicious');
      console.error('   2. Ensure perl and morbo are in PATH');
      console.error('   3. Or start the API manually before running tests');
      // Don't throw - let tests run and fail with connection errors
      // This allows the test infrastructure to be verified even if API isn't available
    }
  } catch (error: any) {
    console.error('❌ Failed to start Testcontainers:', error.message);
    console.error('   Troubleshooting:');
    console.error('   1. Ensure Docker is running: docker ps');
    console.error('   2. Check Docker has enough resources allocated');
    console.error('   3. Try: docker pull postgis/postgis:13-3.1');
    console.error('   4. Try: docker pull redis:7-alpine');
    throw error;
  }
});

// Stop containers and Perl API after ALL tests
AfterAll(async function () {
  await perlApi.stop();
  await testContainers.stop();
});

