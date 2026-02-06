#!/bin/bash
# Script to start the Perl API for contract testing
# This connects the Perl API to the Testcontainers PostgreSQL and Redis

set -e

cd "$(dirname "$0")/../api"

# Check if Testcontainers environment variables are set
if [ -z "$POSTGRES_HOST" ] || [ -z "$POSTGRES_PORT" ]; then
    echo "❌ Error: Testcontainers environment variables not set"
    echo "   Run 'npm test' first to start Testcontainers, then in another terminal:"
    echo "   export POSTGRES_HOST=\$(docker inspect testcontainers-ryuk | jq -r '.[0].NetworkSettings.Networks[].Gateway')"
    echo "   export POSTGRES_PORT=5432"
    echo "   export POSTGRES_DB=penhas_test"
    echo "   export POSTGRES_USER=postgres"
    echo "   export POSTGRES_PASSWORD=trustme"
    echo "   export REDIS_HOST=\$POSTGRES_HOST"
    echo "   export REDIS_PORT=6379"
    echo "   export API_PORT=8080"
    echo "   ./start-perl-api.sh"
    exit 1
fi

echo "🚀 Starting Perl API for contract testing..."
echo "   PostgreSQL: $POSTGRES_HOST:$POSTGRES_PORT"
echo "   Redis: $REDIS_HOST:$REDIS_PORT"
echo "   API will listen on: http://localhost:${API_PORT:-8080}"
echo ""
echo "⚠️  Note: The tests will connect to the API at http://localhost:${API_PORT:-8080}"
echo "   Make sure this matches the PERL_URL environment variable if set."

# Source perlbrew if available
if [ -f "$HOME/perl5/perlbrew/etc/bashrc" ]; then
    source "$HOME/perl5/perlbrew/etc/bashrc"
fi

# Set environment variables for Perl API
export POSTGRESQL_HOST="$POSTGRES_HOST"
export POSTGRESQL_PORT="$POSTGRES_PORT"
export POSTGRESQL_DBNAME="$POSTGRES_DB"
export POSTGRESQL_USER="$POSTGRES_USER"
export POSTGRESQL_PASSWORD="$POSTGRES_PASSWORD"
export REDIS_SERVER="${REDIS_HOST}:${REDIS_PORT}"
export REDIS_NS=""
export API_PORT="${API_PORT:-8080}"
export API_WORKERS="1"
export SQITCH_DEPLOY="docker"
export TZ="Etc/UTC"

# Source envfile if it exists
if [ -f "envfile.sh" ]; then
    source envfile.sh
fi

# Deploy database schema
echo "📦 Deploying database schema..."
sqitch deploy -t docker || echo "⚠️  Schema deployment failed, continuing anyway..."

# Start the API using morbo (development server) for easier debugging
echo "🌐 Starting Mojolicious API server..."
exec morbo script/penhas-api --listen "http://*:${API_PORT}"

