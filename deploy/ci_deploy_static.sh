#!/usr/bin/env bash

# This script is to deploy the additional static installation of DOAJ on the test server.

# Run from the doaj folder that's already checked out
# activate the virtualenv that we expect to be at /home/cloo/doaj
. /home/cloo/doaj-static/bin/activate
cd /home/cloo/doaj-static/src/doaj

# Install DOAJ submodules and requirements
git submodule update --init --recursive
pip install -e .

# Get the static test secrets configuration secrets from AWS
aws --profile doaj-test secretsmanager get-secret-value --secret-id doaj/static-credentials | cut -f4 | base64 -d > app.cfg

# Compile the static pages
python portality/cms/build_fragments.py
if test -f "cms/error_fragments.txt"; then
  exit 1
fi

# compile the sass
python portality/cms/build_sass.py
if test -f "cms/error_sass.txt"; then
  exit 1
fi

# Restart the static site only, then reload nginx.
sudo supervisorctl update
sudo supervisorctl restart doaj-static || sudo supervisorctl start doaj-static

sudo nginx -t && sudo nginx -s reload
