# Penhas Contract Tests

Cucumber.js contract tests for Perl → Python migration (Golden Master / Characterization Testing).

## Overview

This test suite captures the **exact behavior** of the Perl Mojolicious backend to serve as a golden master for implementing the Python FastAPI backend at `/api-v2`.

**Important:** These are characterization tests. Once the baseline is established, the feature files should be frozen (read-only) to maintain the contract.

## Prerequisites

- Node.js 18+ and npm
- Docker (for Testcontainers and Perl API)
  - Docker Desktop with sufficient resources (4GB+ RAM recommended)
  - Platform emulation enabled (for ARM64 Macs)

## Installation

```bash
cd api-contract-tests
npm install
```

## Configuration

### Environment Variables

- `TARGET` - Backend target: `perl` (default) or `python`
- `PERL_URL` - Perl backend URL (default: `http://localhost:8080`)
- `PYTHON_URL` - Python backend URL (default: `http://localhost:8000`)
- `IS_TEST` - Set to `1` to enable test-only features (like `_test_only_id` in responses)

### Automatic API Startup

**The Perl API starts automatically in Docker when you run `npm test`.** 

The test infrastructure will:
1. Start Testcontainers (PostgreSQL + Redis)
2. Load database schema from Sqitch migrations
3. **Automatically start the Perl API in Docker** connected to Testcontainers
4. Run the tests
5. Clean up everything when done

**How it works:**
- The Perl API runs in a Docker container using the image from `docker-compose.yaml`
- If the image doesn't exist locally, it will attempt to pull it (with platform emulation for ARM64)
- If pulling fails (e.g., no ARM64 build), it will build the image locally from `api/docker/Dockerfile`
- The container connects to Testcontainers via Docker gateway (`host.docker.internal` or `172.17.0.1`)
- Port 8080 is mapped to `localhost:8080` for test access

**First-time setup:**
- The first run may take 5-10 minutes if building the Docker image
- Subsequent runs will be faster as the image is cached
- You can pre-build the image: `docker build -f api/docker/Dockerfile -t penhas-api-test api/`

#### Manual API Startup (if automatic fails)

If you need to start the API manually:

```bash
# Export Testcontainers connection details (shown in test output)
export POSTGRESQL_HOST="localhost"  # From test output
export POSTGRESQL_PORT="<port>"     # From test output
export POSTGRESQL_DBNAME="penhas_test"
export POSTGRESQL_USER="postgres"
export POSTGRESQL_PASSWORD="trustme"
export REDIS_SERVER="localhost:<port>"  # From test output
export API_PORT="8080"
export CPF_CACHE_HASH_SALT="test-salt"
export PUBLIC_API_URL="http://localhost:8080/"

# Start the API
cd api
morbo script/penhas-api --listen "http://*:8080"
# OR
perl script/penhas-api daemon -l http://*:8080
```

### Testcontainers

Tests automatically start PostgreSQL (with PostGIS) and Redis containers using Testcontainers. The database schema is loaded from `../api/deploy_db/deploy/*.sql` migrations in Sqitch order.

## Running Tests

### Run all tests
```bash
npm test
```

### Run tests against Perl backend
```bash
npm run test:perl
# or
TARGET=perl npm test
```

### Run tests against Python backend (future)
```bash
npm run test:python
# or
TARGET=python npm test
```

### Run specific feature
```bash
npm run test:auth
```

### Run with tags
```bash
# Run only @auth tagged scenarios
npx cucumber-js --tags '@auth'

# Run only @perl tagged scenarios
npx cucumber-js --tags '@perl'

# Exclude @wip scenarios
npx cucumber-js --tags 'not @wip'
```

### Verify stability (100 runs)
```bash
npm run test:stable
```

### Watch mode (auto-reload on changes)
```bash
npm run test:watch
```

### Generate HTML report
```bash
npm test
npm run report  # Opens reports/report.html
```

## Test Structure

```
api-contract-tests/
├── features/              # Gherkin feature files
│   └── auth.feature       # Authentication scenarios
├── step-definitions/      # TypeScript step definitions
│   ├── api-steps.ts       # HTTP request/response steps
│   ├── db-steps.ts        # Database setup/assertion steps
│   ├── hooks.ts           # Before/After hooks
│   └── world.ts           # Custom World context
├── support/               # Test infrastructure
│   ├── testcontainers.ts  # Testcontainers manager
│   └── global-hooks.ts    # Global setup/teardown
├── cucumber.js            # Cucumber configuration
├── tsconfig.json          # TypeScript configuration
└── package.json           # Dependencies and scripts
```

