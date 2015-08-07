#!/usr/bin/env bash
# TODO don't delete source code, just delete package info, move src dir out of the way, then put it back in
# otherwise we can't check out a specific tag
THIS_SCRIPT=`basename "$0"`
[ $# -ne 1 ] && echo "Call this script as $THIS_SCRIPT <environment: [production, staging, test]>" && exit 1

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

# prep sym links for the app server
ln -sf $DIR/supervisor/doaj-$ENV.conf /home/cloo/repl/$ENV/supervisor/conf.d/doaj-$ENV.conf
ln -sf $DIR/nginx/doaj-$ENV /home/cloo/repl/$ENV/nginx/sites-available/doaj-$ENV
ln -sf /home/cloo/repl/$ENV/nginx/sites-available/doaj-$ENV /home/cloo/repl/$ENV/nginx/sites-enabled/doaj-$ENV

# prep sym links for gateway
ln -sf /home/cloo/repl/$ENV/doaj/src/doaj/deploy/nginx/doaj-gate /home/cloo/repl/gateway/nginx/sites-available/doaj-gate
ln -sf /home/cloo/repl/gateway/nginx/sites-available/doaj-gate /home/cloo/repl/gateway/nginx/sites-enabled/doaj-gate

# replicate across servers
/home/cloo/repl/replicate.sh
/home/cloo/repl/command.sh $ENV /home/cloo/repl/$ENV/doaj/src/doaj/deploy/deploy-apps.sh $ENV

# reload the config if syntax is OK
sudo nginx -t && sudo nginx -s reload
