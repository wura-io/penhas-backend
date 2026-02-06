import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';
import * as fs from 'fs/promises';
import { testContainers } from './testcontainers';

const execAsync = promisify(exec);

interface PerlApiConfig {
    host: string;
    port: number;
    containerId?: string;
}

class PerlApiManager {
    private static instance: PerlApiManager;
    private containerId: string | null = null;
    private started = false;
    private config: PerlApiConfig | null = null;
    private apiDir: string;
    private dataDir: string;
    private static readonly CONTAINER_PREFIX = 'penhas-api-test';

    private constructor() {
        this.apiDir = path.join(process.cwd(), '..', 'api');
        this.dataDir = path.join(process.cwd(), '..', 'data');
    }

    static getInstance(): PerlApiManager {
        if (!PerlApiManager.instance) {
            PerlApiManager.instance = new PerlApiManager();
        }
        return PerlApiManager.instance;
    }

    private async getDockerGateway(): Promise<string> {
        try {
            // Try to get Docker gateway IP
            const { stdout } = await execAsync("docker network inspect bridge | grep -A 1 Gateway | grep -oE '[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}' | head -1");
            return stdout.trim() || 'host.docker.internal';
        } catch {
            // Fallback to host.docker.internal (works on Mac/Windows)
            return 'host.docker.internal';
        }
    }

    private async cleanupStaleContainers(): Promise<void> {
        try {
            const { stdout } = await execAsync(
                `docker ps -a --filter "name=${PerlApiManager.CONTAINER_PREFIX}" --format "{{.Names}}" 2>/dev/null`
            );
            const containers = stdout.trim().split('\n').filter(Boolean);
            if (containers.length > 0) {
                console.log(`   Cleaning up ${containers.length} stale test container(s)...`);
                for (const name of containers) {
                    try {
                        await execAsync(`docker rm -f ${name} 2>/dev/null`);
                        console.log(`   Removed: ${name}`);
                    } catch {
                        // Ignore errors removing individual containers
                    }
                }
            }
        } catch {
            // Ignore errors listing containers
        }
    }

    private async checkDockerImage(): Promise<string> {
        // Use the image from docker-compose
        const imageName = 'ghcr.io/institutoazmina/penhas-backend:5ad72c21ae05c873a7a29bbc7d5470cc70aa5348';
        const localImageName = 'penhas-api-test';

        try {
            // Check if image exists locally
            await execAsync(`docker image inspect ${imageName} > /dev/null 2>&1`);
            console.log(`   Using existing Docker image: ${imageName}`);
            return imageName;
        } catch {
            // Image doesn't exist locally, try to pull it with platform emulation
            console.log(`   Docker image not found locally, attempting to pull (with platform emulation)...`);
            try {
                // Try to pull with linux/amd64 platform for compatibility
                await execAsync(`docker pull --platform linux/amd64 ${imageName}`, {
                    timeout: 300000, // 5 minutes for pull
                });
                console.log(`   Successfully pulled Docker image: ${imageName}`);
                return imageName;
            } catch (error: any) {
                console.log(`   Failed to pull image, attempting to build locally...`);
                // Fallback: build the image locally
                try {
                    const apiDir = this.apiDir;
                    const dockerfilePath = path.join(apiDir, 'docker', 'Dockerfile');
                    console.log(`   Building Docker image from ${dockerfilePath}...`);
                    console.log(`   (This may take 5-10 minutes on first build)`);
                    await execAsync(`docker build -f ${dockerfilePath} -t ${localImageName} ${apiDir}`, {
                        cwd: apiDir,
                        timeout: 600000, // 10 minutes for build
                    });
                    console.log(`   Successfully built Docker image: ${localImageName}`);
                    return localImageName;
                } catch (buildError: any) {
                    console.error(`   Failed to build image: ${buildError.message}`);
                    throw new Error(`Docker image not available and build failed. Please ensure Docker is running and the api directory is accessible.`);
                }
            }
        }
    }

