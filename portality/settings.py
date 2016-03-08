import os

# Use these options to place the application into READ ONLY mode

# This puts the UI into READ_ONLY mode
READ_ONLY_MODE = False

# This puts the cron jobs into READ_ONLY mode
SCRIPTS_READ_ONLY_MODE = False

DOAJ_VERSION = "2.10.9"

OFFLINE_MODE = False

# List the features we want to be active
FEATURES = []
VALID_FEATURES = ['api']

# ========================
# MAIN SETTINGS

# base path, to the directory where this settings file lives
BASE_FILE_PATH = os.path.dirname(os.path.realpath(__file__))

BASE_URL = "https://doaj.org"
API_BLUEPRINT_NAME = "api_v1"  # change if upgrading API to new version and creating new view for that

# make this something secret in your overriding app.cfg
SECRET_KEY = "default-key"

# contact info
ADMIN_NAME = "DOAJ"
ADMIN_EMAIL = "sysadmin@cottagelabs.com"
ADMINS = ["emanuil@cottagelabs.com", "mark@cottagelabs.com"]
ERROR_LOGGING_EMAIL = 'doaj.internal@gmail.com'
SUPPRESS_ERROR_EMAILS = False
SYSTEM_EMAIL_FROM = 'feedback@doaj.org'
CC_ALL_EMAILS_TO = SYSTEM_EMAIL_FROM  # DOAJ may get a dedicated inbox in the future
ENABLE_EMAIL = True
ENABLE_PUBLISHER_EMAIL = True
MANAGING_EDITOR_EMAIL = "managing-editors@doaj.org"

# service info
SERVICE_NAME = "Directory of Open Access Journals"
SERVICE_TAGLINE = "DOAJ is an online directory that indexes and provides access to quality open access, peer-reviewed journals."
HOST = "0.0.0.0"
DEBUG = False
PORT = 5004
SSL = True
VALID_ENVIRONMENTS = ['dev', 'test', 'staging', 'production', 'harvester']

# elasticsearch settings
ELASTIC_SEARCH_HOST = "http://localhost:9200" # remember the http:// or https://
ELASTIC_SEARCH_DB = "doaj"
ELASTIC_SEARCH_TEST_DB = "doajtest"
INITIALISE_INDEX = True # whether or not to try creating the index and required index types on startup

# PyCharm debug settings
DEBUG_PYCHARM = False  # do not try to connect to the PyCharm debugger by default
DEBUG_PYCHARM_SERVER = 'localhost'
DEBUG_PYCHARM_PORT = 6000

# can anonymous users get raw JSON records via the query endpoint?
PUBLIC_ACCESSIBLE_JSON = True 

# =======================
# email settings

# Settings for Flask-Mail. Set in app.cfg
MAIL_SERVER = None          # default localhost
MAIL_PORT = 25              # default 25
#MAIL_USE_TLS               # default False
#MAIL_USE_SSL               # default False
#MAIL_DEBUG                 # default app.debug
#MAIL_USERNAME              # default None
#MAIL_PASSWORD              # default None
#MAIL_DEFAULT_SENDER        # default None
#MAIL_MAX_EMAILS            # default None
#MAIL_SUPPRESS_SEND         # default app.testing

# ========================
# workflow email notification settings
MAN_ED_IDLE_WEEKS = 4      # weeks before an application is considered reminder-worthy
ED_IDLE_WEEKS = 3           # weeks before the editor is warned about idle applications in their group
ASSOC_ED_IDLE_DAYS = 10
ASSOC_ED_IDLE_WEEKS = 3

# Which statuses the notification queries should be filtered to show
MAN_ED_NOTIFICATION_STATUSES = ['submitted', 'pending', 'in progress', 'completed', 'on hold']
ED_NOTIFICATION_STATUSES = ['submitted', 'pending', 'in progress', 'completed']
ASSOC_ED_NOTIFICATION_STATUSES = ['submitted', 'pending', 'in progress']

# ========================
# user login settings

# amount of time a reset token is valid for (86400 is 24 hours)
PASSWORD_RESET_TIMEOUT = 86400
# amount of time a reset token for a new account is valid for
PASSWORD_CREATE_TIMEOUT = PASSWORD_RESET_TIMEOUT * 14

# ========================
# publisher settings

# the earliest date accepted on the publisher's 'enter article metadata' form.
# code will default to 15 years before current year if commented out.
METADATA_START_YEAR = 1960

# tick (on toc) and doaj seal settings
TICK_THRESHOLD = '2014-03-19T00:00:00Z'

# ========================
# authorisation settings

# Can people register publicly? If false, only the superuser can create new accounts
# PUBLIC_REGISTER = False

SUPER_USER_ROLE = "admin"

#"api" top-level role is added to all acounts on creation; it can be revoked per account by removal of the role.
TOP_LEVEL_ROLES = ["admin", "publisher", "editor", "associate_editor", "api"]

