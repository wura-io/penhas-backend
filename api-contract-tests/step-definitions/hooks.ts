import { Before, After, Status } from '@cucumber/cucumber';
import { CustomWorld } from './world';

// Clean database before each scenario tagged with @clean
Before({ tags: '@clean' }, async function (this: CustomWorld) {
  console.log('🧹 Cleaning database before scenario');
  // Database cleanup handled by step: "Given I have a clean database"
});

// Initialize HTTP client before scenarios that need it
Before({ tags: '@perl or @python' }, async function (this: CustomWorld) {
  if (!this.request) {
    this.initClient();
  }
});

// Log failed scenarios
After(async function (this: CustomWorld, scenario) {
  if (scenario.result?.status === Status.FAILED) {
    console.log(`❌ Scenario failed: ${scenario.pickle.name}`);
    if (this.response) {
      console.log('Response status:', this.response.status);
      console.log('Response body:', JSON.stringify(this.response.body, null, 2));
    } else {
      // If no response, the request likely failed - check container status
      const { perlApi } = await import('../support/perl-api-manager');
      if (perlApi.isStarted()) {
        const config = perlApi.getConfig();
        if (config?.containerId) {
          try {
            const { exec } = await import('child_process');
            const { promisify } = await import('util');
            const execAsync = promisify(exec);
            const { stdout: logs } = await execAsync(`docker logs ${config.containerId} 2>&1 | tail -30`);
            console.log('📋 Container logs (last 30 lines):');
            console.log(logs);
          } catch (error: any) {
            console.log('⚠️  Could not fetch container logs:', error.message);
          }
        }
      }
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

