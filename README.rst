Portality - a web frontend based on elasticsearch by default.


Install
=======

sudo apt-get install python-pip python-dev build-essential

sudo pip install --upgrade pip

sudo pip install --upgrade virtualenv

sudo apt-get install git

wget https://github.com/downloads/elasticsearch/elasticsearch/elasticsearch-0.18.2.tar.gz

tar -xzvf elasticsearch-0.18.2.tar.gz

./elasticsearch-0.18.2/bin/elasticsearch start

virtualenv .

. ./bin/activate

git clone https://github.com/CottageLabs/portality.git

cd portality

git submodule init
git submodule update

# python setup.py install
pip install -e .

python portality/web.py


Customise
=========

Check out the Flask docs for further info

Customise dao.py to work with a different backend if you need to.

web.py controls the main routes. Add more if necessary. But note:

search.py catches all other web routes. Add to that too when it needs to be flexible.

There are default templates and useful javascript plugins in static. Add or alter 
them as necessary.


Run it
======

Use your preferred web server setup to expose your website. For example, nginx
proxy passing to the python script, which itself can be run using supervisord.