ROLE_MAP = {
    "editor": [
        "associate_editor",     # note, these don't cascade, so we still need to list all the low-level roles
        "edit_journal",
        "edit_suggestion",
        "editor_area",
        "assign_to_associate",
        "list_group_journals",
        "list_group_suggestions",
    ],
    "associate_editor": [
        "edit_journal",
        "edit_suggestion",
        "editor_area",
    ]
}

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
MAPPINGS['toc'] = {'toc':MAPPINGS['journal']['journal']}
MAPPINGS['lcc'] = {'lcc':MAPPINGS['journal']['journal']}
MAPPINGS['article_history'] = {'article_history':MAPPINGS['journal']['journal']}
MAPPINGS['editor_group'] = {'editor_group':MAPPINGS['journal']['journal']}
MAPPINGS['news'] = {'news':MAPPINGS['journal']['journal']}
MAPPINGS['lock'] = {'lock':MAPPINGS['journal']['journal']}
MAPPINGS['bulk_reapplication'] = {'bulk_reapplication':MAPPINGS['journal']['journal']}
MAPPINGS['bulk_upload'] = {'bulk_upload':MAPPINGS['journal']['journal']}
MAPPINGS['journal_history'] = {'journal_history':MAPPINGS['journal']['journal']}

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
    "publisher_query" : {"role" : "publisher", "default_filter" : False, "owner_filter" : True},
    "editor_query" : {"role" : "editor", "default_filter" : False, "editor_filter" : True},
    "associate_query" : {"role" : "associate_editor", "default_filter" : False, "associate_filter" : True},
    "publisher_reapp_query" : {"role" : "publisher", "default_filter" : False, "owner_filter" : True, "reapp_filter" : True}
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

FEED_TITLE = "DOAJ Recent Journals Added"

# Maximum number of feed entries to be given in a single response.  If this is omitted, it will
# default to 20
MAX_FEED_ENTRIES = 100

# Maximum age of feed entries (in seconds) (default value here is 30 days).
MAX_FEED_ENTRY_AGE = 2592000

# NOT USED IN THIS IMPLEMENTATION
# Which index to run feeds from
#FEED_INDEX = "journal"

# Licensing terms for feed content
FEED_LICENCE = "(c) DOAJ 2013. CC BY-SA."

# name of the feed generator (goes in the atom:generator element)
FEED_GENERATOR = "CottageLabs feed generator"

# Larger image to use as the logo for all of the feeds
FEED_LOGO = "https://doaj.org/static/doaj/images/favicon.ico"


# ============================
# OAI-PMH SETTINGS

OAI_DC_METADATA_FORMAT = {
    "metadataPrefix": "oai_dc",
    "schema": "http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
    "metadataNamespace": "http://www.openarchives.org/OAI/2.0/oai_dc/"
}

OAI_DOAJ_METADATA_FORMAT = {
    "metadataPrefix": "oai_doaj",
    "schema": "https://doaj.org/static/doaj/doajArticles.xsd",
    "metadataNamespace": "https://doaj.org/features/oai_doaj/1.0/"
}

OAIPMH_METADATA_FORMATS = {
    # "specific endpoint": [list, of, formats, supported]

    None: [OAI_DC_METADATA_FORMAT],  # no specific endpoint, the request is to the root /oai path
    "article": [OAI_DC_METADATA_FORMAT, OAI_DOAJ_METADATA_FORMAT]
}

OAIPMH_IDENTIFIER_NAMESPACE = "doaj.org"

OAIPMH_LIST_RECORDS_PAGE_SIZE = 100

OAIPMH_LIST_IDENTIFIERS_PAGE_SIZE = 300

OAIPMH_RESUMPTION_TOKEN_EXPIRY = 86400

# =================================
# Settings for reapplication process

# Whether reactivation is ongoing; when False, reapplication pages will be hidden.
REAPPLICATION_ACTIVE = True

# The link showed in the bulk reapplication tab in the Publisher's area, showing help for filling out CSVs
CSV_DOC_LINK = 'https://docs.google.com/a/doaj.org/spreadsheet/ccc?key=0AkfPCpIPjZlmdEQySmdSN2tUNTJiSmotTDlXcm5fcmc#gid=0'


# =================================
# File Upload and crosswalk settings

# directory to upload files to.  MUST be full absolute path
# The default takes the directory above this, and then down in to "upload"
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "upload")

# Reapplication upload directory
REAPPLICATION_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "upload_reapplication")

# paths to schema files to validate incoming documents against for the various
# crosswalks available

SCHEMAS = {
    "doaj" : os.path.join(BASE_FILE_PATH, "static", "doaj", "doajArticles.xsd")
}

# maximum size of files that can be provided by-reference (the default value is 250Mb)
MAX_REMOTE_SIZE = 262144000

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

# root of the git repo
ROOT_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")

