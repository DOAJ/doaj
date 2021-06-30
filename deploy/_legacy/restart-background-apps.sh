#!/usr/bin/env bash

THIS_SCRIPT=`basename "$0"`
[ $# -ne 1 ] && echo "Call this script as $THIS_SCRIPT <environment: [production, staging, test, harvester]>" && exit 1

ENV=$1

sudo supervisorctl reread huey-main-$ENV
sudo supervisorctl reread huey-long-running-$ENV
sudo supervisorctl update huey-main-$ENV
sudo supervisorctl update huey-long-running-$ENV
sudo supervisorctl restart huey-main-$ENV
sudo supervisorctl restart huey-long-running-$ENV
