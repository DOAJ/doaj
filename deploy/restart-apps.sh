#!/usr/bin/env bash

THIS_SCRIPT=`basename "$0"`
[ $# -ne 1 ] && echo "Call this script as $THIS_SCRIPT <environment: [production, staging, test, harvester]>" && exit 1

ENV=$1

# Restart the python app under supervisor
sudo supervisorctl reread doaj-$ENV
sudo supervisorctl update doaj-$ENV
kill -HUP $(sudo supervisorctl pid doaj-$ENV)

# Restart nginx, which the app is running behind.
sudo nginx -t && sudo nginx -s reload