# directory into which to put files which are cached (e.g. the csv)
CACHE_DIR = os.path.join(ROOT_DIR, "cache")

# Publisher CSV storage
BULK_REAPP_PATH = os.path.join(ROOT_DIR, "reapp_csvs")

# Article and Journal History directories - they should be different
ARTICLE_HISTORY_DIR = os.path.join(ROOT_DIR, "history", "article")
JOURNAL_HISTORY_DIR = os.path.join(ROOT_DIR, "history", "journal")

# Where static files are served from - in case we need to serve a file
# from there ourselves using Flask instead of nginx (e.g. to support a
# legacy route to that file)
# Changing this will not change the actual folder that Flask serves
# static files from.
# http://flask.pocoo.org/snippets/102/
STATIC_DIR = os.path.join(ROOT_DIR, "portality", "static")


# ===================================
# Sitemap settings

# approximate rate of change of the Table of Contents for journals
TOC_CHANGEFREQ = "monthly"

STATIC_PAGES = [
    ("", "monthly"), # home page
    ("/search", "daily"),
    ("/toc", "monthly"),
    ("/application/new", "monthly"),
    ("/about", "monthly"),
    ("/publishers", "monthly"),
    ("/support", "monthly"),
    ("/contact", "yearly"),
    ("/supportDoaj", "monthly"),
    ("/members", "monthly"),
    ("/membership", "monthly"),
    ("/publishermembers", "monthly"),
    ("/faq", "monthly"),
    ("/features", "monthly"),
    ("/oainfo", "monthly"),
    ("/sponsors", "monthly")
]


# =====================================
# News feed settings

BLOG_URL = "http://doajournals.wordpress.com/"

BLOG_FEED_URL = "http://doajournals.wordpress.com/feed/atom/"

FRONT_PAGE_NEWS_ITEMS = 3

NEWS_PAGE_NEWS_ITEMS = 20


# =====================================
# Edit Lock settings

# amount of time loading an editable page locks it for, in seconds.
EDIT_LOCK_TIMEOUT = 1200


# =====================================
# Search query shortening settings

# bit,ly api shortening service
BITLY_SHORTENING_API_URL = "https://api-ssl.bitly.com/v3/shorten"

# bitly oauth token
# ENTER YOUR OWN TOKEN IN APPROPRIATE .cfg FILE
BITLY_OAUTH_TOKEN = ""

# =====================================
# when dates.format is called without a format argument, what format to use?
# FIXME: this is actually wrong - should really use the timezone correctly
DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# date formats that we know about, and should try, in order, when parsing
DATE_FORMATS = [
    "%Y-%m-%dT%H:%M:%SZ",   # e.g. 2014-09-23T11:30:45Z
    "%Y-%m-%d",             # e.g. 2014-09-23
    "%d/%m/%y",             # e.g. 29/02/80
    "%d/%m/%Y",             # e.g. 29/02/1980
    "%d-%m-%Y",             # e.g. 01-01-2015
    "%Y.%m.%d",             # e.g. 2014.09.12
    "%d.%m.%Y",             # e.g. 12.9.2014
    "%d.%m.%y",             # e.g. 12.9.14
    "%d %B %Y",             # e.g. 21 June 2014
    "%d-%b-%Y",             # e.g. 31-Jul-13
    "%d-%b-%y",             # e.g. 31-Jul-2013
    "%b-%y",                # e.g. Aug-13
    "%B %Y",                # e.g. February 2014
    "%Y"                    # e.g. 1978
]


# ========================================
# API configuration

DISCOVERY_MAX_PAGE_SIZE = 100

DISCOVERY_ARTICLE_SEARCH_SUBS = {
    "title" : "bibjson.title",
    "doi" : "bibjson.identifier.id.exact",
    "issn" :  "index.issn.exact",
    "publisher" : "bibjson.journal.publisher",
    "journal" : "bibjson.journal.title",
    "abstract" :  "bibjson.abstract"
}

DISCOVERY_ARTICLE_SORT_SUBS = {
    "title" : "index.unpunctitle.exact"
}

DISCOVERY_JOURNAL_SEARCH_SUBS = {
    "title" : "index.title",
    "issn" :  "index.issn.exact",
    "publisher" : "bibjson.publisher",
    "license" : "index.license.exact",
    "username" : "admin.owner.exact"
}

DISCOVERY_JOURNAL_SORT_SUBS = {
    "title" : "index.unpunctitle.exact",
    "issn" :  "index.issn.exact"
}

DISCOVERY_APPLICATION_SEARCH_SUBS = {
    "title" : "index.title",
    "issn" :  "index.issn.exact",
    "publisher" : "bibjson.publisher",
    "license" : "index.license.exact"
}

DISCOVERY_APPLICATION_SORT_SUBS = {
    "title" : "index.unpunctitle.exact",
    "issn" :  "index.issn.exact"
}
