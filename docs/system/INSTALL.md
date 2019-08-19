# Setting up the software

This installation instruction is for Ubuntu 16.04 and Ubuntu 18.04 users. We recommend running our application on Ubuntu OS.

## Java 8

Java 8 is required to install correct version of Elasticsearch. On ubuntu it can be download from apt:

    sudo apt install openjdk-8-jre

## Elasticsearch
Elasticsearch is the datastore we use. Currently we require version 1.7.

You can download .deb package from [here](https://www.elastic.co/downloads/past-releases/elasticsearch-1-7-0https://www.elastic.co/downloads/past-releases/elasticsearch-1-7-0) and install it by:

    sudo apt install <path-to-es-deb-package>

Alternatively, you can download and extract the `tar` or `zip` archive and run the elasticsearch executable directly - this makes it easier to have multiple versions available to use in different projects.

    cd <directory-you extracted-elasticsearch>
    ./bin/elasticsearch

Elasticsearch documentation can be found [here](https://www.elastic.co/guide/en/elasticsearch/reference/1.7/setup.html#setup-installation).

You can check whether its running via `curl localhost:9200` by pointing your browser to [http://localhost:9200](http://localhost:9200) - you should see a basic JSON response telling you what version you're running.

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

You can upgrade a package with

    pip install --upgrade <package>

## Developer tools

For development, it's useful to have `git`, `wget`, and `curl` installed. If you don't have them already, all can be retrieved via apt:

    sudo apt install git wget curl

## virtualenv

It's recommended to run the DOAJ inside a python virtual environment so it doesn't interfere with your system python packages. This can be installed via `pip` or apt:

    sudo apt install python-virtualenv
    # OR
    sudo pip install virtualenv

## The DOAJ app

    # system dependencies
    sudo apt install libxml2-dev libxslt-dev python-dev lib32z1-dev

    # Create a virtualenv for python 2.7 then activate it (also use this to run scripts etc)
    virtualenv -p python2.7 doajenv
    cd doajenv
    . bin/activate

    # Clone the DOAJ codebase
    mkdir src && cd src
    git clone https://github.com/DOAJ/doaj.git  # SSH URL: git@github.com:DOAJ/doaj.git
    cd doaj

    # Install the submodules then the dependencies
    git submodule update --init --recursive
    pip install -r requirements.txt

    # Finally, run the app. You should see it in a browser
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
