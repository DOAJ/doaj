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
virtualenv doaj
cd doaj
. bin/activate
pip install pip --upgrade
mv /home/cloo/tmp_deploy_workspace_$ENV/doaj_src src
cd src/doaj

git submodule update --recursive --init
git submodule update --recursive

# install app on gate
sudo apt-get update -q -y
sudo apt-get -q -y install libxml2-dev libxslt-dev python-dev lib32z1-dev
pip install -r requirements.txt
# insert assorted swearwords and curses
pip install flask-swagger==0.2.8
pip install flask==0.9  # we need to bump flask to 10.1 and retest the app .. soon
pip install flask-cors==2.1.2 # for some reason this is not being picked up from setup.py?!
# none of these newly introduced requirements are being picked up by pip
# something's wrong with the virtualenv
pip install LinkHeader==0.4.3
pip install universal-analytics-python==0.2.4

# prep sym links for the app server
ln -sf $DIR/supervisor/doaj-$ENV.conf /home/cloo/repl/$ENV/supervisor/conf.d/doaj-$ENV.conf
ln -sf $DIR/nginx/doaj-$ENV /home/cloo/repl/$ENV/nginx/sites-available/doaj-$ENV
ln -sf /home/cloo/repl/$ENV/nginx/sites-available/doaj-$ENV /home/cloo/repl/$ENV/nginx/sites-enabled/doaj-$ENV

# prep sym links for gateway
if [ "$ENV" = 'harvester' ]
then
    GATE_ENV=$ENV
else
    GATE_ENV=production
fi
ln -sf /home/cloo/repl/$GATE_ENV/doaj/src/doaj/deploy/nginx/doaj-$GATE_ENV-gate /home/cloo/repl/gateway/nginx/sites-available/doaj-$GATE_ENV-gate
ln -sf /home/cloo/repl/gateway/nginx/sites-available/doaj-$GATE_ENV-gate /home/cloo/repl/gateway/nginx/sites-enabled/doaj-$GATE_ENV-gate

# gateway crons
sudo ln -sf /home/cloo/repl/$GATE_ENV/doaj/src/doaj/deploy/anacrontab-$GATE_ENV-gate /etc/anacrontab
crontab /home/cloo/repl/$GATE_ENV/doaj/src/doaj/deploy/crontab-$GATE_ENV-gate

# replicate across servers
/home/cloo/repl/replicate.sh
/home/cloo/repl/command.sh $ENV /home/cloo/repl/$ENV/doaj/src/doaj/deploy/deploy-apps.sh $ENV

# reload the config if syntax is OK
sudo nginx -t && sudo nginx -s reload
