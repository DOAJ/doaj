#!/usr/bin/env bash

# apt dependencies for the DOAJ app
sudo apt-get update
sudo apt-get install -q -y libxml2-dev libxslt-dev python-dev lib32z1-dev awscli

# Run from the doaj folder that's already checked out

# activate the virtualenv that we expect to be at /home/cloo/doaj
. /home/cloo/doaj/bin/activate
cd /home/cloo/doaj/src/doaj

# Install DOAJ submodules and requirements
git submodule update --init --recursive
pip install -r requirements.txt

# Get the app configuration secrets from AWS  - NOTE: on a mac, base64 needs -D rather than -d
aws --profile doaj-app secretsmanager get-secret-value --secret-id doaj/app-credentials | cut -f4 | base64 -d > app.cfg

# Restart all supervisor tasks, which will cover the app, and huey on the background server. Then reload nginx.
sudo supervisorctl reread
sudo supervisorctl restart all || sudo supervisorctl start all
sudo nginx -t && sudo nginx -s reload
