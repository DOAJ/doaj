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

echo "Setting up crontab and anacrontab"
crontab $DIR/crontab-production-apps
sudo rm -f /etc/anacrontab && sudo ln -sf $DIR/anacrontab-production-apps /etc/anacrontab
