# Setting up the software

## Elasticsearch
Elasticsearch is the datastore we use.

Install elasticsearch as per [its documentation](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/setup.html#setup-installation).

You can check whether its running by pointing your browser to [http://localhost:9200](http://localhost:9200) - you should see a basic JSON response telling you what version you're running.

## Redis

We use a dockerised Redis installation. Currently this is only used for Huey background job processing tasks, so you don't need to run it unless you're going to run background jobs.

  1. Install Docker [by following step 1 of the Docker Compose installation tutorial](https://docs.docker.com/compose/install/) on your machine.

  2. Make sure you don't need to `sudo` to run docker.
  
    sudo groupadd docker
    sudo gpasswd -a ${USER} docker
    newgrp docker

  3. Install [Docker Compose by following steps 2 and onwards from the Docker Compose installation Tutorial](https://docs.docker.com/compose/install/).

    Ubuntu Linux users, the command that Docker-Compose provides you with will not work since /usr/local/bin is not writeable by anybody but root in default Ubuntu setups. Use `sudo tee` instead, e.g.:

    ```
    curl -L https://github.com/docker/compose/releases/download/[INSERT_DESIRED_DOCKER_COMPOSE_VERSION_HERE]/docker-compose-`uname -s`-`uname -m` | sudo tee /usr/local/bin/docker-compose > /dev/null && sudo chmod a+x /usr/local/bin/docker-compose
    ```

  4. Open a console and try running `docker -h` and `docker-compose -h` to verify they are both accessible.
  
From this point on, simply `cd docker/` and `docker-compose up`.

If you find yourself developing the Docker setup itself, just run `docker-compose build && docker-compose up`.

## The DOAJ Python app

Install Python 2.6.6 or more recent . Not tested with Python 3.x .

Install pip using [pip's very robust instructions](http://www.pip-installer.org/en/latest/installing.html).
    
    sudo pip install virtualenv  # won't upgrade it if you already have it. pip install -- upgrade virtualenv for that.
    virtualenv -p <path/to/python 2.7 executable> doajenv
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
    python portality/app.py  # the output of this will tell you which port it's running on and whether it's in debug mode

## Cron Jobs

The following tasks need to run periodically:

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
