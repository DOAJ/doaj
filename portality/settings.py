import os

# ========================
# MAIN SETTINGS

# base path, to the directory where this settings file lives
BASE_FILE_PATH = os.path.dirname(os.path.realpath(__file__))

# make this something secret in your overriding app.cfg
SECRET_KEY = "default-key"

# contact info
ADMIN_NAME = "DOAJ"
ADMIN_EMAIL = "emanuil@cottagelabs.com"
ADMINS = ["emanuil@cottagelabs.com", "mark@cottagelabs.com"]
SUPPRESS_ERROR_EMAILS = False  # should be set to False in production and True in staging

# service info
SERVICE_NAME = "Directory of Open Access Journals"
SERVICE_TAGLINE = ""
HOST = "0.0.0.0"
DEBUG = True
PORT = 5004
SSL = True

# elasticsearch settings
ELASTIC_SEARCH_HOST = "http://localhost:9200" # remember the http:// or https://
#ELASTIC_SEARCH_HOST = "http://93.93.131.168:9200"
ELASTIC_SEARCH_DB = "doaj"
INITIALISE_INDEX = True # whether or not to try creating the index and required index types on startup

# can anonymous users get raw JSON records via the query endpoint?
PUBLIC_ACCESSIBLE_JSON = True 

# =======================
# email settings

SMTP_SERVER = "smtp.mandrillapp.com"

SMTP_PORT = 587

# ========================
# user login settings

# amount of time a reset token is valid for (86400 is 24 hours)
PASSWORD_RESET_TIMEOUT = 86400

# ========================
# authorisation settings

# Can people register publicly? If false, only the superuser can create new accounts
# PUBLIC_REGISTER = False

SUPER_USER_ROLE = "admin"

# FIXME: something like this required for hierarchical roles, but not yet needed
#ROLE_MAP = {
#    "admin" : {"publisher", "create_user"}
#}

# ========================
# MAPPING SETTINGS

# a dict of the ES mappings. identify by name, and include name as first object name
# and identifier for how non-analyzed fields for faceting are differentiated in the mappings
FACET_FIELD = ".exact"
MAPPINGS = {
    "journal" : {
        "journal" : {
            "dynamic_templates" : [
                {
                    "default" : {
                        "match" : "*",
                        "match_mapping_type": "string",
                        "mapping" : {
                            "type" : "multi_field",
                            "fields" : {
                                "{name}" : {"type" : "{dynamic_type}", "index" : "analyzed", "store" : "no"},
                                "exact" : {"type" : "{dynamic_type}", "index" : "not_analyzed", "store" : "yes"}
                            }
                        }
                    }
                }
            ]
        }
    }
}
MAPPINGS['account'] = {'account':MAPPINGS['journal']['journal']}
MAPPINGS['article'] = {'article':MAPPINGS['journal']['journal']}
MAPPINGS['suggestion'] = {'suggestion':MAPPINGS['journal']['journal']}
MAPPINGS['upload'] = {'upload':MAPPINGS['journal']['journal']}
MAPPINGS['cache'] = {'cache':MAPPINGS['journal']['journal']}


# ========================
# QUERY SETTINGS

# list index types that should not be queryable via the query endpoint
NO_QUERY = []
SU_ONLY = ["account"]

# list additional terms to impose on anonymous users of query endpoint
# for each index type that you wish to have some
# must be a list of objects that can be appended to an ES query.bool.must
# for example [{'term':{'visible':True}},{'term':{'accessible':True}}]
ANONYMOUS_SEARCH_TERMS = {
    # "pages": [{'term':{'visible':True}},{'term':{'accessible':True}}]
}

# a default sort to apply to query endpoint searches
# for each index type that you wish to have one
# for example {'created_date' + FACET_FIELD : {"order":"desc"}}
DEFAULT_SORT = {
    # "pages": {'created_date' + FACET_FIELD : {"order":"desc"}}
}

QUERY_ROUTE = {
    "query" : {"role": None, "default_filter": True},
    "admin_query" : {"role" : "admin", "default_filter": False},
    "publisher_query" : {"role" : "publisher", "default_filter" : False, "owner_filter" : True}
}

# ========================
# MEDIA SETTINGS

# location of media storage folder
MEDIA_FOLDER = "media"


# ========================
# PAGEMANAGER SETTINGS

# folder name for storing page content
# will be added under the templates/pagemanager route
CONTENT_FOLDER = "content"

# etherpad endpoint if available for collaborative editing
COLLABORATIVE = 'http://localhost:9001'

# when a page is deleted from the index should it also be removed from 
# filesystem and etherpad (if they are available in the first place)
DELETE_REMOVES_FS = False # True / False
DELETE_REMOVES_EP = False # MUST BE THE ETHERPAD API-KEY OR DELETES WILL FAIL

# disqus account shortname if available for page comments
COMMENTS = ''


# ========================
# HOOK SETTINGS

REPOS = {
    "portality": {
        "path": "/opt/portality/src/portality"
    },
    "content": {
        "path": "/opt/portality/src/portality/portality/templates/pagemanager/content"
    }
}

# ========================
# FEED SETTINGS

FEED_TITLE = "Directory of Open Access Journals"

BASE_URL = "http://doaj.org"

# Maximum number of feed entries to be given in a single response.  If this is omitted, it will
# default to 20
MAX_FEED_ENTRIES = 100

# Maximum age of feed entries (in seconds) (default value here is 30 days).
MAX_FEED_ENTRY_AGE = 2592000

# NOT USED IN THIS IMPLEMENTATION
# Which index to run feeds from
#FEED_INDEX = "journal"

# Licensing terms for feed content
FEED_LICENCE = "(c) DOAJ 2013. CC-BY-SA."

# name of the feed generator (goes in the atom:generator element)
FEED_GENERATOR = "CottageLabs feed generator"

# Larger image to use as the logo for all of the feeds
FEED_LOGO = "http://www.doaj.org/static/doaj/images/favicon.ico"


# ============================
# OAI-PMH SETTINGS

OAIPMH_METADATA_FORMATS = [
    {
        "metadataPrefix" : "oai_dc",
        "schema" : "http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
        "metadataNamespace" : "http://www.openarchives.org/OAI/2.0/oai_dc/"
    }
]

OAIPMH_IDENTIFIER_NAMESPACE = "doaj.org"

OAIPMH_LIST_RECORDS_PAGE_SIZE = 100

OAIPMH_LIST_IDENTIFIERS_PAGE_SIZE = 300

OAIPMH_RESUMPTION_TOKEN_EXPIRY = 86400


# =================================
# File Upload and crosswalk settings

# directory to upload files to.  MUST be full absolute path
# The default takes the directory above this, and then down in to "upload"
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "upload")

# paths to schema files to validate incoming documents against for the various
# crosswalks available

SCHEMAS = {
    "doaj" : os.path.join(BASE_FILE_PATH, "static", "doaj", "doajArticles.xsd")
}

# =================================
# ReCaptcha settings
# We use per-domain, not global keys
RECAPTCHA_PUBLIC_KEY = '6LdaE-wSAAAAAKTofjeh5Zn94LN1zxzbrhxE8Zxr'
# RECAPTCHA_PRIVATE_KEY is set in secret_settings.py which should not be
# committed to the repository, but only held locally and on the server
# (transfer using scp).


# =================================
# Cache settings

# number of seconds site statistics should be considered fresh
# 1800s = 30mins
SITE_STATISTICS_TIMEOUT = 1800

# directory into which to put files which are cached (e.g. the csv)
CACHE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "cache")

