import os

from portality import constants

# Use these options to place the application into READ ONLY mode

# This puts the UI into READ_ONLY mode
READ_ONLY_MODE = False

# This puts the cron jobs into READ_ONLY mode
SCRIPTS_READ_ONLY_MODE = False

DOAJ_VERSION = "3.1.5"

OFFLINE_MODE = False

# List the features we want to be active
FEATURES = ['api']
VALID_FEATURES = ['api']

# ========================
# MAIN SETTINGS

# base path, to the directory where this settings file lives
BASE_FILE_PATH = os.path.dirname(os.path.realpath(__file__))

BASE_URL = "https://doaj.org"
if BASE_URL.startswith('https://'):
    BASE_DOMAIN = BASE_URL[8:]
elif BASE_URL.startswith('http://'):
    BASE_DOMAIN = BASE_URL[7:]
else:
    BASE_DOMAIN = BASE_URL
API_BLUEPRINT_NAME = "api_v1"  # change if upgrading API to new version and creating new view for that

# Used when generating external links, e.g. in the API docs
PREFERRED_URL_SCHEME = 'https'

# make this something secret in your overriding app.cfg
SECRET_KEY = "default-key"

# contact info
ADMIN_NAME = "DOAJ"
ADMIN_EMAIL = "sysadmin@cottagelabs.com"
ADMINS = ["steve@cottagelabs.com", "mark@cottagelabs.com"]
SYSTEM_EMAIL_FROM = 'feedback@doaj.org'
CC_ALL_EMAILS_TO = SYSTEM_EMAIL_FROM  # DOAJ may get a dedicated inbox in the future
ENABLE_EMAIL = True
ENABLE_PUBLISHER_EMAIL = True
MANAGING_EDITOR_EMAIL = "managing-editors@doaj.org"
CONTACT_FORM_ADDRESS = "feedback+contactform@doaj.org"

# Error logging via email
SUPPRESS_ERROR_EMAILS = False
ERROR_LOGGING_EMAIL = 'doaj.internal@gmail.com'
ERROR_MAIL_HOSTNAME = 'smtp.mailgun.org'
ERROR_MAIL_USERNAME = None
ERROR_MAIL_PASSWORD = None

# service info
SERVICE_NAME = "Directory of Open Access Journals"
SERVICE_TAGLINE = "DOAJ is an online directory that indexes and provides access to quality open access, peer-reviewed journals."
HOST = '0.0.0.0'
DEBUG = False
DEBUG_TB_TEMPLATE_EDITOR_ENABLED = True
DEBUG_TB_INTERCEPT_REDIRECTS = False
PORT = 5004
SSL = True
VALID_ENVIRONMENTS = ['dev', 'test', 'staging', 'production', 'harvester']

# elasticsearch settings
ELASTIC_SEARCH_HOST = "http://localhost:9200" # remember the http:// or https://
ELASTIC_SEARCH_DB = "doaj"
ELASTIC_SEARCH_TEST_DB = "doajtest"
INITIALISE_INDEX = True # whether or not to try creating the index and required index types on startup
ELASTIC_SEARCH_VERSION = "1.7.5"
ELASTIC_SEARCH_SNAPSHOT_REPOSITORY = None
ELASTIC_SEARCH_SNAPSHOT_TTL = 366

ES_TERMS_LIMIT = 1024

# /status endpoint connection to all app machines
APP_MACHINES_INTERNAL_IPS = [HOST + ':' + str(PORT)] # This should be set in production.cfg (or dev.cfg etc)

# huey/redis settings
HUEY_REDIS_HOST = '127.0.0.1'
HUEY_REDIS_PORT = 6379
HUEY_EAGER = False

