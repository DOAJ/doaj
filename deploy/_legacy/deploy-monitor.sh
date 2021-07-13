#!/usr/bin/env bash
THIS_SCRIPT=`basename "$0"`
[ $# -ne 1 ] && echo "Call this script as $THIS_SCRIPT <environment: [production, staging, test, harvester]>" && exit 1

ENV=$1

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )


if [ "$ENV" = 'production' ]
then
    echo "Setting up crontab and anacrontab"
    crontab $DIR/crontab-$ENV-monitor
else
    echo "Not setting up monitor crontab in $ENV - it only runs in production."
fi