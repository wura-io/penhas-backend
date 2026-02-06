import { setWorldConstructor, World, IWorldOptions } from '@cucumber/cucumber';
import supertest from 'supertest';
import { faker } from '@faker-js/faker';

export class CustomWorld extends World {
  // HTTP client (Supertest)
  request!: supertest.SuperTest<supertest.Test> | any;
  
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
  
  constructor(options: IWorldOptions) {
    super(options);
  }
  
  // Initialize HTTP client based on target
  initClient() {
    const target = process.env.TARGET || 'perl';
    // Tests run on host, so connect to API on localhost
    const baseUrl = target === 'perl' 
      ? process.env.PERL_URL || 'http://localhost:8080'
      : process.env.PYTHON_URL || 'http://localhost:8000';
    
    // Supertest can work with URLs, but we need to ensure it's properly configured
    // For remote URLs, supertest creates a new agent for each request
    this.request = (supertest as any)(baseUrl);
    console.log(`🌐 Initialized HTTP client for ${target} backend: ${baseUrl}`);
    
    // Test connectivity
    this.testConnectivity(baseUrl);
  }
  
  // Test if we can reach the API
  async testConnectivity(baseUrl: string) {
    try {
      const testRequest = (this.request.get as any)('/');
      const response = await testRequest.timeout(5000);
      console.log(`✅ API connectivity test: ${response.status}`);
    } catch (error: any) {
      console.warn(`⚠️  API connectivity test failed: ${error.message}`);
      console.warn(`   This might indicate the API is not ready or not accessible`);
    }
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
  
  // Process body with placeholders
  processBody(body: string): any {
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
      
      // Replace stored variables like <sessionId>, <userId>
      for (const [key, value] of Object.entries(this.testData)) {
        const placeholder = `<${key}>`;
        if (processed.includes(placeholder)) {
          processed = processed.replace(new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), String(value));
        }
      }
      
      return JSON.parse(processed);
    } catch (error: any) {
      console.error('Error processing body:', error);
      return JSON.parse(body);
    }
  }
  
  // Process single value
  processValue(value: string): any {
    if (value === '<random>') return Math.random().toString(36).substring(2, 10);
    if (value === '<timestamp>') return Date.now();
    if (value === '<uuid>') return this.faker.string.uuid();
    if (value === '<email>') return this.generateTestEmail('auto');
    
    // Replace stored variables
    for (const [key, val] of Object.entries(this.testData)) {
      if (value === `<${key}>`) {
        return val;
      }
    }
    
    return value;
  }
  
  // Validate partial JSON match
  validatePartialMatch(actual: any, expected: any, path: string = '') {
    for (const [key, expectedValue] of Object.entries(expected)) {
      const currentPath = path ? `${path}.${key}` : key;
      const actualValue = actual[key];
      
      // Handle special matchers
      if (typeof expectedValue === 'string') {
        if (expectedValue.startsWith('#regex ')) {
          const pattern = expectedValue.substring(7);
          const regex = new RegExp(pattern);
          if (!regex.test(String(actualValue))) {
            throw new Error(`Field ${currentPath} should match regex ${pattern}, got: ${actualValue}`);
          }
          continue;
        }
        if (expectedValue === '#number') {
          if (typeof actualValue !== 'number') {
            throw new Error(`Field ${currentPath} should be a number, got: ${typeof actualValue}`);
          }
          continue;
        }
        if (expectedValue === '#string') {
          if (typeof actualValue !== 'string') {
            throw new Error(`Field ${currentPath} should be a string, got: ${typeof actualValue}`);
          }
          continue;
        }
        if (expectedValue === '#boolean') {
          if (typeof actualValue !== 'boolean') {
            throw new Error(`Field ${currentPath} should be a boolean, got: ${typeof actualValue}`);
          }
          continue;
        }
        if (expectedValue === '#array') {
          if (!Array.isArray(actualValue)) {
            throw new Error(`Field ${currentPath} should be an array, got: ${typeof actualValue}`);
          }
          continue;
        }
        if (expectedValue === '#object') {
          if (typeof actualValue !== 'object' || actualValue === null || Array.isArray(actualValue)) {
            throw new Error(`Field ${currentPath} should be an object, got: ${typeof actualValue}`);
          }
          continue;
        }
        if (expectedValue === '#null') {
          if (actualValue !== null) {
            throw new Error(`Field ${currentPath} should be null, got: ${actualValue}`);
          }
          continue;
        }
        if (expectedValue === '#notnull') {
          if (actualValue === null || actualValue === undefined) {
            throw new Error(`Field ${currentPath} should not be null`);
          }
          continue;
        }
      }
      
      // Recursive check for nested objects
      if (typeof expectedValue === 'object' && expectedValue !== null && !Array.isArray(expectedValue)) {
        if (typeof actualValue === 'object' && actualValue !== null && !Array.isArray(actualValue)) {
          this.validatePartialMatch(actualValue, expectedValue, currentPath);
          continue;
        } else {
          throw new Error(`Field ${currentPath} should be an object`);
        }
      }
      
      // Regular equality check
      if (JSON.stringify(actualValue) !== JSON.stringify(expectedValue)) {
        throw new Error(`Field ${currentPath} mismatch: expected ${JSON.stringify(expectedValue)}, got ${JSON.stringify(actualValue)}`);
      }
    }
  }
  
  // Get nested value from object using dot notation
  getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => {
      if (current === null || current === undefined) {
        return undefined;
      }
      return current[key];
    }, obj);
  }
}

// Register world constructor
setWorldConstructor(CustomWorld);

