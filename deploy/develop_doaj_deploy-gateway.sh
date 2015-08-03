DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
# recreate the virtualenv, so go all the way out of it
# after checking it's the right dir to delete
cd $DIR/../../../
CHECK_DIR=`basename "$PWD"`

[ ! "$CHECK_DIR" = "doaj" ] && echo "Wrong virtualenv name, expected 'doaj' so it could be deleted and recreated" && exit 1
cd ..
rm -rf doaj
virtualenv doaj
cd doaj
. bin/activate
pip install pip --upgrade
mkdir src
cd src
git clone https://github.com/DOAJ/doaj.git doaj
cd doaj

git submodule update --recursive --init
git submodule update --recursive

# symlink the app config into place
ln -sf /home/cloo/repl/test/appconfig/doaj-test.cfg test.cfg
ln -sf /home/cloo/repl/test/appconfig/doaj-test-deploy-newrelic.ini deploy/newrelic.ini

# install app on gate
sudo apt-get update -q -y
sudo apt-get -q -y install libxml2-dev libxslt-dev python-dev lib32z1-dev
pip install -r requirements.txt

# prep sym links for the test server
ln -sf $DIR/supervisor/doaj-test.conf /home/cloo/repl/test/supervisor/conf.d/doaj-test.conf
ln -sf $DIR/nginx/doaj-test /home/cloo/repl/test/nginx/sites-available/doaj-test
ln -sf /home/cloo/repl/test/nginx/sites-available/doaj-test /home/cloo/repl/test/nginx/sites-enabled/doaj-test

# prep sym links for gateway
ln -sf /home/cloo/repl/test/doaj/src/doaj/deploy/nginx/doaj-gate /home/cloo/repl/gateway/nginx/sites-available/doaj-gate
ln -sf /home/cloo/repl/gateway/nginx/sites-available/doaj-gate /home/cloo/repl/gateway/nginx/sites-enabled/doaj-gate

# replicate across test servers
/home/cloo/repl/replicate.sh
/home/cloo/repl/command.sh test /home/cloo/repl/test/doaj/src/doaj/deploy/develop_doaj_deploy-apps.sh

# reload the config if syntax is OK
sudo nginx -t && sudo nginx -s reload
