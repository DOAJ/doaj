DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd $DIR/..
git submodule update --recursive --init
git submodule update --recursive

# prep sym links for app servers
ln -sf $DIR/supervisor/doaj-production.conf /home/cloo/repl/apps/supervisor/conf.d/doaj-production.conf
ln -sf $DIR/nginx/doaj-apps /home/cloo/repl/apps/nginx/sites-available/doaj-apps
ln -sf /home/cloo/repl/apps/nginx/sites-available/doaj-apps /home/cloo/repl/apps/nginx/sites-enabled/doaj-apps

# prep sym links for gateway
ln -sf /home/cloo/repl/apps/doaj/src/doaj/deploy/nginx/doaj-gate /home/cloo/repl/gateway/nginx/sites-available/doaj-gate
ln -sf /home/cloo/repl/gateway/nginx/sites-available/doaj-gate /home/cloo/repl/gateway/nginx/sites-enabled/doaj-gate

# replicate across app servers
/home/cloo/repl/replicate.sh
/home/cloo/repl/command.sh apps /home/cloo/repl/apps/doaj/src/doaj/deploy/production_doaj_deploy-apps.sh

# reload the config if syntax is OK
sudo nginx -t && sudo nginx -s reload

echo "Setting up crontab and anacrontab"
crontab $DIR/crontab-production-gate
sudo rm /etc/anacrontab && sudo ln -sf $DIR/anacrontab-production-gate /etc/anacrontab