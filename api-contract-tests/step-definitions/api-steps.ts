import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from 'chai';
import { CustomWorld } from './world';
import { DataTable } from '@cucumber/cucumber';

// ============================================================================
// HTTP REQUEST STEPS
// ============================================================================

Given('I am testing the {string} backend', function (this: CustomWorld, target: string) {
  process.env.TARGET = target;
  this.initClient();
});

When('I send a {string} request to {string}', async function (this: CustomWorld, method: string, path: string) {
  const methodLower = method.toLowerCase() as 'get' | 'post' | 'put' | 'delete' | 'patch';
  const request = (this.request[methodLower] as any)(path)
    .timeout(30000); // 30 second timeout
  try {
    const response = await request;
    this.setResponse(response);
  } catch (error: any) {
    console.error(`Request failed: ${error.message}`);
    console.error(`Path: ${path}`);
    throw error;
  }
});

// Try both patterns - Cucumber might need exact match
When('I send a POST request to {string} with body:', async function (this: CustomWorld, path: string, docString: string) {
  if (!docString) {
    throw new Error('Doc string body is required but was not provided');
  }
  const processedBody = this.processBody(docString);
  const request = (this.request.post as any)(path)
    .set('Content-Type', 'application/json')
    .timeout(30000) // 30 second timeout
    .send(processedBody);
  try {
    const response = await request;
    this.setResponse(response);
  } catch (error: any) {
    console.error(`Request failed: ${error.message}`);
    console.error(`Path: ${path}`);
    console.error(`Body:`, JSON.stringify(processedBody, null, 2));
    throw error;
  }
});

When('I send a GET request to {string} with body:', async function (this: CustomWorld, path: string, docString: string) {
  if (!docString) {
    throw new Error('Doc string body is required but was not provided');
  }
  const processedBody = this.processBody(docString);
  const request = (this.request.get as any)(path)
    .set('Content-Type', 'application/json')
    .send(processedBody);
  const response = await request;
  this.setResponse(response);
});

When('I send a PUT request to {string} with body:', async function (this: CustomWorld, path: string, docString: string) {
  if (!docString) {
    throw new Error('Doc string body is required but was not provided');
  }
  const processedBody = this.processBody(docString);
  const request = (this.request.put as any)(path)
    .set('Content-Type', 'application/json')
    .send(processedBody);
  const response = await request;
  this.setResponse(response);
});

When('I send a DELETE request to {string} with body:', async function (this: CustomWorld, path: string, docString: string) {
  if (!docString) {
    throw new Error('Doc string body is required but was not provided');
  }
  const processedBody = this.processBody(docString);
  const request = (this.request.delete as any)(path)
    .set('Content-Type', 'application/json')
    .send(processedBody);
  const response = await request;
  this.setResponse(response);
});

// Generic pattern as fallback
When('I send a {string} request to {string} with body:', async function (this: CustomWorld, method: string, path: string, docString: string) {
  if (!docString) {
    throw new Error('Doc string body is required but was not provided');
  }
  const processedBody = this.processBody(docString);
  const methodLower = method.toLowerCase() as 'get' | 'post' | 'put' | 'delete' | 'patch';
  
  const request = (this.request[methodLower] as any)(path)
    .set('Content-Type', 'application/json')
    .timeout(30000) // 30 second timeout
    .send(processedBody);
  
  try {
    const response = await request;
    this.setResponse(response);
  } catch (error: any) {
    console.error(`Request failed: ${error.message}`);
    console.error(`Path: ${path}`);
    console.error(`Body:`, JSON.stringify(processedBody, null, 2));
    throw error;
  }
});

When('I send a {string} request to {string} with query parameters:', async function (this: CustomWorld, method: string, path: string, dataTable: DataTable) {
  const queryParams: Record<string, any> = {};
  for (const row of dataTable.rows()) {
    const [key, value] = row;
    queryParams[key] = this.processValue(value);
  }
  
  const methodLower = method.toLowerCase() as 'get' | 'post' | 'put' | 'delete' | 'patch';
  const request = (this.request[methodLower] as any)(path).query(queryParams);
  const response = await request;
  this.setResponse(response);
});