#  Crontab schedules must be for unique times to avoid delays due to perceived race conditions
HUEY_SCHEDULE = {
    "sitemap": {"month": "*", "day": "*", "day_of_week": "*", "hour": "8", "minute": "0"},
    "reporting": {"month": "*", "day": "1", "day_of_week": "*", "hour": "0", "minute": "0"},
    "journal_csv": {"month": "*", "day": "*", "day_of_week": "*", "hour": "*", "minute": "35"},
    "read_news": {"month": "*", "day": "*", "day_of_week": "*", "hour": "*", "minute": "30"},
    "article_cleanup_sync": {"month": "*", "day": "2", "day_of_week": "*", "hour": "0", "minute": "0"},
    "async_workflow_notifications": {"month": "*", "day": "*", "day_of_week": "1", "hour": "5", "minute": "0"},
    "request_es_backup": {"month": "*", "day": "*", "day_of_week": "*", "hour": "6", "minute": "0"},
    "check_latest_es_backup": {"month": "*", "day": "*", "day_of_week": "*", "hour": "9", "minute": "0"},
    "prune_es_backups": {"month": "*", "day": "*", "day_of_week": "*", "hour": "9", "minute": "15"},
    "public_data_dump": {"month": "*", "day": "*/6", "day_of_week": "*", "hour": "10", "minute": "0"}
}

HUEY_TASKS = {
    "ingest_articles": {"retries": 10, "retry_delay": 15}
}

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
#MAIL_USE_TLS               # default FalseW
#MAIL_USE_SSL               # default False
#MAIL_DEBUG                 # default app.debug
#MAIL_USERNAME              # default None
#MAIL_PASSWORD              # default None
#MAIL_DEFAULT_SENDER        # default None
#MAIL_MAX_EMAILS            # default None
#MAIL_SUPPRESS_SEND         # default app.testing

# ================================
# File store

# put this in your production.cfg, to store on S3:
# STORE_IMPL = "portality.store.StoreS3"

STORE_IMPL = "portality.store.StoreLocal"
STORE_TMP_IMPL = "portality.store.TempStore"

from portality.lib import paths
STORE_LOCAL_DIR = paths.rel2abs(__file__, "..", "local_store", "main")
STORE_TMP_DIR = paths.rel2abs(__file__, "..", "local_store", "tmp")
STORE_LOCAL_EXPOSE = False  # if you want to allow files in the local store to be exposed under /store/<path> urls.  For dev only.
STORE_LOCAL_WRITE_BUFFER_SIZE = 16777216
STORE_TMP_WRITE_BUFFER_SIZE = 16777216

# containers (buckets in AWS) where various content will be stored
# These values are placeholders, and must be overridden in live deployment
# this prevents test environments from accidentally writing to the production buckets
STORE_ANON_DATA_CONTAINER = "doaj-anon-data-placeholder"
STORE_CACHE_CONTAINER = "doaj-data-cache-placeholder"
STORE_PUBLIC_DATA_DUMP_CONTAINER = "doaj-data-dump-placeholder"


# S3 credentials for relevant scopes
STORE_S3_SCOPES = {
    "anon_data" : {
        "aws_access_key_id" : "put this in your dev/test/production.cfg",
        "aws_secret_access_key" : "put this in your dev/test/production.cfg"
    },
    "cache" : {
        "aws_access_key_id" : "put this in your dev/test/production.cfg",
        "aws_secret_access_key" : "put this in your dev/test/production.cfg"
    },
    # Used by the api_export script to dump data from the api
    "public_data_dump" : {

        "aws_access_key_id" : "put this in your dev/test/production.cfg",
        "aws_secret_access_key" : "put this in your dev/test/production.cfg"
    }
}


# ========================
# workflow email notification settings
MAN_ED_IDLE_WEEKS = 4      # weeks before an application is considered reminder-worthy
ED_IDLE_WEEKS = 3           # weeks before the editor is warned about idle applications in their group
ASSOC_ED_IDLE_DAYS = 10
ASSOC_ED_IDLE_WEEKS = 3

# Which statuses the notification queries should be filtered to show
MAN_ED_NOTIFICATION_STATUSES = [
    constants.APPLICATION_STATUS_PENDING,
    constants.APPLICATION_STATUS_IN_PROGRESS, constants.APPLICATION_STATUS_COMPLETED,
    constants.APPLICATION_STATUS_ON_HOLD
]
ED_NOTIFICATION_STATUSES = [
    constants.APPLICATION_STATUS_PENDING,
    constants.APPLICATION_STATUS_IN_PROGRESS,
    constants.APPLICATION_STATUS_COMPLETED
]
ASSOC_ED_NOTIFICATION_STATUSES = [
    constants.APPLICATION_STATUS_PENDING,
    constants.APPLICATION_STATUS_IN_PROGRESS
]

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
TOP_LEVEL_ROLES = ["admin", "publisher", "editor", "associate_editor", "api", "ultra_bulk_delete"]

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

