#!/usr/bin/env bash
THIS_SCRIPT=`basename "$0"`
[ $# -ne 1 ] && echo "Call this script as $THIS_SCRIPT <environment: [production, staging, test, harvester]>" && exit 1

ENV=$1

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
mkdir -p /home/cloo/appdata/doaj
mkdir -p /home/cloo/appdata/doaj/history
mkdir -p /home/cloo/appdata/doaj/history/article
mkdir -p /home/cloo/appdata/doaj/history/journal
mkdir -p /home/cloo/appdata/doaj/local_store
mkdir -p /home/cloo/appdata/doaj/local_store/main
mkdir -p /home/cloo/appdata/doaj/local_store/tmp

sudo apt-get update -q -y
sudo apt-get install -q -y redis-tools

echo "Mounting S3FS permanently"
cd /home/cloo/repl/$ENV/doaj
. bin/activate
cd src/doaj
chmod 600 .s3fs-credentials  # s3fs will refuse to use the credentials file if there are any Group or Other permissions on it
deploy/install_s3fs.sh
echo
echo "Attempting to unmount"
echo
DOAJENV=$1 python deploy/mount_s3fs.py -u || true  # try to unmount, but don't care if that doesn't work (e.g. s3fs is not mounted)

if [ $? -ne 0 ]; then echo; echo "Unmounting failed, but if the reason is that S3FS is already mounted then it can be ignored safely."; echo; fi

DOAJENV=$1 python deploy/mount_s3fs.py -p

if [ $? -eq 0 ]; then
    echo
    echo "Permanent mount seems to be in place. Now attempting to actually mount S3FS using the permanent settings."
    echo
    DOAJENV=$1 python deploy/mount_s3fs.py
fi

mkdir -p /home/cloo/appdata/doaj/s3fs
mkdir -p /home/cloo/appdata/doaj/s3fs/cache
mkdir -p /home/cloo/appdata/doaj/s3fs/cache/csv
mkdir -p /home/cloo/appdata/doaj/s3fs/cache/sitemap
mkdir -p /home/cloo/appdata/doaj/s3fs/upload

# Restart background apps services
/home/cloo/repl/$ENV/doaj/src/doaj/deploy/restart-background-apps.sh $ENV

echo "Setting up crontab and anacrontab"
crontab $DIR/crontab-$ENV-background-apps
sudo rm -f /etc/anacrontab && sudo ln -sf $DIR/anacrontab-$ENV-background-apps /etc/anacrontab