// Specific patterns for better Cucumber matching
When('I send a GET request to {string}', async function (this: CustomWorld, path: string) {
  const request = (this.request.get as any)(path);
  const response = await request;
  this.setResponse(response);
});

When('I send a POST request to {string} with headers:', async function (this: CustomWorld, path: string, dataTable: DataTable) {
  const headers: Record<string, string> = {};
  for (const row of dataTable.rows()) {
    const [key, value] = row;
    headers[key] = this.processValue(value);
  }
  
  const request = (this.request.post as any)(path)
    .set(headers)
    .timeout(30000); // 30 second timeout
  try {
    const response = await request;
    this.setResponse(response);
  } catch (error: any) {
    console.error(`Request failed: ${error.message}`);
    console.error(`Path: ${path}`);
    throw error;
  }
});

When('I send a GET request to {string} with headers:', async function (this: CustomWorld, path: string, dataTable: DataTable) {
  const headers: Record<string, string> = {};
  for (const row of dataTable.rows()) {
    const [key, value] = row;
    headers[key] = this.processValue(value);
  }
  
  const request = (this.request.get as any)(path)
    .set(headers)
    .timeout(30000); // 30 second timeout
  try {
    const response = await request;
    this.setResponse(response);
  } catch (error: any) {
    console.error(`Request failed: ${error.message}`);
    console.error(`Path: ${path}`);
    throw error;
  }
});

When('I send a {string} request to {string} with headers:', async function (this: CustomWorld, method: string, path: string, dataTable: DataTable) {
  const headers: Record<string, string> = {};
  for (const row of dataTable.rows()) {
    const [key, value] = row;
    headers[key] = this.processValue(value);
  }
  
  const methodLower = method.toLowerCase() as 'get' | 'post' | 'put' | 'delete' | 'patch';
  const request = (this.request[methodLower] as any)(path).set(headers);
  const response = await request;
  this.setResponse(response);
});

When('I send a {string} request to {string} with body and headers:', async function (this: CustomWorld, method: string, path: string, body: string, dataTable: DataTable) {
  const processedBody = this.processBody(body);
  
  const headers: Record<string, string> = {};
  for (const row of dataTable.rows()) {
    const [key, value] = row;
    headers[key] = this.processValue(value);
  }
  
  const methodLower = method.toLowerCase() as 'get' | 'post' | 'put' | 'delete' | 'patch';
  const request = (this.request[methodLower] as any)(path)
    .set(headers)
    .set('Content-Type', 'application/json')
    .send(processedBody);
  
  const response = await request;
  this.setResponse(response);
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

Then('the response status should be {int} or {int} or {int}', function (this: CustomWorld, code1: number, code2: number, code3: number) {
  const status = this.getResponse().status;
  expect([code1, code2, code3]).to.include(status);
});

Then('the response should contain JSON:', function (this: CustomWorld, expectedJson: string) {
  const responseJson = this.getResponse().body;
  const expected = JSON.parse(expectedJson);
  
  this.validatePartialMatch(responseJson, expected);
});

Then('the response should match schema:', function (this: CustomWorld, schemaJson: string) {
  const responseJson = this.getResponse().body;
  const schema = JSON.parse(schemaJson);
  
  this.validatePartialMatch(responseJson, schema);
});

Then('the response {string} should be {string}', function (this: CustomWorld, fieldPath: string, expectedValue: string) {
  const value = this.getNestedValue(this.getResponse().body, fieldPath);
  const processedExpected = this.processValue(expectedValue);
  expect(value).to.equal(processedExpected);
});

Then('the response {string} should be a number', function (this: CustomWorld, fieldPath: string) {
  const value = this.getNestedValue(this.getResponse().body, fieldPath);
  expect(value).to.be.a('number');
});

Then('the response {string} should match regex {string}', function (this: CustomWorld, fieldPath: string, regexPattern: string) {
  const value = this.getNestedValue(this.getResponse().body, fieldPath);
  const regex = new RegExp(regexPattern);
  expect(String(value)).to.match(regex);
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

