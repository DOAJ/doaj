#The Directory of Open Access Journals (DOAJ)

This repository provides the software which drives the DOAJ website and the DOAJ directory.

## Deployment
We're running supervisord on our server. Every time you push changes, do
    
    git pull  # or git clone https://github.com/DOAJ/doaj.git if deploying for the first time
    git submodule init  # if this is the first time you're deploying the app, but won't hurt if it's not
    git submodule update  # in case one of the repo's submodules are at a newer commit now
    sudo supervisorctl restart doaj

## Setting up the software

### Elasticsearch
Elasticsearch is the datastore we use.

Install elasticsearch as per [its documentation](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/setup.html#setup-installation).

You can check whether its running by pointing your browser to [http://localhost:9200](http://localhost:9200) - you should see a basic JSON response telling you what version you're running.

### The DOAJ Python app

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
    git submodule init
    git submodule update
    sudo apt-get install libxml2-dev libxslt-dev  # install LXML dependencies on Linux. Windows users: grab a precompiled LXML from http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml (go for version 3.x) - make sure the virtual environment can see it!
    pip install -e .  # install all the app's dependencies
    python portality/app.py  # the output of this will tell you which port it's running on and whether it's in debug mode
    
## Data Models

Notes on the data model

* All dates are provided in ISO 8601, which are of the form yyyy-mm-ddTHH:MM:SSZ

The objective of the "history" section of the records is to record old versions of the bibliographic metadata.  This is not to say, a version history of the record, but actual snapshots of data that was accurate at the time it was created, but which has changed.  So, erroneous metadata should still not be present in the history records, and it should be possible to amend history records if errors are found.  Repeat: it is not like version control, it is a legitimate historic record.

It is likely that history records will only be created upon request by the administrator.

### Journal Data Model

```json
{
    "id" : "<some opaque identifier>",
    "bibjson" : {
        "active" : true|false,
        "title" : "The title of the journal",
        "alternative_title" : "An alternative title for the journal",
        "identifier": [
            {"type" : "pissn", "id" : "<print issn>"},
            {"type" : "eissn", "id" : "<electronic issn>"},
        ],
        "keywords" : [<list of free-text keywords>],
        "language" : ["The language of the journal"],
        "country" : "<country of journal publication>",
        "publisher" : "<publisher>",
        "provider" : "<service provider or platform used for journal>",
        "institution" : "<society or institution responsible for journal>",
        "link": [
            {"type" : "homepage", "url" : "<url>"},
            {"type" : "waiver_policy", "url" : "<url>"},
            {"type" : "editorial_board", "url" : "<url>"},
            {"type" : "aims_scope", "url" : "<url>"},
            {"type" : "author_instructions", "url" : "<url>"},
            {"type" : "oa_statement", "url" : "<url>"}
        ],
        "subject" : [
            {
                "scheme" : "<scheme>", 
                "term" : "<term>"
            }
        ],
        
        "oa_start" : {
            "year" : "<year>", 
            "volume" : "<volume>", # Deprecated - may be removed
            "number" : "<issue number>" # Deprecated - may be removed
        },
        "oa_end" : {
            "year" : "<year>", 
            "volume" : "<volume>", # Deprecated - may be removed
            "number" : "<issue number>" # Deprecated - may be removed
        },
        "apc" : {
            "currency" : "<currency code>",
            "average_price" : "<average price of APC>"
        },
        "submission_charges" : {
            "currency" : "<currency code>",
            "average_price" : "<average price of submission charge>"
        },
        "archiving_policy" : {
            "policy" : ["<policy type (e.g. LOCKSS)>"]
            "url" : "<url to policy information page>"
        },
        "editorial_review" : {
            "process" : "<type of editorial review process>",
            "url" : "<url to info about editorial review process>"
        },
        "plagiarism_detection" : {
            "detection": true|false, # is there plagiarism detection
            "url" : "<url to info about plagiarism detection>"
        },
        "article_statistics" : {
            "statistics" : true|false
            "url" : "<url for info about article statistics>"
        },
        "deposit_policy" : ["<policy type (e.g. Sherpa/Romeo)>"],
        "author_copyright" : {
            "from" : "<year statement is valid from>",
            "copyright" : true|false
        },
        "author_publishing_rights" : {
            "from" : "<year statement is valid from>",
            "publishing_rights" : true|false
        }
        "allows_fulltext_indexing" : true|false,
        "persistent_identifier_schemes" : [<list of names of pid schemes>],
        "article_statistics" : true|false, # does the journal provide download statistics
        "format" : [<list of mimetypes of fulltext formats available>]
        "publication_time" : "<average time in weeks to publication>"
        "license" : [
            {
                "title" : "<name of licence>",
                "type" : "<type>", 
                "url" : "<url>", 
                "version" : "<version>",
                "open_access": true|false, # is the licence BOAI compliant
                "embedded" : true|false # is the licence metadata embedded in the article pages>
            }
        ],
        
        # Require migration to "apc"
        "author_pays_url" : "<charging link>",
        "author_pays" : true|false
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
        "suggester" : { 
            "name" : "name of person suggesting journal",
            "email" : "email of person suggesting journal"
        },
        "suggested_on" : "<date of suggestion>",
        "articles_last_year" : {
            "count" : "<number of articles published last year>",
            "url" : "<link to proof of above number>"
        },
        "article_metadata" : true|false
        
        # Deprecated - may be removed
        "description" : "description of the journal's activities",
        "suggested_by_owner" : true|false,
    },
    "admin" : {
        "in_doaj" : true|false,
        "application_status" : "state of journal application",
        "notes" : [
            {
                "note" : "<note>", 
                "date" : "<date>"
            }
        ],
        "owner_correspondence" : [
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
        "subject" : [<all possible subject keywords>],
        "schema_subject" : [<all subject keywords with schema prefixes>],
        "classification" : [<list of classification terms without prefixes>],
        "language" : [<list of languages of the journal>],
        "country" : "<country of journal publication>",
        "license" : [<list of titles of licences>],
        "publisher" : "<publisher>",
        "homepage_url" : "<homepage url>",
        "waiver_policy_url" : "<waiver policy url>",
        "editorial_board_url" : "<editorial board url>",
        "aims_scope_url" : "<aims and scope url>",
        "author_instructions_url" : "<author instructions url>",
        "oa_statement_url" : "<OA statment url>"
    },
    "created_date" : "<date created>",
    "last_updated" : "<date record last modified>"
}
```

### Article Data Model

```json
{
    "id" : "<some opaque identifier>",
    "admin" : {
        "in_doaj" : true|false
    },
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
            "publisher" : "<publisher>",
            "title" : "<journal title (taken from journal record)>"
            "license" : [
                {
                    "title" : "<name of licence>",
                    "type" : "<type>", 
                    "url" : "<url>", 
                    "version" : "<version>",
                    "open_access": true|false,
                }
            ],
            "language" : "<language of journal as a whole>",
            "country" : "<country of publication>"
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
        "keywords" : [<list of free text keywords>],
        "subject" : [
            {
                "scheme" : "<subject scheme>",
                "term" : "<subject term>"
            }
        ]
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
        "subject" : [<all possible subject keywords>],
        "schema_subject" : [<all subject keywords with schema prefixes>],
        "classification" : [<list of classification terms without prefixes>],
        "language" : [<list of languages of the journal>],
        "country" : "<country of journal publication>",
        "license" : [<list of titles of licences>],
        "publisher" : "<publisher>"
    },
    "created" : "<date created>",
    "last_modified" : "<date record last modified>"
}
```

NOTE: there's an argument for putting the issn identifiers inside the journal part of the bibjson, rather than at the root of the bibliographic record, but this creates some annoying complexities in the software implementation and its API for interacting with identifiers, so it has not yet been done.  Sould it be?  The same goes for the subject, which currently comes from the journal record, but which can effectively be applied the the article too.

### Contact Data Model

NOTE: this is just for the purposes of holding them over until the new year.  We should actually have each document
assert the user(s) they can be administered by

    {
        "id" : "<the username of the user>",
        "password" : "<hashed password>",
        "name" : "<user's actual name>",
        "email" : "<user's email address>",
        "journal" : [<list of journal ids the user can administer>]
    }


## Authentication and Authorisation System

### Creating a new user

To create a new user for the DOAJ use the createuser.py script in the first instance:

    python portality/scripts/createuser.py -u username -r admin -p password -e email

This will create a new user with the "admin" role.

If you want to update the user account at any point via the command line, use the same command again.  Any user that already exists and is identified by the argument to the -u option will be modified/overwritten

To edit the user via the web interface, login to the DOAJ application and go to

    /account/<username>

Once you have created the initial administrator, new users can be created when logged in as that administrator via:

    /account/register

### Role-based authorisation

The DOAJ user area uses role-based authorisation.

When implementing a feature, that feature should be given a role name.

For example, if implementing a "Create new Administrator" feature, a new role should be defined with the name "create_administrator".  Any actions which pertain to the creation of a new administrator should be authorised with a call to the current user's has_role method:

    if current_user.has_role("create_administrator"):
        # do some create administrator stuff
    else:
        # unauthorised

There are two high-level roles which the DOAJ implements

* admin - for the DOAJ administrators, who will have complete super-user priviledges
* publisher - for publisher users of the DOAJ, who will be administering their own content

At this early stage of development, user accounts will only need to be assigned one of those roles.  The "admin" role is a super user so any calls to has_role for any role on an administrator's user object will result in success (i.e. has_role("create_administrator") on a user with role "admin" will return True).

At a later stage, and when it becomes necessary, we will implement mappings of the high level roles to more granular roles.


### Authentication

When developing authenticated areas of the DOAJ site, there are two things you should do.

The blueprint should have a "before_request" method which rejects anonymous users or users who do not have the correct role.  For example:

    # restrict everything in admin to logged in users with the "publsiher" role
    @blueprint.before_request
    def restrict():
        if current_user.is_anonymous() or not current_user.has_role("publisher"):
            abort(401)

The restricted method should be annotated with flask.ext.login's login_required:

    from flask.ext.login import login_required
    
    @blueprint.route("/")
    @login_required
    def index():
        # some restricted method



























