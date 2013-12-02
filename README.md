#The Directory of Open Access Journals (DOAJ)

This repository provides the software which drives the DOAJ website and the DOAJ directory.

## Setting up the software

### Elasticsearch
Elasticsearch is the datastore we use.

Install elasticsearch as per [its documentation](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/setup.html#setup-installation).

You can check whether its running by pointing your browser to [http://localhost:9200](http://localhost:9200) - you should see a basic JSON response telling you what version you're running.

### The DOAJ Python app

Install Python 2.7 . Not tested with Python 3.x . Python 2.6.x usable, but you will need to use the [drop-in OrderedDict replacement](https://pypi.python.org/pypi/ordereddict).

Install pip using [pip's very robust instructions](http://www.pip-installer.org/en/latest/installing.html).
    
    pip install virtualenv  # won't upgrade it if you already have it. pip install -- upgrade virtualenv for that.
    virtualenv -p <path/to/python 2.7 executable> doajenv
    cd doajenv
    . bin/activate
    mkdir src
    cd src
    git clone https://github.com/DOAJ/doaj.git  # SSH URL: git@github.com:DOAJ/doaj.git
    cd doaj
    git submodule init
    git submodule update
    python portality/app.py  # the output of this will tell you which port it's running on and whether it's in debug mode
    

## Journal Data Model

    {
        "id" : "<some opaque identifier>",
        "bibjson" : {
            "title" : "The title of the journal",
            "alternative_title" : "An alternative title for the journal",
            "identifier": [
                {"type" : "pissn", "id" : "<print issn>"},
                {"type" : "eissn", "id" : "<electronic issn>"},
            ],
            "keywords" : [<list of free-text keywords>],
            "language" : ["The language of the journal"],
            "author_pays_url" : "<charging link>",
            "author_pays" : true|false,
            "country" : "<country of journal publication>",
            "license" : [
                {
                    "title" : "<name of licence>",
                    "type" : "<type>", 
                    "url" : "<url>", 
                    "version" : "<version>",
                    "open_access": true|false,
                }
            ],
            "publisher" : "<publisher>",
            "link": [{"url" : "<url>"}],
            "oa_start" : {
                "year" : "<year>", 
                "volume" : "<volume>", 
                "number" : "<issue number>"
            },
            "oa_end" : {
                "year" : "<year>", 
                "volume" : "<volume>", 
                "number" : "<issue number>"
            },
            "provider" : "<journal provider if different from publisher>",
            "active" : true|false
            "for_free" : true|false
            "subject" : [
                {
                    "scheme" : "<scheme>", 
                    "term" : "<term>"
                }
            ]
        },
        "history" : [
            {
                "date" : "<date history object created>",
                "replaces" : [<list of p/e-issns this record immediately supersedes than>],
                "isreplacedby" : [<list of p/e-issns that this record is immediately superseded by>]
                "bibjson" : { <snapshot of historic bibjson record> }
            }
        ]
        "suggestion" : {
            "description" : "description of the journal's activities",
            "suggester" : { 
                "name" : "name of person suggesting journal",
                "email" : "email of person suggesting journal"
            },
            "suggested_by_owner" : true|false,
            "suggested_on" : "<date of suggestion>"
        },
        "admin" : {
            "in_doaj" : true|false,
            "application_status" : "state of journal application",
            notes : [
                {
                    "note" : "<note>", 
                    "date" : "<date>"
                }
            ],
            owner_correspondence : [
                {
                    "note" : "<note>", 
                    "date" : "<date>"
                }
            ],
            "contact" : [
                { 
                    "email" : "<email of journal contact>",
                    "name" : "<name of journal contact>"
                }
            ]
        },
        "index" : {
            "issn" : [<list of all print and electronic issns for all time>],
            "title" : [<list of all titles the journal has been known by>],
            "subjects" : [<all possible subject keywords>],
            "schema_subjects" : [<all subject keywords with schema prefixes>]
        },
        "created_date" : "<date created>",
        "last_updated" : "<date record last modified>"
    }

### A Note on the History

The objective of the "history" section of the record is to record old versions of the bibliographic metadata.  This is not to say, a version history of the record, but actual snapshots of data that was accurate at the time it was created, but which has changed.  So, erroneous metadata should still not be present in the history records, and it should be possible to amend history records if errors are found.  Repeat: it is not like version control, it is a legitimate historic record.

It is likely that history records will only be created upon request by the administrator.

This applies to the Article Data Model too

## Article Data Model

    {
        "id" : "<some opaque identifier>",
        "bibjson" : {
            "title" : "<title of the article>",
            "identifier": [
                {"type" : "doi", "id" : "<doi>", "url" : "<doi url>"},
                {"type" : "pissn", "id" : "<print issn>"},
                {"type" : "eissn", "id" : "<electronic issn>"}
            ],
            "journal" : {
                "volume" : "journal volume number",
                "number" : "journal issue number",
                "publisher" : "<publisher>"
            },
            "year" : "<year of publication>",
            "month" : "<month of publicaiton>",
            "start_page" : "<start page>",
            "end_page" : "<end page>",
            "link" : [
                {
                    "url" : "<fulltext url>",
                    "type" : "fulltext"
                }
            ],
            "abstract" : "<the abstract>",
            "author" : [
                {"name" : "<author name>"},
            ],
            "keywords" : [<list of free text keywords>]
        },
        "history" : [
            {
                "date" : "<date history record created>",
                "bibjson" : { <historic bibjson record> }
            }
        ]
        "index" : {
            "date" : "<date of publication>"
            "issn" : [<list of all issns that this item pertains to>],
        },
        "created" : "<date created>",
        "last_modified" : "<date record last modified>"
    }





























