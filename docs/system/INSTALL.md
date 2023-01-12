# Setting up DOAJ

[comment] <>: (~~Install:Documentation~~)

This installation instruction is for Ubuntu 16.04 and Ubuntu 18.04 users. We recommend running our application on Ubuntu OS.

## Java

[comment] <>: (~~->Java:Technology~~)

Java is required to natively run Elasticsearch, if you're running ES directly from the archive (rather than using `apt`) you'll need a JRE such as:

    sudo apt install openjdk-11-jre

## Elasticsearch

[comment] <>: (~~->Elasticsearch:Technology~~)

Elasticsearch is the datastore we use. Currently we use version 7.10.2 OSS in production, but you'll find OpenSearch might work too.

You can download .deb package from [here](https://www.elastic.co/downloads/past-releases/elasticsearch-7-10-2) and install it with:

    sudo dpkg -i <path-to-es-deb-package>

Alternatively, you can download and extract the `tar` or `zip` archive and run the elasticsearch executable directly - this makes it easier to have multiple versions available to use in different projects.

    cd <directory-you extracted-elasticsearch>
    ./bin/elasticsearch

Elasticsearch documentation can be found [here](https://www.elastic.co/guide/en/elasticsearch/reference/7.10/setup.html#setup-installation).

You can check whether its running via `curl localhost:9200` by pointing your browser to [http://localhost:9200](http://localhost:9200) - you should see a basic JSON response telling you what version you're running.

## Redis

[comment] <>: (~~->Redis:Technology~~)

For background tasks, we use `redis`. Run this however you like, just make sure the correct port is configured in app settings and is accessible to the app. E.g. to install in Ubuntu:

    sudo apt install redis-server
    # Start redis service
    service redis start
    # Check redis is running and enabled
    systemctl status redis

# Python and Pip

[comment] <>: (~~->Python:Technology~~)

Install Python 3.7 or more recent. Python 2.x is not supported anymore. You can verify if correct version of python is in use by typing:

    python --version

Install pip using:

    sudo apt install python3-pip

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

    # Create a virtualenv for python 3.7 then activate it (also use this to run scripts etc)
    virtualenv -p python3.7 doajenv
    cd doajenv
    . bin/activate

    # Clone the DOAJ codebase
    mkdir src && cd src
    git clone https://github.com/DOAJ/doaj.git  # SSH URL: git@github.com:DOAJ/doaj.git
    cd doaj

    # Install the submodules then the dependencies
    git submodule update --init --recursive
    pip install -e .

    # If you are running in development, get the extra dependencies to run the tests
    pip install -e .[test]
    # Or the documentation generation libraries:
    pip install -e .[docs]

    # Finally, run the app. You should see it in a browser
    DOAJENV=dev python portality/app.py  # the output of this will tell you which port it's running on and whether it's in debug mode

## Scheduled tasks

[comment] <>: (~~->Huey:Technology~~)

The following tasks are run periodically via `huey` (see the app settings to configure).  If you wish to run them directly
the following scripts can be used.

### Generate the Journal CSV.

If you wish to run this task manually you can use the script:

    portality/scripts/journalcsv.py

This will generate the latest version of the csv to serve on request.

[comment] <>: (~~->JournalCSV:Script~~)

### Generate the Sitemap

    portality/scripts/sitemap.py

This will generate the latest version of the sitemap to serve on request.

[comment] <>: (~~->Sitemap:Script~~)

### Import News Items

    portality/scripts/news.py

This will import the latest news from the DOAJ wordpress blog.

[comment] <>: (~~->News:Script~~)