# If you change the reserved usernames, your data will likely need a migration to remove their
# existing use in the system.
SYSTEM_USERNAME = "system"
RESERVED_USERNAMES = [SYSTEM_USERNAME]  # do not allow the creation of user accounts with this id

# ========================
# MAPPING SETTINGS

FACET_FIELD = ".exact"

# an array of DAO classes from which to retrieve the type-specific ES mappings
# to be loaded into the index during initialisation.
ELASTIC_SEARCH_MAPPINGS = [
    "portality.models.Journal",
    "portality.models.Suggestion",
    "portality.models.harvester.HarvestState"
]

# Map from dataobj coercion declarations to ES mappings
DATAOBJ_TO_MAPPING_DEFAULTS = {
    "unicode": {
        "type": "string",
        "fields": {
            "exact": {
                "type": "string",
                "index": "not_analyzed",
                "store": True
            }
        }
    },
    "str": {
        "type": "string",
        "fields": {
            "exact": {
                "type": "string",
                "index": "not_analyzed",
                "store": True
            }
        }
    },
    "unicode_upper": {
        "type": "string",
        "fields": {
            "exact": {
                "type": "string",
                "index": "not_analyzed",
                "store": True
            }
        }
    },
    "utcdatetime": {
        "type": "date",
        "format": "dateOptionalTime"
    },
    "bool": {
        "type": "boolean"
    },
    "integer": {
        "type": "long"
    },
    "bigenddate": {
        "type": "date",
        "format": "dateOptionalTime"
    }
}


DEFAULT_DYNAMIC_MAPPING = {
    "dynamic_templates": [
        {
            "default": {
                "match": "*",
                "match_mapping_type": "string",
                "mapping": {
                    "type": "multi_field",
                    "fields": {
                        "{name}": {"type": "{dynamic_type}", "index": "analyzed", "store": "no"},
                        "exact": {"type": "{dynamic_type}", "index": "not_analyzed", "store": "yes"}
                    }
                }
            }
        }
    ]
}

# LEGACY MAPPINGS
# a dict of the ES mappings. identify by name, and include name as first object name
# and identifier for how non-analyzed fields for faceting are differentiated in the mappings

MAPPINGS = {
    'account': {
        'account': DEFAULT_DYNAMIC_MAPPING
    }
}
MAPPINGS['article'] = {'article': DEFAULT_DYNAMIC_MAPPING}
MAPPINGS['suggestion'] = {'suggestion': DEFAULT_DYNAMIC_MAPPING}
MAPPINGS['upload'] = {'upload': DEFAULT_DYNAMIC_MAPPING}
MAPPINGS['cache'] = {'cache': DEFAULT_DYNAMIC_MAPPING}
MAPPINGS['lcc'] = {'lcc': DEFAULT_DYNAMIC_MAPPING}
MAPPINGS['article_history'] = {'article_history': DEFAULT_DYNAMIC_MAPPING}
MAPPINGS['editor_group'] = {'editor_group': DEFAULT_DYNAMIC_MAPPING}
MAPPINGS['news'] = {'news': DEFAULT_DYNAMIC_MAPPING}
MAPPINGS['lock'] = {'lock': DEFAULT_DYNAMIC_MAPPING}
MAPPINGS['journal_history'] = {'journal_history': DEFAULT_DYNAMIC_MAPPING}
MAPPINGS['provenance'] = {'provenance': DEFAULT_DYNAMIC_MAPPING}
MAPPINGS['background_job'] = {'background_job': DEFAULT_DYNAMIC_MAPPING}

# ========================
# QUERY SETTINGS

