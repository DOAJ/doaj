#!/usr/bin/env bash

# Environment is a required arg to this script
[ $# -ne 1 ] && echo "Call this script as `basename "$0"` <environment: [production, test]>" && exit 1
ENV=$1

# apt dependencies for the DOAJ app
sudo apt-get update
sudo apt-get install -q -y libxml2-dev libxslt-dev python3-dev python3-pip lib32z1-dev

# get awscli from pip so it's up to date (although installation will use the one from the virtualenv it's handy to have)
sudo pip install awscli

# Run from the doaj folder that's already checked out

# activate the virtualenv that we expect to be at /home/cloo/doaj
. /home/cloo/doaj/bin/activate
cd /home/cloo/doaj/src/doaj || exit 1

# Get the app configuration secrets from AWS  - NOTE: on a mac, base64 needs -D rather than -d
if [ "$ENV" = 'production' ]
then
    aws --profile doaj-app secretsmanager get-secret-value --secret-id doaj/app-credentials | cut -f4 | base64 -d > app.cfg
elif [ "$ENV" = 'test' ]
then
    aws --profile doaj-test secretsmanager get-secret-value --secret-id doaj/test-credentials | cut -f4 | base64 -d > app.cfg
fi

# Validate the secrets file so we don't try to install & restart the app if it's broken
if python -m py_compile app.cfg
then
    echo "Secrets file app.cfg is OK"
else
    echo "Error in secrets file app.cfg. Exiting."
    exit 1
fi

# Install DOAJ submodules and dependencies
git submodule update --init --recursive
pip install -e .

# Compile the static pages
python portality/cms/build_fragments.py
if test -f "cms/error_fragments.txt"; then
  echo "ABORT - fragment error:"
  cat cms/error_fragments.txt
  exit 1
fi

# compile the sass
python portality/cms/build_sass.py
if test -f "cms/error_sass.txt"; then
  echo "ABORT - sass error:"
  cat cms/error_sass.txt
  exit 1
fi

# Restart all supervisor tasks, will cover the app and kafka, plus huey on the background server. Then reload nginx.
sudo supervisorctl update
sudo supervisorctl restart all || sudo supervisorctl start all

# todo: we might want to move this to ansible so we don't run on the background server unnecessarily
sudo nginx -t && sudo nginx -s reload