    async start(): Promise<PerlApiConfig> {
        if (this.started) {
            return this.config!;
        }

        // Get Testcontainers config
        const dbConfig = testContainers.getConfig();

        if (!dbConfig) {
            throw new Error('Testcontainers must be started before Perl API');
        }

        // Kill any stale containers from previous runs
        await this.cleanupStaleContainers();

        console.log('🚀 Starting Perl API in Docker...');
        console.log(`   Connecting to PostgreSQL: ${dbConfig.postgres.host}:${dbConfig.postgres.port}`);
        console.log(`   Connecting to Redis: ${dbConfig.redis.host}:${dbConfig.redis.port}`);

        // Check if API directory exists
        try {
            await fs.access(this.apiDir);
        } catch (error) {
            throw new Error(`Perl API directory not found at ${this.apiDir}. Make sure you're running from the correct directory.`);
        }

        // Ensure data directory exists
        try {
            await fs.mkdir(this.dataDir, { recursive: true });
        } catch (error) {
            // Ignore if already exists
        }

        // Get Docker gateway to connect to Testcontainers from inside container
        // Use host.docker.internal which works on Mac/Windows, fallback to gateway on Linux
        const dockerGateway = process.platform === 'linux' 
            ? await this.getDockerGateway() 
            : 'host.docker.internal';
        console.log(`   Using Docker gateway: ${dockerGateway} to reach Testcontainers`);

        // Check/build Docker image
        const imageName = await this.checkDockerImage();
        console.log(`   Using Docker image: ${imageName}`);

        // Set up environment variables for the container
        // From inside the container, Testcontainers are accessible via host.docker.internal
        // But we need to use the actual host IP and ports
        const envVars = [
            `POSTGRESQL_HOST=${dockerGateway}`,
            `POSTGRESQL_PORT=${dbConfig.postgres.port}`,
            `POSTGRESQL_DBNAME=${dbConfig.postgres.db}`,
            `POSTGRESQL_USER=${dbConfig.postgres.user}`,
            `POSTGRESQL_PASSWORD=${dbConfig.postgres.password}`,
            `REDIS_SERVER=${dockerGateway}:${dbConfig.redis.port}`,
            `REDIS_NS=`,
            `API_PORT=8080`,
            `API_WORKERS=1`,
            `SQITCH_DEPLOY=none`, // Migrations already applied by Testcontainers via raw SQL
            `TZ=Etc/UTC`,
            `CPF_CACHE_HASH_SALT=${process.env.CPF_CACHE_HASH_SALT || 'test-salt-fixed-for-contract-tests'}`,
            `PUBLIC_API_URL=${process.env.PUBLIC_API_URL || 'http://localhost:8080/'}`,
            `APP_NAME=API`,
            `PENHAS_API_LOG_DIR=/data/log/`,
            `HARNESS_ACTIVE=1`, // Enable test mode in Perl API
            `IWEB_SERVICE_CHAVE=${process.env.IWEB_SERVICE_CHAVE || 'test-key'}`, // Prevent API crash if CPF lookup needed
            `MAX_CPF_ERRORS_IN_24H=10000`, // Allow many CPF errors in test mode
        ];

        // Build docker run command
        // Use dynamic port (0 = Docker picks a free host port) to avoid collisions
        const containerName = `${PerlApiManager.CONTAINER_PREFIX}-${Date.now()}`;
        const dockerArgs = [
            'run',
            '-d', // detached mode
            '--rm', // remove on exit
            `--name=${containerName}`,
            `--platform=linux/amd64`, // Use amd64 platform for compatibility
            `-p`, `127.0.0.1:0:8080`, // Dynamic host port mapped to container's 8080
            `-v`, `${this.apiDir}:/src`, // Mount API source
            `-v`, `${this.dataDir}:/data`, // Mount data directory
            ...envVars.flatMap(env => ['-e', env]),
            imageName,
        ];

        try {
            console.log(`   Starting container: ${containerName}...`);
            const { stdout: containerId } = await execAsync(`docker ${dockerArgs.join(' ')}`);
            this.containerId = containerId.trim();

            console.log(`   Container started: ${this.containerId.substring(0, 12)}...`);

            // Read the dynamically assigned host port
            const { stdout: portMapping } = await execAsync(
                `docker port ${this.containerId} 8080/tcp`
            );
            // Output format: "127.0.0.1:XXXXX" or "0.0.0.0:XXXXX"
            const hostPort = parseInt(portMapping.trim().split(':').pop()!, 10);
            if (isNaN(hostPort)) {
                throw new Error(`Could not determine mapped port from: ${portMapping.trim()}`);
            }
            console.log(`   Mapped host port: ${hostPort} -> container 8080`);

            // Wait for the API to be ready
            // Note: start-server.sh runs cpanm and sqitch deploy which can take 2-5 minutes
            console.log(`   Waiting for API to be ready (this may take 2-5 minutes on first run)...`);
            let ready = false;
            let attempts = 0;
            const maxAttempts = 300; // 5 minutes timeout (cpanm + sqitch can take time)

            while (!ready && attempts < maxAttempts) {
                await new Promise(resolve => setTimeout(resolve, 1000));
                attempts++;

                try {
                    // Check if container is still running
                    const { stdout: status } = await execAsync(`docker ps --filter id=${this.containerId} --format "{{.Status}}"`);
                    if (!status.trim()) {
                        // Container stopped, check logs
                        const { stdout: logs } = await execAsync(`docker logs ${this.containerId} 2>&1 | tail -20`);
                        throw new Error(`Container stopped unexpectedly. Logs:\n${logs}`);
                    }

                    // Check if API is actually listening on port 8080 inside container
                    try {
                        const { stdout: portCheck } = await execAsync(`docker exec ${this.containerId} sh -c "netstat -tlnp 2>/dev/null | grep :8080 || ss -tlnp 2>/dev/null | grep :8080 || echo 'not_listening'"`, {
                            timeout: 5000,
                        });

                        if (!portCheck.includes('not_listening') && portCheck.includes('8080')) {
                            // Port is listening, verify with HTTP request via the dynamic host port
                            const { stdout: curlOutput } = await execAsync(`curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:${hostPort}/ 2>&1 || echo "000"`, {
                                timeout: 6000,
                            });
                            const statusCode = curlOutput.trim();
                            // Accept any HTTP status code (200, 404, etc.) as long as we get a response
                            if (statusCode !== '000' && !statusCode.includes('Failed') && !statusCode.includes('refused')) {
                                ready = true;
                                break;
                            }
                        }
                    } catch (checkError: any) {
                        // Check failed, continue waiting
                    }
                } catch (error: any) {
                    // Connection failed, continue waiting
                    if (attempts % 30 === 0) {
                        // Check what's happening in the container
                        try {
                            const { stdout: serviceStatus } = await execAsync(`docker exec ${this.containerId} sv status api 2>&1 || echo "service_check_failed"`);
                            const { stdout: recentLogs } = await execAsync(`docker logs ${this.containerId} 2>&1 | tail -20 || echo ""`);
                            const { stdout: processes } = await execAsync(`docker exec ${this.containerId} ps aux 2>&1 | head -10 || echo ""`);
                            console.log(`   Still waiting... (${attempts}/${maxAttempts})`);
                            console.log(`   Service status: ${serviceStatus.trim()}`);
                            console.log(`   Running processes: ${processes.trim().split('\n').slice(0, 5).join(' | ')}`);
                            if (recentLogs.trim()) {
                                console.log(`   Recent logs: ${recentLogs.trim().split('\n').slice(-5).join('\n   ')}`);
                            }
                        } catch (logError: any) {
                            console.log(`   Still waiting... (${attempts}/${maxAttempts})`);
                        }
                    }
                }
            }

            if (!ready) {
                // Get logs for debugging
                const { stdout: logs } = await execAsync(`docker logs ${this.containerId} 2>&1 | tail -100`);
                const { stdout: apiLogs } = await execAsync(`docker exec ${this.containerId} cat /var/log/api/current 2>&1 || echo "No API logs"`);
                const { stdout: processes } = await execAsync(`docker exec ${this.containerId} ps aux 2>&1 || echo "Could not get processes"`);
                const { stdout: netstat } = await execAsync(`docker exec ${this.containerId} netstat -tlnp 2>&1 || docker exec ${this.containerId} ss -tlnp 2>&1 || echo "Could not check ports"`);
                throw new Error(`API did not become ready within ${maxAttempts} seconds.\nContainer logs:\n${logs}\n\nAPI logs:\n${apiLogs}\n\nRunning processes:\n${processes}\n\nListening ports:\n${netstat}`);
            }

            // Verify API is actually running by checking the process
            try {
                const { stdout: processes } = await execAsync(`docker exec ${this.containerId} ps aux | grep -E "(hypnotoad|penhas-api|perl)" | grep -v grep || echo "No API process found"`);
                if (!processes.trim() || processes.includes('No API process found')) {
                    // API not running, check service status and logs
                    const { stdout: serviceStatus } = await execAsync(`docker exec ${this.containerId} sv status api 2>&1 || echo "Service check failed"`);
                    const { stdout: apiServiceLogs } = await execAsync(`docker exec ${this.containerId} cat /var/log/api/current 2>&1 | tail -50 || echo "No API service logs"`);
                    console.log(`   ⚠️  API service status: ${serviceStatus.trim()}`);
                    console.log(`   ⚠️  API service logs:\n${apiServiceLogs.substring(0, 500)}`);
                    throw new Error('API service is not running in container. Check logs above.');
                }
                console.log(`   ✅ API processes found: ${processes.trim().split('\n').length} process(es)`);
            } catch (error: any) {
                if (error.message.includes('API service is not running')) {
                    throw error;
                }
                console.log(`   ⚠️  Could not check API processes: ${error.message}`);
            }

            console.log('✅ Perl API started successfully in Docker');
            this.started = true;
            this.config = {
                host: 'localhost',
                port: hostPort,
                containerId: this.containerId,
            };

            return this.config;
        } catch (error: any) {
            // Clean up container if it was created
            if (this.containerId) {
                try {
                    await execAsync(`docker rm -f ${this.containerId} 2>/dev/null || true`);
                } catch {
                    // Ignore cleanup errors
                }
            }

            throw new Error(`Failed to start Perl API in Docker: ${error.message}`);
        }
    }

    async stop() {
        if (!this.started || !this.containerId) {
            return;
        }

        console.log('🛑 Stopping Perl API container...');

        try {
            // Stop and remove the container
            await execAsync(`docker stop ${this.containerId} 2>/dev/null || true`);
            await execAsync(`docker rm -f ${this.containerId} 2>/dev/null || true`);
        } catch (error: any) {
            console.error(`⚠️  Error stopping Perl API container: ${error.message}`);
        }

        this.containerId = null;
        this.started = false;
        this.config = null;
        console.log('✅ Perl API container stopped');
    }

    getConfig(): PerlApiConfig | null {
        return this.config;
    }

    isStarted(): boolean {
        return this.started;
    }
}

export const perlApi = PerlApiManager.getInstance();
