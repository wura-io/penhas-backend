#!/bin/bash -e
source /home/app/perl5/perlbrew/etc/bashrc
export TZ=Etc/UTC

mkdir -p /data/log/;

export PENHAS_API_LOG_DIR=/data/log/

cd /src;
if [ -f envfile_local.sh ]; then
    source envfile_local.sh
else
    source envfile.sh
fi

export SQITCH_DEPLOY=${SQITCH_DEPLOY:=docker}

cpanm -nv . --installdeps

# If using docker target, construct URI from environment variables and override sqitch config
if [ "$SQITCH_DEPLOY" = "none" ]; then
    echo "Skipping sqitch deploy (SQITCH_DEPLOY=none)"
elif [ "$SQITCH_DEPLOY" = "docker" ]; then
    SQITCH_URI="db:pg://${POSTGRESQL_USER:-postgres}:${POSTGRESQL_PASSWORD:-trustme}@${POSTGRESQL_HOST:-172.17.0.1}:${POSTGRESQL_PORT:-5432}/${POSTGRESQL_DBNAME:-penhas_test}"
    # Use sqitch deploy with explicit URI override
    sqitch deploy "$SQITCH_URI"
else
    sqitch deploy -t $SQITCH_DEPLOY
fi

LIBEV_FLAGS=4 APP_NAME=API MOJO_IOLOOP_DEBUG=1 hypnotoad script/penhas-api

sleep infinity