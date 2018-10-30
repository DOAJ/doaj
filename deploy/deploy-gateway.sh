#!/usr/bin/env bash
# TODO don't delete source code, just delete package info, move src dir out of the way, then put it back in
# otherwise we can't check out a specific tag
THIS_SCRIPT=`basename "$0"`
[ $# -ne 1 ] && echo "Call this script as $THIS_SCRIPT <environment: [production, staging, test, harvester]>" && exit 1

ENV=$1

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
# recreate the virtualenv, so go all the way out of it
# after checking it's the right dir to delete
cd $DIR/../../../
CHECK_DIR=`basename "$PWD"`

[ ! "$CHECK_DIR" = "doaj" ] && echo "Wrong virtualenv name, expected 'doaj' so it could be deleted and recreated" && exit 1

# if everything's ok, time to move out the source code and recreate the virtualenv, and move the source code back in
rm -rf /home/cloo/tmp_deploy_workspace_$ENV
mkdir -p /home/cloo/tmp_deploy_workspace_$ENV
rm -rf src/doaj/doaj.egg-info
mv src /home/cloo/tmp_deploy_workspace_$ENV/doaj_src
cd ..
rm -rf doaj
virtualenv -p python2.7 doaj
cd doaj
. bin/activate
pip install --upgrade pip==10.0.1
mv /home/cloo/tmp_deploy_workspace_$ENV/doaj_src src
cd src/doaj

git submodule update --recursive --init
git submodule update --recursive

# install app on gate
sudo apt-get update -q -y
sudo apt-get -q -y install libxml2-dev libxslt-dev python-dev lib32z1-dev zip
pip install -r requirements.txt

# prep sym links for the app server
ln -sf $DIR/supervisor/$ENV/doaj-$ENV.conf /home/cloo/repl/$ENV/supervisor/conf.d/doaj-$ENV.conf
ln -sf $DIR/nginx/doaj-$ENV /home/cloo/repl/$ENV/nginx/sites-available/doaj-$ENV
ln -sf /home/cloo/repl/$ENV/nginx/sites-available/doaj-$ENV /home/cloo/repl/$ENV/nginx/sites-enabled/doaj-$ENV

# prep sym links for the background app server
ln -sf $DIR/supervisor/$ENV-background/huey-main-$ENV.conf /home/cloo/repl/$ENV-background/supervisor/conf.d/huey-main-$ENV.conf
ln -sf $DIR/supervisor/$ENV-background/huey-long-running-$ENV.conf /home/cloo/repl/$ENV-background/supervisor/conf.d/huey-long-running-$ENV.conf

# prep sym links for gateway
if [ "$ENV" = 'harvester' ]
then
    GATE_ENV=$ENV
else
    GATE_ENV=production
fi
ln -sf /home/cloo/repl/$GATE_ENV/doaj/src/doaj/deploy/nginx/doaj-$GATE_ENV-gate /home/cloo/repl/gateway/nginx/sites-available/doaj-$GATE_ENV-gate
ln -sf /home/cloo/repl/gateway/nginx/sites-available/doaj-$GATE_ENV-gate /home/cloo/repl/gateway/nginx/sites-enabled/doaj-$GATE_ENV-gate
ln -sf /home/cloo/repl/$GATE_ENV/doaj/src/doaj/deploy/nginx/gateway /home/cloo/repl/gateway/nginx/sites-available/gateway
ln -sf /home/cloo/repl/gateway/nginx/sites-available/gateway /home/cloo/repl/gateway/nginx/sites-enabled/gateway
ln -sf /home/cloo/repl/$GATE_ENV/doaj/src/doaj/deploy/nginx/block_user_agents.conf /home/cloo/repl/gateway/nginx/conf.d/block_user_agents.conf
ln -sf /home/cloo/repl/$GATE_ENV/doaj/src/doaj/deploy/nginx/proxy_pass_settings /home/cloo/repl/gateway/nginx/includes/proxy_pass_settings
sudo ln -sf /home/cloo/repl/$GATE_ENV/doaj/src/doaj/deploy/logrotate/doaj-duplicity /etc/logrotate.d/doaj-duplicity

# gateway crons
sudo ln -sf /home/cloo/repl/$GATE_ENV/doaj/src/doaj/deploy/anacrontab-$GATE_ENV-gate /etc/anacrontab
crontab /home/cloo/repl/$GATE_ENV/doaj/src/doaj/deploy/crontab-$GATE_ENV-gate

# Upload AWS Lambda functions
# todo: this could actually be better using an S3 client library and Lambda from S3 filesystem
# todo: populating .aws/credentials is a bit tricky at the moment. Again solved with S3 library above. (sort of)
# todo: when we have more than one function, they should each be in their own subdirectories named function-name.
if [ "$ENV" = 'production' ]
then
    aws --version
    cd deploy/lambda
    zip upload.zip *
    # Credentials must already be in ~/.aws/
    aws --profile doaj-production-lambda lambda update-function-code --function-name alertS3BackupsFailure --zip-file fileb://upload.zip --region=eu-west-1 --publish
    rm upload.zip
fi

# replicate across servers
/home/cloo/repl/replicate.sh
/home/cloo/repl/command.sh -v redis-$ENV /home/cloo/repl/$ENV/doaj/src/doaj/deploy/deploy-redis.sh $ENV
/home/cloo/repl/command.sh -v $ENV /home/cloo/repl/$ENV/doaj/src/doaj/deploy/deploy-apps.sh $ENV
/home/cloo/repl/command.sh -v $ENV-background /home/cloo/repl/$ENV/doaj/src/doaj/deploy/deploy-background-apps.sh $ENV
/home/cloo/repl/command.sh -v monitor /home/cloo/repl/$ENV/doaj/src/doaj/deploy/deploy-monitor.sh $ENV

# Restart gateway services
/home/cloo/repl/$GATE_ENV/doaj/src/doaj/deploy/restart-gateway.sh
