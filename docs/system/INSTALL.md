# Setting up the software

This installation instruction is for Ubuntu 16.04 and Ubuntu 18.04 users. We recommend running our application on Ubuntu OS.

## Java 8

Java 8 is required to install correct version of Elasticsearch. On ubuntu it can be download from apt:

    sudo apt-get install openjdk-8-jre

## Elasticsearch
Elasticsearch is the datastore we use. Currently we require version 1.7.

You can download .deb package from [here](https://www.elastic.co/downloads/past-releases/elasticsearch-1-7-0https://www.elastic.co/downloads/past-releases/elasticsearch-1-7-0) and install it by:

    sudo apt install ./path-to-es-deb-package

Elasticsearch documentation can be found [here](https://www.elastic.co/guide/en/elasticsearch/reference/1.7/setup.html#setup-installation).

You can check whether its running by pointing your browser to [http://localhost:9200](http://localhost:9200) - you should see a basic JSON response telling you what version you're running.

## Redis

For background tasks, we use `redis`. Run this however you like, just make sure the correct port is configured in app settings and is accessible to the app. E.g. to install in Ubuntu:

    sudo apt install redis-server
    # Start redis service
    service redis start
    # Check redis is running and enabled
    systemctl status redis

#Python and Pip

Install Python 2.7 or more recent . Not tested with Python 3.x. You can verify if correct version of python is in use by typing:
     
    python --version

Install pip using:

    sudo apt install python-pip
  
## The DOAJ app
  
    
    sudo pip install virtualenv  # won't upgrade it if you already have it. pip install -- upgrade virtualenv for that.
    virtualenv -p python2.7 doajenv
    cd doajenv
    . bin/activate
    mkdir src
    cd src
    git clone https://github.com/DOAJ/doaj.git  # SSH URL: git@github.com:DOAJ/doaj.git
    cd doaj
    git submodule update --init --recursive
    git submodule update --recursive
    sudo apt-get install libxml2-dev libxslt-dev python-dev lib32z1-dev # install LXML dependencies on Linux. Windows users: grab a precompiled LXML from http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml (go for version 3.x) - make sure the virtual environment can see it!
    pip install -r requirements.txt  # install all the app's dependencies
    DOAJENV=dev python portality/app.py  # the output of this will tell you which port it's running on and whether it's in debug mode

## Scheduled tasks

The following tasks need to run periodically via `huey`:

    portality/scripts/ingestarticles.py

This will ingest all of the latest file uploads and remote URLs provided.  It should be run approximately every hour.

    portality/scripts/journalcsv.py

This will generate the latest version of the csv to serve on request.  It should be run approximately every 30 minutes.

    portality/scripts/toc.py

This will re-generate all of the Table of Contents pages for performance purposes.  This script can take a long time to run (several hours) so should only be run daily at the most.

    portality/scripts/sitemap.py

This will generate the latest version of the sitemap to serve on request.  It should be run approximately every 30 minutes.

    portality/scripts/news.py

This will import the latest news from the DOAJ wordpress blog.  It should be run daily.

todo: more tasks