QUERY_ROUTE = {
    "query" : {
        "journal,article" : {
            "auth" : False,
            "role" : None,
            "query_validator" : "public_query_validator",
            "query_filters" : ["only_in_doaj"],
            "result_filters" : ["public_result_filter", "prune_author_emails"],
            "dao" : "portality.models.search.JournalArticle",
            "required_parameters" : {"ref" : ["fqw", "public_journal_article", "subject_page"]}
        },
        "article" : {
            "auth" : False,
            "role" : None,
            "query_filters" : ["only_in_doaj"],
            "result_filters" : ["public_result_filter", "prune_author_emails"],
            "dao" : "portality.models.Article",
            "required_parameters" : {"ref" : ["toc"]}
        }
    },
    "publisher_query" : {
        "journal" : {
            "auth" : True,
            "role" : "publisher",
            "query_filters" : ["owner", "only_in_doaj"],
            "result_filters" : ["publisher_result_filter", "prune_author_emails"],
            "dao" : "portality.models.Journal"
        },
        "suggestion" : {
            "auth" : True,
            "role" : "publisher",
            "query_filters" : ["owner", "update_request"],
            "result_filters" : ["publisher_result_filter", "prune_author_emails"],
            "dao" : "portality.models.Suggestion"
        }
    },
    "admin_query" : {
        "journal" : {
            "auth" : True,
            "role" : "admin",
            "dao" : "portality.models.Journal"
        },
        "suggestion" : {
            "auth" : True,
            "role" : "admin",
            "dao" : "portality.models.Suggestion"
        },
        "editor,group" : {
            "auth" : True,
            "role" : "admin",
            "dao" : "portality.models.EditorGroup"
        },
        "account" : {
            "auth" : True,
            "role" : "admin",
            "dao" : "portality.models.Account"
        },
        "journal,article" : {
            "auth" : True,
            "role" : "admin",
            "dao" : "portality.models.search.JournalArticle"
        },
        "background,job" : {
            "auth" : True,
            "role" : "admin",
            "dao" : "portality.models.BackgroundJob"
        }
    },
    "associate_query" : {
        "journal" : {
            "auth" : True,
            "role" : "associate_editor",
            "query_filters" : ["associate"],
            "dao" : "portality.models.Journal"
        },
        "suggestion" : {
            "auth" : True,
            "role" : "associate_editor",
            "query_filters" : ["associate"],
            "dao" : "portality.models.Suggestion"
        }
    },
    "editor_query" : {
        "journal" : {
            "auth" : True,
            "role" : "editor",
            "query_filters" : ["editor"],
            "dao" : "portality.models.Journal"
        },
        "suggestion" : {
            "auth" : True,
            "role" : "editor",
            "query_filters" : ["editor"],
            "dao" : "portality.models.Suggestion"
        }
    },
    "api_query" : {
        "article" : {
            "auth" : False,
            "role" : None,
            "query_filters" : ["only_in_doaj", "public_source"],
            "dao" : "portality.models.Article",
            "required_parameters" : None,
            "keepalive" : "10m"
        },
        "journal" : {
            "auth" : False,
            "role" : None,
            "query_filters" : ["only_in_doaj", "public_source"],
            "dao" : "portality.models.Journal",
            "required_parameters" : None
        },
        "application" : {
            "auth" : True,
            "role" : None,
            "query_filters" : ["owner", "private_source"],
            "dao" : "portality.models.Suggestion",
            "required_parameters" : None
        }
    }
}

QUERY_FILTERS = {
    # sanitisers
    "public_query_validator" : "portality.lib.query_filters.public_query_validator",

    # query filters
    "only_in_doaj" : "portality.lib.query_filters.only_in_doaj",
    "owner" : "portality.lib.query_filters.owner",
    "update_request" : "portality.lib.query_filters.update_request",
    "associate" : "portality.lib.query_filters.associate",
    "editor" : "portality.lib.query_filters.editor",

    # result filters
    "public_result_filter": "portality.lib.query_filters.public_result_filter",
    "publisher_result_filter": "portality.lib.query_filters.publisher_result_filter",
    "prune_author_emails": "portality.lib.query_filters.prune_author_emails",

    # source filters
    "private_source": "portality.lib.query_filters.private_source",
    "public_source": "portality.lib.query_filters.public_source",
}

UPDATE_REQUESTS_SHOW_OLDEST = "2018-01-01T00:00:00Z"

AUTOCOMPLETE_ADVANCED_FIELD_MAPS = {
    "bibjson.publisher" : "index.publisher_ac",
    "bibjson.institution" : "index.institution_ac",
    "bibjson.provider" : "index.provider_ac"
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
# File Upload and crosswalk settings

# directory to upload files to.  MUST be full absolute path
# The default takes the directory above this, and then down in to "upload"
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "upload")
FAILED_ARTICLE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "failed_articles")

