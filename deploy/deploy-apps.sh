#!/usr/bin/env bash
THIS_SCRIPT=`basename "$0"`
[ $# -ne 1 ] && echo "Call this script as $THIS_SCRIPT <environment: [production, staging, test, harvester]>" && exit 1

ENV=$1

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
mkdir -p /home/cloo/appdata/doaj
mkdir -p /home/cloo/appdata/doaj/cache
mkdir -p /home/cloo/appdata/doaj/cache/csv
mkdir -p /home/cloo/appdata/doaj/cache/sitemap
mkdir -p /home/cloo/appdata/doaj/upload
mkdir -p /home/cloo/appdata/doaj/upload_reapplication
mkdir -p /home/cloo/appdata/doaj/reapp_csvs
mkdir -p /home/cloo/appdata/doaj/history
mkdir -p /home/cloo/appdata/doaj/history/article
mkdir -p /home/cloo/appdata/doaj/history/journal
mkdir -p /home/cloo/appdata/doaj/s3fs

sudo supervisorctl reread doaj-$ENV
sudo supervisorctl update doaj-$ENV
kill -HUP $(sudo supervisorctl pid doaj-$ENV)

sudo nginx -t && sudo nginx -s reload

echo "Setting up crontab and anacrontab"
crontab $DIR/crontab-$ENV-apps
sudo rm -f /etc/anacrontab && sudo ln -sf $DIR/anacrontab-$ENV-apps /etc/anacrontab

echo "Mounting S3FS permanently"
cd /home/cloo/repl/$ENV/doaj
. bin/activate
cd src/doaj
deploy/install_s3fs.sh
DOAJENV=$1 python deploy/mount_s3fs.py -u || true  # try to unmount, but don't care if that doesn't work (e.g. s3fs is not mounted)
DOAJENV=$1 python deploy/mount_s3fs.py -p
