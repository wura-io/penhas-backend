export POSTGRESQL_HOST="${POSTGRESQL_HOST:-172.17.0.1}"
export POSTGRESQL_PORT="${POSTGRESQL_PORT:-5432}"
export POSTGRESQL_DBNAME="${POSTGRESQL_DBNAME:-penhas_test}"
export POSTGRESQL_USER="${POSTGRESQL_USER:-postgres}"
export POSTGRESQL_PASSWORD="${POSTGRESQL_PASSWORD:-trustme}"

export SQITCH_DEPLOY="docker"

export API_PORT="8080"
export API_WORKERS="1"

# Set from docker
# export MYSQL_HOST="localhost"
# export MYSQL_PORT="3306"
# export MYSQL_DBNAME="directus"
# export MYSQL_USER="username"
# export MYSQL_PASSWORD="password"