# paths to schema files to validate incoming documents against for the various
# crosswalks available

SCHEMAS = {
    "doaj": os.path.join(BASE_FILE_PATH, "static", "doaj", "doajArticles.xsd"),
    "crossref": os.path.join(BASE_FILE_PATH, "static", "crossref", "crossref4.4.2.xsd")
}

DOAJ_SCHEMA = None
CROSSREF_SCHEMA = None
LOAD_CROSSREF_THREAD = None

# mapping of format names to modules which implement the crosswalks
ARTICLE_CROSSWALKS = {
    "doaj": "portality.crosswalks.article_doaj_xml.DOAJXWalk",
    "crossref": "portality.crosswalks.article_crossref_xml.CrossrefXWalk"
}

# maximum size of files that can be provided by-reference (the default value is 250Mb)
MAX_REMOTE_SIZE = 262144000

# =================================
# Cache settings

# number of seconds site statistics should be considered fresh
# 1800s = 30mins
SITE_STATISTICS_TIMEOUT = 1800

# root of the git repo
ROOT_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")

# directory into which to put files which are cached (e.g. the csv)
CACHE_DIR = os.path.join(ROOT_DIR, "cache")

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
    # ("/search", "daily"),  # taken out since javascript-enabled bots were spidering this, causing enormous load - there should be other ways to present a list of all journals to them if we need to
    ("/toc", "monthly"),
    ("/application/new", "monthly"),
    ("/about", "monthly"),
    ("/publishers", "monthly"),
    ("/support", "monthly"),
    ("/contact", "yearly"),
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

# amount of time a background task can lock a resource for, in seconds
BACKGROUND_TASK_LOCK_TIMEOUT = 3600


# =====================================
# Search query shortening settings

# bit,ly api shortening service
BITLY_SHORTENING_API_URL = "https://api-ssl.bitly.com/v4/shorten"

# bitly oauth token
# ENTER YOUR OWN TOKEN IN APPROPRIATE .cfg FILE
BITLY_OAUTH_TOKEN = ""

# =====================================
# when dates.format is called without a format argument, what format to use?
# FIXME: this is actually wrong - should really use the timezone correctly
DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# date formats that we know about, and should try, in order, when parsing
DATE_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%fZ",   # e.g. 2010-01-01T00:00:00.000Z
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

# The last_manual_update field was initialised to this value. Used to label as 'never'.
DEFAULT_TIMESTAMP = "1970-01-01T00:00:00Z"

# ========================================
# API configuration

# maximum number of records to return per page
DISCOVERY_MAX_PAGE_SIZE = 100

# maximum number of records to return in total (a request for a page starting beyond this number will fail)
DISCOVERY_MAX_RECORDS_SIZE = 1000

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

# API data dump settings
DISCOVERY_BULK_PAGE_SIZE = 1000
DISCOVERY_RECORDS_PER_FILE = 100000

# =========================================
# scheduled reports configuration
REPORTS_BASE_DIR = "/home/cloo/reports/"
REPORTS_EMAIL_TO = ["feedback@doaj.org"]


# ========================================
# Hotjar configuration

# hotjar id - only activate this in production
HOTJAR_ID = ""


# ========================================
# Google Analytics configuration
# specify in environment .cfg file - avoids sending live analytics
# events from test and dev environments
GOOGLE_ANALYTICS_ID = ''

# Where to put the google analytics logs
GOOGLE_ANALTYICS_LOG_DIR = None

# Google Analytics custom dimensions. These are configured in the GA interface.
GA_DIMENSIONS = {
    'oai_res_id': 'dimension1',                                                                    # In GA as OAI:Record
}

# GA for OAI-PMH
GA_CATEGORY_OAI = 'OAI-PMH'

# GA for Atom
GA_CATEGORY_ATOM = 'Atom'
GA_ACTION_ACTION = 'Feed request'

# GA for JournalCSV
GA_CATEGORY_JOURNALCSV = 'JournalCSV'
GA_ACTION_JOURNALCSV = 'Download'

# GA for OpenURL
GA_CATEGORY_OPENURL = 'OpenURL'

