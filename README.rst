Portality - everything you need to build a web frontend.


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


