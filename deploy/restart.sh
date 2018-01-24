#!/usr/bin/env bash
# Restart all DOAJ production services

THIS_SCRIPT=`basename "$0"`
[ $# -ne 1 ] && echo "Call this script as $THIS_SCRIPT <environment: [production, staging, test, harvester]>" && exit 1

ENV=$1

# Handle the exception for the harvester duplicate production site fixme: this should probably go since that testing is over
if [ "$ENV" = 'harvester' ]
then
    GATE_ENV=$ENV
else
    GATE_ENV=production
fi

/home/cloo/repl/command.sh -v redis-$ENV /home/cloo/repl/$ENV/doaj/src/doaj/deploy/restart-redis.sh $ENV
/home/cloo/repl/command.sh -v $ENV /home/cloo/repl/$ENV/doaj/src/doaj/deploy/restart-apps.sh $ENV
/home/cloo/repl/command.sh -v $ENV-background /home/cloo/repl/$ENV/doaj/src/doaj/deploy/restart-background-apps.sh $ENV
/home/cloo/repl/$GATE_ENV/doaj/src/doaj/deploy/restart-gateway.sh