# GA for API
GA_CATEGORY_API = 'API Hit'
GA_ACTIONS_API = {
    'search_applications': 'Search applications',
    'search_journals': 'Search journals',
    'search_articles': 'Search articles',
    'create_application': 'Create application',
    'retrieve_application': 'Retrieve application',
    'update_application': 'Update application',
    'delete_application': 'Delete application',
    'create_article': 'Create article',
    'retrieve_article': 'Retrieve article',
    'update_article': 'Update article',
    'delete_article': 'Delete article',
    'retrieve_journal': 'Retrieve journal',
    'bulk_application_create': 'Bulk application create',
    'bulk_application_delete': 'Bulk application delete',
    'bulk_article_create': 'Bulk article create',
    'bulk_article_delete': 'Bulk article delete'
}


# GA for fixed query widget
GA_CATEGORY_FQW = 'FQW'
GA_ACTION_FQW = 'Hit'

# ========================================
# Anonymisation configuration
ANON_SALT = 'changeme'

# ========================================
# Quick Reject Feature Config
QUICK_REJECT_REASONS = [
    "The journal has not published enough research content to qualify for DOAJ inclusion.",
    "The ISSN is incorrect, provisional or not registered with issn.org.",
    "The URL(s) provided in the application do not work.",
    "The contact details provided are not real names of individuals.",
    "The journal is already in DOAJ.",
    "The journal is not Open Access.",
    "The journal title in the application and/or website does not match the title at issn.org.",
    "The application has incomplete answers or the URLs given do not provide the required information.",
    "This application is a duplicate.",
    "The full-text articles are not available article by article with individual links.",
    "The information in the journal implies that it does not employ a fair & robust peer review process.",
    "The journal or publisher has been previously rejected or removed from DOAJ.",
    "The journal's copyright policy is not available or unclear.",
    "The journal's licensing policy is not available or unclear.",
    "The information about the journal is in different languages.",
    "The journal makes a false claim to be indexed in DOAJ or other databases or displays non-standard Impact Factors.",
    "The journal does not employ good publishing practices."
]

# ========================================
# Elastic APM config  (MUST be configured in env file)
ENABLE_APM = False

ELASTIC_APM = {
  # Set required service name. Allowed characters:
  # a-z, A-Z, 0-9, -, _, and space
  'SERVICE_NAME': '',

  # Use if APM Server requires a token
  'SECRET_TOKEN': '',

  # Set custom APM Server URL (default: http://localhost:8200)
  'SERVER_URL': '',
}

########################################
## Consent Cookie

CONSENT_COOKIE_KEY = "doaj-cookie-consent"



#############################################
## Harvester Configuration

## Configuration options for the DOAJ API Client

DOAJ_SEARCH_BASE = "https://doaj.org"

DOAJ_SEARCH_PORT = 80

DOAJ_QUERY_ENDPOINT = "query"

DOAJ_SEARCH_TYPE = "journal,article"

DOAJ_API_BASE_URL = "https://doaj.org/api/v1/"


## EPMC Client configuration

EPMC_REST_API = "http://www.ebi.ac.uk/europepmc/webservices/rest/"
EPMC_TARGET_VERSION = "6.2"

# General harvester configuraiton

HARVESTERS = [
    "portality.harvester.epmc.epmc_harvester.EPMCHarvester"
]

INITIAL_HARVEST_DATE = "2015-12-01T00:00:00Z"

# The mapping from account ids to API keys.  MUST NOT be checked into the repo, put these
# in the local.cfg instead
HARVESTER_API_KEYS = {

}

EPMC_HARVESTER_THROTTLE = 0.2

# Process name while harvester is starting, running
HARVESTER_STARTING_PROCTITLE = 'harvester: starting'
HARVESTER_RUNNING_PROCTITLE = 'harvester: running'

# Minutes we wait between terminate and kill
HARVESTER_MAX_WAIT = 10

# Email notifications
HARVESTER_EMAIL_ON_EVENT = False
HARVESTER_EMAIL_RECIPIENTS = None
HARVESTER_EMAIL_FROM_ADDRESS = "harvester@doaj.org"
HARVESTER_EMAIL_SUBJECT_PREFIX = "[harvester] "

#Recaptcha test keys, should be overridden in dev.cfg by the keys obtained from Google ReCaptcha v2
RECAPTCHA_SITE_KEY = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
RECAPTCHA_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"

