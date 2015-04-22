DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
mkdir -p /home/cloo/appdata/doaj
mkdir -p /home/cloo/appdata/doaj/cache
mkdir -p /home/cloo/appdata/doaj/cache/csv
mkdir -p /home/cloo/appdata/doaj/cache/sitemap
mkdir -p /home/cloo/appdata/doaj/upload
mkdir -p /home/cloo/appdata/doaj/upload_reapplication
mkdir -p /home/cloo/appdata/doaj/reapp_csvs
sudo apt-get update -q -y
sudo apt-get -q -y install libxml2-dev libxslt-dev python-dev lib32z1-dev
cd $DIR/..
. ../../bin/activate
pip install -r requirements.txt
sudo supervisorctl reread doaj-production
sudo supervisorctl update doaj-production
kill -HUP $(sudo supervisorctl pid doaj-production)
crontab $DIR/crontab-production
sudo rm /etc/anacrontab
sudo ln -sf /home/cloo/repl/apps/doaj/src/doaj/deploy/anacrontab-production /etc/anacrontab
