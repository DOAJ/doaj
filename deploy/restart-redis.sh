#!/usr/bin/env bash

THIS_SCRIPT=`basename "$0"`
[ $# -ne 1 ] && echo "Call this script as $THIS_SCRIPT <environment: [production, staging, test, harvester]>" && exit 1

ENV=$1

cd /home/cloo/repl/$ENV/doaj/src/doaj/docker
docker-compose down || true  # it's fine to fail to bring down redis if it is not started yet
# for the line below:
# --build to pick up docker/redis/Dockerfile changes
# --remove-orphans to remove all containers that are not defined in the docker/docker-compose.yml (allows us to change service names and configuration just by editing that file and deploying
# -d for detached mode rather than run in foreground
docker-compose up --build --remove-orphans -d
