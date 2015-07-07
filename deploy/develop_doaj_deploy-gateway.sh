DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd $DIR/..
git submodule update --recursive --init
git submodule update --recursive

# prep sym links for the test server
ln -sf $DIR/supervisor/doaj-test.conf /home/cloo/repl/test/supervisor/conf.d/doaj-test.conf
ln -sf $DIR/nginx/doaj-test /home/cloo/repl/test/nginx/sites-available/doaj-test
ln -sf /home/cloo/repl/test/nginx/sites-available/doaj-test /home/cloo/repl/test/nginx/sites-enabled/doaj-test

# prep sym links for gateway
ln -sf /home/cloo/repl/test/doaj/src/doaj/deploy/nginx/doaj-gate /home/cloo/repl/gateway/nginx/sites-available/doaj-gate
ln -sf /home/cloo/repl/gateway/nginx/sites-available/doaj-gate /home/cloo/repl/gateway/nginx/sites-enabled/doaj-gate

# install app on gate
sudo apt-get update -q -y
sudo apt-get -q -y install libxml2-dev libxslt-dev python-dev lib32z1-dev
cd $DIR/..
. ../../bin/activate
pip install -r requirements.txt

# replicate across test servers
/home/cloo/repl/replicate.sh
/home/cloo/repl/command.sh test /home/cloo/repl/test/doaj/src/doaj/deploy/develop_doaj_deploy-apps.sh

# reload the config if syntax is OK
sudo nginx -t && sudo nginx -s reload