## Writing Tests

### Example Scenario

```gherkin
@perl @auth @clean
Scenario: POST /signup creates new user successfully
  When I send a POST request to "/signup" with body:
    """
    {
      "dry": 0,
      "email": "<email>",
      "senha": "SecurePass123!",
      "nome_completo": "Maria Silva",
      "dt_nasc": "1990-01-15",
      "cpf": "544.340.690-63",
      "cep": "01310100",
      "genero": "Feminino",
      "apelido": "Maria",
      "raca": "Parda",
      "app_version": "1.0.0"
    }
    """
  Then the response status should be 200
  And the response should contain JSON:
    """
    {
      "session": "#regex .+",
      "_test_only_id": "#number"
    }
    """
  And I store the response "session" as "sessionId"
```

### Available Step Definitions

#### HTTP Requests
- `Given I am testing the "{string}" backend`
- `When I send a {string} request to {string}`
- `When I send a {string} request to {string} with body:`
- `When I send a {string} request to {string} with headers:`
- `When I send a {string} request to {string} with body and headers:`

#### Response Assertions
- `Then the response status should be {int}`
- `Then the response should contain JSON:`
- `Then the response {string} should be {string}`
- `Then the response {string} should be a number`
- `Then the response {string} should match regex {string}`

#### Data Storage
- `Then I store the response {string} as {string}`
- `Then I store the response body as {string}`

#### Database
- `Given I have a clean database`
- `Given the database has a user with email {string}`
- `Then the database should have {int} users`

### Placeholders

- `<random>` - Random alphanumeric string
- `<timestamp>` - Current timestamp
- `<uuid>` - UUID v4
- `<email>` - Unique test email
- `<sessionId>` - Stored session token (from previous step)
- `<userId>` - Stored user ID (from previous step)

### Special Matchers

In JSON assertions, use these special matchers:
- `#regex <pattern>` - Match regex pattern
- `#number` - Must be a number
- `#string` - Must be a string
- `#boolean` - Must be a boolean
- `#array` - Must be an array
- `#object` - Must be an object
- `#null` - Must be null
- `#notnull` - Must not be null

## Tags

- `@perl` - Tests for Perl backend
- `@python` - Tests for Python backend (future)
- `@auth` - Authentication-related tests
- `@clean` - Requires clean database
- `@creates-user` - Creates a user (for cleanup)
- `@wip` - Work in progress (excluded by default)

## Golden Master Process

1. **Establish Baseline**: Run tests against Perl backend until 100% pass rate
2. **Verify Stability**: Run `npm run test:stable` (100 runs) to ensure consistency
3. **Freeze Tests**: Mark feature files as read-only, tag commit as `perl-golden-master-v1.0`
4. **Document**: All response formats, error codes, and edge cases are now documented
5. **Future**: Use same tests to drive Python FastAPI implementation (TDD)

## Troubleshooting

### Testcontainers not starting
- Ensure Docker is running
- Check Docker has enough resources allocated
- Try `docker ps` to verify containers

### Database connection errors
- Verify Testcontainers started successfully
- Check environment variables are set correctly
- Ensure Perl backend can reach `host.testcontainers.internal`

### Tests failing against Perl backend
- **Most common issue**: Perl API Docker container failed to start
  - Check console output for Docker errors
  - Ensure Docker is running: `docker ps`
  - Check Docker has enough resources (4GB+ RAM recommended)
  - Verify Docker can access the API directory: `ls api/`
  - Check container logs: `docker logs <container-id>` (shown in test output)
  - For ARM64 Macs: Ensure Docker Desktop has platform emulation enabled
- **Docker image issues:**
  - If image pull fails, it will attempt to build locally (takes 5-10 minutes)
  - Pre-build the image: `docker build -f api/docker/Dockerfile -t penhas-api-test api/`
  - Check image exists: `docker images | grep penhas`
- Verify Perl API is listening: `curl http://localhost:8080` (should not return connection refused)
- Check `PERL_URL` environment variable (default: `http://localhost:8080`)
- Ensure database migrations are applied (done automatically by Testcontainers)
- Check container status: `docker ps | grep penhas-api-test`
- Ensure container can reach Testcontainers (uses Docker gateway, shown in test output)

## Notes

- Tests use `host.testcontainers.internal` to connect backends to Testcontainers DB
- Database cleanup uses TRUNCATE with CASCADE for speed
- JWT secret must match between test setup and Perl backend (use test secret)
- CPF `544.340.690-63` is used for all signup tests (valid test CPF)
