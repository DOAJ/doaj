Portality - a web frontend based on elasticsearch.

This repo uses submodules - for more info: http://git-scm.com/book/en/Git-Tools-Submodules

This repo is a collection of useful things - it requires customisation in order 
to get working. Make sure you READ BELOW to get it up and running properly.

More information including a description of the various available default views
is available at http://cottagelabs.com/software/portality


Install
=======


sudo apt-get install python-pip python-dev build-essential

sudo pip install --upgrade pip

sudo pip install --upgrade virtualenv

sudo apt-get install git

virtualenv -p python2.7 portality –no-site-packages

cd portality

mkdir src

cd src

source ../../bin/activate

git clone https://github.com/CottageLabs/portality.git

cd portality

git submodule init
git submodule update

pip install gunicorn

# python setup.py install
pip install -e .


Dependencies
============

By default portality assumes an elasticsearch backend for the dao to talk to.
There are numerous ways to install elasticsearch, here is an example:

cd /opt

wget https://github.com/downloads/elasticsearch/elasticsearch/elasticsearch-0.18.2.tar.gz

tar -xzvf elasticsearch-0.18.2.tar.gz

ln -s elasticsearch-0.18.2 elasticsearch

cd elasticsearch


Then you should install the elasticsearch service, and create a user to run it 
on your system if you so desire. Then you should ensure that user has unlimited
ability to lock memory - to do this for root, it looks like this:

sudo su

ulimit -l unlimited


You should also set some config before you start elasticsearch - in the 
conf/elasticsearch.yml uncomment bootstrap.mlockall to enable it. Also set the 
RAM to as high a number as you can afford on your machine. Then to ensure you 
do not accidentally contaminate elasticsearch with indices from other running 
instances on the same network, set the elasticsearch group name to something 
that is not the default. That way, elasticsearch will only try to auto-shard 
between instances that you manually set to have that same group name. Then once 
you are ready to go, just do 

sudo /etc/init.d/elasticsearch start


Important configuration options
===============================

When you customise your app.cfg (read below) you should ensure you set a random 
long string as your secret key, and that you properly set the location of your 
elasticsearch instance, and any running info such as ports - making sure not 
to clash with other services running on your server. When you first start your 
system, you should create a new user with the same name as the SUPERUSER config 
setting - that account will then have full frontend admin control. If you want 
custom mappings in the elasticsearch index for your models, ensure they are 
defined in your config and they will be created when the system starts, if they 
are not already there - note also the config setting for the name you wish to 
use for your elasticsearch index.


Run it
======

Portality provides various useful default bits and pieces - you need to choose 
which ones you want and enable them. In the portality folder you will find a 
web.py file and a default_settings.py file - these are configured to setup 
everything that portality has, so you should copy web.py to a different file - 
say app.py - and then customsise it to only run the things you need. You should 
also make a copy of default_settings.py and call it app.cfg and put it in the 
folder above - the root folder of the portality repo. Then you can overwrite 
the settings and they will be read from there on startup.

For data access and modelling, the dao.py file defines the data access model 
which you can leave as is unless you want to change the backend, and the 
default_models.py file has some example data models that inherit from the dao.
You should symlink models.py to default_models.py if you want to use it as is, 
or else create a new models.py and write your own models into it.

When you first clone portality, it includes default_auth, default_view and 
default_templates folders - if you want to use their contents as is, you should 
symlink to each of them from folders called auth, view and templates. 
Alternatively, create folders called auth, view and templates and then copy/
paste the ones you want, and write your own. Each view that needs templates 
should have corresponding default templates in the templates folder.

Once you are fully setup with app.cfg, models.py, auth, view and templates, you 
can try running your app by calling your app file - using the example name of 
app.py, do the following:

python portality/app.py


A note about feeds
==================

There is a view called feed.py which provides data feeds, however it requires
lxml - however as this is a bit more complex to install, it is not called by 
the default web.py and lxml is commented out in the setup.py. So if you want to 
use the feed view, install the lxml requirements on your local system then 
uncomment lxml in the setup.py and re-install. You will then be able to import 
the feed view and use it as required. Some example code for getting lxml on an 
ubuntu machine (sudo / permissions required):

sudo apt-get install libxml2-dev libxslt-dev

sudo apt-get install lib32z1-dev

sudo apt-get install python-lxml


And if you get a weird error even then, note this particular problem with some 
versions of virtualenv on ubuntu - which I had even after upgrading virtualenv 
to the most recent version:

http://stackoverflow.com/questions/15608236/eclipse-and-google-app-engine-importerror-no-module-named-sysconfigdata-nd-u


Doing the symlink mentioned in the first answer solved it for me.

cd /usr/lib/python2.7

sudo ln -s plat-x86_64-linux-gnu/_sysconfigdata_nd.py .


Customise
=========

When you want to customise portality, you should start your own new git repo 
and then add portality as an upstream source. Then you can merge it with your 
own local master.

git remote add upstream https://github.com/CottageLabs/portality.git
git fetch upstream
git merge upstream/master

Next you should create real versions of the default files and folders as 
described above. Then you can edit them as you require, and when you next want 
to sync with portality, you can just fetch and merge from upstream again 
without conflicting with your local changes.

NOTE that if you do overwrite any of the other files in your own repo copy, you 
will need to check for conflicts after a fetch and merge, and fix them.

If you want to add your own javascript includes and things like that, put them 
in the static folder, but not in the portality folder

Check out the Flask docs for further info about the framework.

If you want to contribute your changes back up the fork and into portality, 
make sure you prepare a branch of your local repo that conforms to the portality
structure, ignore anything that is relevant only to your own specific instance, 
and send a pull request.
(https://help.github.com/articles/using-pull-requests)


Run it with proper deployment
=============================

Use your preferred web server setup to expose your website. For example, nginx
proxy passing to the python script, which itself can be run using supervisord.

You should install nginx with a sites-available folder and a sites-enabled 
folder. There is an example default nginx config in the deploy folder of the 
portality repo. Copy or symlink it into the sites-available folder of nginx, 
then symlink that in sites-enabled and restart nginx.

cd /etc/nginx/sites-available

sudo ln -s /opt/portality/src/portality/deploy/portality_nginx_config portality

cd ../sites-enabled

sudo ln -s ../sites-available/portality portality

sudo /etc/init.d/nginx restart


Now nginx will proxy-pass to your app, so you just need to have your app 
running. If you did the pip install gunicorn in the virtualenv install above, 
then you can do this using the supervisord config if you like (or your own 
preference).

sudo apt-get install supervisor

cd /etc/supervisor/conf.d

sudo ln -s /opt/portality/src/portality/deploy/portality_supervisord_config

sudo supervisorctl reread

sudo supervisorctl update


Auto-deployment and backups
===========================

And coming soon a default view that acts as a git webhook to auto-deploy.

And perhaps some built-in backup.






