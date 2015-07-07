DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
mkdir -p /home/cloo/appdata/doaj
mkdir -p /home/cloo/appdata/doaj/cache
mkdir -p /home/cloo/appdata/doaj/cache/csv
mkdir -p /home/cloo/appdata/doaj/cache/sitemap
mkdir -p /home/cloo/appdata/doaj/upload
mkdir -p /home/cloo/appdata/doaj/upload_reapplication
mkdir -p /home/cloo/appdata/doaj/reapp_csvs

sudo supervisorctl reread doaj-test
sudo supervisorctl update doaj-test
kill -HUP $(sudo supervisorctl pid doaj-test)

echo "Setting up crontab and anacrontab"
crontab $DIR/crontab-test-apps
sudo rm -f /etc/anacrontab && sudo ln -sf $DIR/anacrontab-test-apps /etc/anacrontab
