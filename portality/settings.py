"""
~~AppSettings:Config~~
"""
import os
from portality import constants
from portality.lib import paths

###########################################
# Application Version information
# ~~->API:Feature~~

DOAJ_VERSION = "6.2.18"
API_VERSION = "3.0.1"

######################################
# Deployment configuration

HOST = '0.0.0.0'
DEBUG = False
PORT = 5004
SSL = True
VALID_ENVIRONMENTS = ['dev', 'test', 'staging', 'production', 'harvester']
CMS_BUILD_ASSETS_ON_STARTUP = False
# Cookies security
SESSION_COOKIE_SAMESITE='Strict'
SESSION_COOKIE_SECURE=True
REMEMBER_COOKIE_SECURE = True

####################################
# Debug Mode

# PyCharm debug settings
DEBUG_PYCHARM = False  # do not try to connect to the PyCharm debugger by default
DEBUG_PYCHARM_SERVER = 'localhost'
DEBUG_PYCHARM_PORT = 6000

#~~->DebugToolbar:Framework~~
DEBUG_TB_TEMPLATE_EDITOR_ENABLED = True
DEBUG_TB_INTERCEPT_REDIRECTS = False

#######################################
# Elasticsearch configuration
#~~->Elasticsearch:Technology

# elasticsearch settings # TODO: changing from single host / esprit to multi host on ES & correct the default
ELASTIC_SEARCH_HOST = os.getenv('ELASTIC_SEARCH_HOST', 'http://localhost:9200') # remember the http:// or https://
ELASTICSEARCH_HOSTS = [{'host': 'localhost', 'port': 9200}, {'host': 'localhost', 'port': 9201}]
ELASTIC_SEARCH_VERIFY_CERTS = True  # Verify the SSL certificate of the ES host.  Set to False in dev.cfg to avoid having to configure your local certificates

# 2 sets of elasticsearch DB settings - index-per-project and index-per-type. Keep both for now so we can migrate.
# e.g. host:port/index/type/id
ELASTIC_SEARCH_DB = "doaj"
ELASTIC_SEARCH_TEST_DB = "doajtest"

# e.g. host:port/type/doc/id
ELASTIC_SEARCH_INDEX_PER_TYPE = True
INDEX_PER_TYPE_SUBSTITUTE = '_doc'      # Migrated from esprit
ELASTIC_SEARCH_DB_PREFIX = "doaj-"    # note: include the separator
ELASTIC_SEARCH_TEST_DB_PREFIX = "doajtest-"

INITIALISE_INDEX = True # whether or not to try creating the index and required index types on startup
ELASTIC_SEARCH_VERSION = "1.7.5"
ELASTIC_SEARCH_SNAPSHOT_REPOSITORY = None
ELASTIC_SEARCH_SNAPSHOT_TTL = 366

ES_TERMS_LIMIT = 1024

#####################################################
# Elastic APM config  (MUST be configured in env file)
# ~~->APM:Feature~~

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

###########################################
# Event handler

# use this to queue events asynchronously through kafka
EVENT_SEND_FUNCTION = "portality.events.kafka_producer.send_event"
# use this one to bypass kafka and process events immediately/synchronously
# EVENT_SEND_FUNCTION = "portality.events.shortcircuit.send_event"

KAFKA_BROKER = "kafka://localhost:9092"
KAFKA_EVENTS_TOPIC = "events"
KAFKA_BOOTSTRAP_SERVER = "localhost:9092"

###########################################
# Read Only Mode
#
# Use these options to place the application into READ ONLY mode

# This puts the UI into READ_ONLY mode
# ~~->ReadOnlyMode:Feature~~
READ_ONLY_MODE = False

# This puts the cron jobs into READ_ONLY mode
SCRIPTS_READ_ONLY_MODE = False


###########################################
# Feature Toggles

# ~~->OfflineMode:Feature~~
OFFLINE_MODE = False

# List the features we want to be active (API v1 and v2 remain with redirects to v3)
# ~~->API:Feature~~
FEATURES = ['api1', 'api2', 'api3']
VALID_FEATURES = ['api1', 'api2', 'api3']

########################################
# File Path and URL Path settings

# root of the git repo
ROOT_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")

# base path, to the directory where this settings file lives
BASE_FILE_PATH = os.path.dirname(os.path.realpath(__file__))

BASE_URL = "https://doaj.org"
if BASE_URL.startswith('https://'):
    BASE_DOMAIN = BASE_URL[8:]
elif BASE_URL.startswith('http://'):
    BASE_DOMAIN = BASE_URL[7:]
else:
    BASE_DOMAIN = BASE_URL

# ~~->API:Feature~~
BASE_API_URL = "https://doaj.org/api/"
API_CURRENT_BLUEPRINT_NAME = "api_v3"  # change if upgrading API to new version and creating new view

# URL used for the journal ToC URL in the journal CSV export
# NOTE: must be the correct route as configured in view/doaj.py
# ~~->ToC:WebRoute~~
JOURNAL_TOC_URL_FRAG = BASE_URL + '/toc/'

# Used when generating external links, e.g. in the API docs
PREFERRED_URL_SCHEME = 'https'

# Whether the app is running behind a proxy, for generating URLs based on X-Forwarded-Proto
# ~~->ProxyFix:Framework~~
PROXIED = False

# directory to upload files to.  MUST be full absolute path
# The default takes the directory above this, and then down in to "upload"
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "upload")
FAILED_ARTICLE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "failed_articles")

# directory where reports are output
REPORTS_BASE_DIR = "/home/cloo/reports/"

##################################
# File store
# ~~->FileStore:Feature~~

# put this in your production.cfg, to store everything on S3:
# STORE_IMPL = "portality.store.StoreS3"

STORE_IMPL = "portality.store.StoreLocal"
STORE_SCOPE_IMPL = {
# Enable this by scope in order to have different scopes store via different storage implementations
#     constants.STORE__SCOPE__PUBLIC_DATA_DUMP: "portality.store.StoreS3"
}

STORE_TMP_IMPL = "portality.store.TempStore"

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
STORE_HARVESTER_CONTAINER = "doaj-harvester"

# S3 credentials for relevant scopes
# ~~->S3:Technology~~
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
    constants.STORE__SCOPE__PUBLIC_DATA_DUMP : {
        "aws_access_key_id" : "put this in your dev/test/production.cfg",
        "aws_secret_access_key" : "put this in your dev/test/production.cfg"
    },
    # Used to store harvester run logs to S3
    "harvester" : {
        "aws_access_key_id" : "put this in your dev/test/production.cfg",
        "aws_secret_access_key" : "put this in your dev/test/production.cfg"
    }
}

STORE_S3_MULTIPART_THRESHOLD = 5 * 1024**3   # 5GB

####################################
# CMS configuration

# paths where static content should be served from.
# * in the order you want them searched
# * relative to the portality directory
# ~~->CMS:DataStore~~
STATIC_PATHS = [
    "static",
    "../cms/assets"
]

# GitHub base url where static content can be edited by the DOAJ team (you can leave out the trailing slash)
#~~->GitHub:ExternalService~~
CMS_EDIT_BASE_URL = "https://github.com/DOAJ/doaj/edit/static_pages/cms"

# Where static files are served from - in case we need to serve a file
# from there ourselves using Flask instead of nginx (e.g. to support a
# legacy route to that file)
# Changing this will not change the actual folder that Flask serves
# static files from.
# http://flask.pocoo.org/snippets/102/
STATIC_DIR = os.path.join(ROOT_DIR, "portality", "static")

######################################
# Service Descriptive Text

SERVICE_NAME = "Directory of Open Access Journals"

###################################
# Cookie settings

# make this something secret in your overriding app.cfg
# ~~->Cookies:Feature~~
SECRET_KEY = "default-key"


# Consent Cookie and other Top-Level dismissable notes
# ~~->ConsentCookie:Feature~~
CONSENT_COOKIE_KEY = "doaj-cookie-consent"

# site notes, which can be configured to run any time with any content
# ~~-> SiteNote:Feature~~
SITE_NOTE_ACTIVE = False
SITE_NOTE_KEY = "doaj-site-note"
SITE_NOTE_SLEEP = 259200    # every 3 days
SITE_NOTE_COOKIE_VALUE = "You have seen our most recent site wide announcement"
SITE_NOTE_TEMPLATE = "doaj/site_note.html"

####################################
# Authorisation settings
# ~~->AuthNZ:Feature~~

# Can people register publicly? If false, only the superuser can create new accounts
PUBLIC_REGISTER = True

SUPER_USER_ROLE = "admin"

LOGIN_VIA_ACCOUNT_ID = True

# amount of time a reset token is valid for (86400 is 24 hours)
PASSWORD_RESET_TIMEOUT = 86400
# amount of time a reset token for a new account is valid for
PASSWORD_CREATE_TIMEOUT = PASSWORD_RESET_TIMEOUT * 14

#"api" top-level role is added to all acounts on creation; it can be revoked per account by removal of the role.
TOP_LEVEL_ROLES = [
    "admin",
    "publisher",
    "editor",
    "associate_editor",
    "api",
    "ultra_bulk_delete",
    "preservation",
    constants.ROLE_PUBLIC_DATA_DUMP
]

ROLE_MAP = {
    "editor": [
        "associate_editor",     # note, these don't cascade, so we still need to list all the low-level roles
        "edit_journal",
        "edit_suggestion",
        "edit_application",      # todo: switchover from suggestion to application
        "editor_area",
        "assign_to_associate",
        "list_group_journals",
        "list_group_suggestions",
        "read_notifications"
    ],
    "associate_editor": [
        "edit_journal",
        "edit_suggestion",
        "editor_area",
        "read_notifications"
    ]
}

# If you change the reserved usernames, your data will likely need a migration to remove their
# existing use in the system.
SYSTEM_USERNAME = "system"
RESERVED_USERNAMES = [SYSTEM_USERNAME]  # do not allow the creation of user accounts with this id

# Role map to destination route on login (when no other destination page is present)
# checked in order, if the user has the role in the first tuple position, they will
# be redirected to the endpoint in the second tuple position
ROLE_LOGIN_DESTINATIONS = [
    ("admin", "dashboard.top_todo"),
    ("editor", "editor.index"),
    ("associate_editor", "editor.index"),
    ("publisher", "publisher.index")
]

# if the user doesn't have one of the above roles, where should they be sent after login
DEFAULT_LOGIN_DESTINATION = "doaj.home"

####################################
# Email Settings
# ~~->Email:ExternalService

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

ENABLE_EMAIL = True
ENABLE_PUBLISHER_EMAIL = True

ADMIN_NAME = "DOAJ"
ADMIN_EMAIL = "sysadmin@cottagelabs.com"
ADMINS = ["steve@cottagelabs.com", "mark@cottagelabs.com"]

MANAGING_EDITOR_EMAIL = "managing-editors@doaj.org"
CONTACT_FORM_ADDRESS = "feedback+contactform@doaj.org"
SCRIPT_TAG_DETECTED_EMAIL_RECIPIENTS = ["helpdesk@doaj.org"]

SYSTEM_EMAIL_FROM = 'helpdesk@doaj.org'
CC_ALL_EMAILS_TO = SYSTEM_EMAIL_FROM  # DOAJ may get a dedicated inbox in the future

# Error logging via email
SUPPRESS_ERROR_EMAILS = False
ERROR_LOGGING_EMAIL = 'doaj.internal@gmail.com'
ERROR_MAIL_HOSTNAME = 'smtp.mailgun.org'
ERROR_MAIL_USERNAME = None
ERROR_MAIL_PASSWORD = None

# Reports email recipient
REPORTS_EMAIL_TO = ["helpdesk@doaj.org"]

########################################
# workflow email notification settings
# ~~->WorkflowNotifications:Feature~~

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

###################################
# status endpoint configuration
# ~~->StatusEndpoint:Feature~~

# /status endpoint connection to all app machines
APP_MACHINES_INTERNAL_IPS = [HOST + ':' + str(PORT)] # This should be set in production.cfg (or dev.cfg etc)

###########################################
# Background Jobs settings
# ~~->Huey:Technology~~
# ~~->Redis:Technology~~
# ~~->BackgroundTasks:Feature~~

# huey/redis settings
HUEY_REDIS_HOST = os.getenv('HUEY_REDIS_HOST', '127.0.0.1')
HUEY_REDIS_PORT = os.getenv('HUEY_REDIS_PORT', 6379)
HUEY_EAGER = False

# Crontab for never running a job - February 31st (use to disable tasks)
CRON_NEVER = {"month": "2", "day": "31", "day_of_week": "*", "hour": "*", "minute": "*"}

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
    "public_data_dump": {"month": "*", "day": "*/6", "day_of_week": "*", "hour": "10", "minute": "0"},
    "harvest": {"month": "*", "day": "*", "day_of_week": "*", "hour": "5", "minute": "30"},
    "anon_export": {"month": "*", "day": "10", "day_of_week": "*", "hour": "6", "minute": "30"},
    "old_data_cleanup": {"month": "*", "day": "12", "day_of_week": "*", "hour": "6", "minute": "30"},
    "monitor_bgjobs": {"month": "*", "day": "*/6", "day_of_week": "*", "hour": "10", "minute": "0"},
}

HUEY_TASKS = {
    "ingest_articles": {"retries": 10, "retry_delay": 15},
    "preserve": {"retries": 0, "retry_delay": 15}
}

####################################
# publisher area settings

# the earliest date accepted on the publisher's 'enter article metadata' form.
# code will default to 15 years before current year if commented out.
# ~~->ArticleMetadata:Page~~
METADATA_START_YEAR = 1960

# tick (on toc) and doaj seal settings
# ~~->Tick:Feature~~
TICK_THRESHOLD = '2014-03-19T00:00:00Z'

# ~~->UpdateRequests:Feature~~
UPDATE_REQUESTS_SHOW_OLDEST = "2018-01-01T00:00:00Z"

##############################################
# Elasticsearch Mappings
# ~~->Elasticsearch:Technology~~

FACET_FIELD = ".exact"

# an array of DAO classes from which to retrieve the type-specific ES mappings
# to be loaded into the index during initialisation.
ELASTIC_SEARCH_MAPPINGS = [
    "portality.models.Journal", # ~~->Journal:Model~~
    "portality.models.Application", # ~~->Application:Model~~
    "portality.models.DraftApplication",    # ~~-> DraftApplication:Model~~
    "portality.models.harvester.HarvestState",   # ~~->HarvestState:Model~~
    "portality.models.background.BackgroundJob" # ~~-> BackgroundJob:Model~~
]

# Map from dataobj coercion declarations to ES mappings
# ~~->DataObj:Library~~
# ~~->Seamless:Library~~
DATAOBJ_TO_MAPPING_DEFAULTS = {
    "unicode": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
#                "index": False,
                "store": True
            }
        }
    },
    "str": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
#                "index": False,
                "store": True
            }
        }
    },
    "unicode_upper": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
#                "index": False,
                "store": True
            }
        }
    },
    "unicode_lower": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
#                "index": False,
                "store": True
            }
        }
    },
    "isolang": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
#                "index": False,
                "store": True
            }
        }
    },
    "isolang_2letter": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
#                "index": False,
                "store": True
            }
        }
    },
    "country_code": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
#                "index": False,
                "store": True
            }
        }
    },
    "currency_code": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
#                "index": False,
                "store": True
            }
        }
    },
    "issn": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
#                "index": False,
                "store": True
            }
        }
    },
    "url": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
#                "index": False,
                "store": True
            }
        }
    },
    "utcdatetimemicros": {
        "type": "date",
        "format": "date_optional_time"
    },
    "utcdatetime": {
        "type": "date",
        "format": "date_optional_time"
    },
    "bool": {
        "type": "boolean"
    },
    "integer": {
        "type": "long"
    },
    "bigenddate": {
        "type": "date",
        "format": "date_optional_time"
    },
    "year": {
        "type": "date",
        "format": "year"
    }
}

# TODO: we may want a big-type and little-type setting
DEFAULT_INDEX_SETTINGS = \
    {
        'number_of_shards': 4,
        'number_of_replicas': 1
    }


DEFAULT_DYNAMIC_MAPPING = {
    'dynamic_templates': [
        {
            "strings": {
                "match_mapping_type": "string",
                "mapping": {
                    "type": "text",
                    "fields": {
                        "exact": {
                            "type": "keyword",
                            #"normalizer": "lowercase"
                        }
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
    'account': {  #~~->Account:Model~~
        # 'aliases': {
        #     'account': {}
        # },
        'mappings': DEFAULT_DYNAMIC_MAPPING,
        'settings': DEFAULT_INDEX_SETTINGS
    }
}
# MAPPINGS['article'] = {'article': DEFAULT_DYNAMIC_MAPPING}  #~~->Article:Model~~
# MAPPINGS['upload'] = {'upload': DEFAULT_DYNAMIC_MAPPING} #~~->Upload:Model~~
# MAPPINGS['cache'] = {'cache': DEFAULT_DYNAMIC_MAPPING} #~~->Cache:Model~~
# MAPPINGS['lcc'] = {'lcc': DEFAULT_DYNAMIC_MAPPING}  #~~->LCC:Model~~
# MAPPINGS['editor_group'] = {'editor_group': DEFAULT_DYNAMIC_MAPPING} #~~->EditorGroup:Model~~
# MAPPINGS['news'] = {'news': DEFAULT_DYNAMIC_MAPPING}    #~~->News:Model~~
# MAPPINGS['lock'] = {'lock': DEFAULT_DYNAMIC_MAPPING}    #~~->Lock:Model~~
# MAPPINGS['provenance'] = {'provenance': DEFAULT_DYNAMIC_MAPPING}    #~~->Provenance:Model~~
# MAPPINGS['preserve'] = {'preserve': DEFAULT_DYNAMIC_MAPPING}    #~~->Preservation:Model~~

MAPPINGS['article'] = MAPPINGS["account"]  #~~->Article:Model~~
MAPPINGS['upload'] = MAPPINGS["account"] #~~->Upload:Model~~
MAPPINGS['cache'] = MAPPINGS["account"] #~~->Cache:Model~~
MAPPINGS['lcc'] = MAPPINGS["account"]  #~~->LCC:Model~~
MAPPINGS['editor_group'] = MAPPINGS["account"] #~~->EditorGroup:Model~~
MAPPINGS['news'] = MAPPINGS["account"]    #~~->News:Model~~
MAPPINGS['lock'] = MAPPINGS["account"]    #~~->Lock:Model~~
MAPPINGS['provenance'] = MAPPINGS["account"]    #~~->Provenance:Model~~
MAPPINGS['preserve'] = MAPPINGS["account"]    #~~->Preservation:Model~~
MAPPINGS['notification'] = MAPPINGS["account"]    #~~->Notification:Model~~

#########################################
# Query Routes
# ~~->Query:WebRoute~~

QUERY_ROUTE = {
    "query" : {
        # ~~->PublicJournalQuery:Endpoint~~
        "journal" : {
            "auth" : False,
            "role" : None,
            "query_validator" : "public_query_validator",
            "query_filters" : ["only_in_doaj", "last_update_fallback"],
            "result_filters" : ["public_result_filter"],
            "dao" : "portality.models.Journal", # ~~->Journal:Model~~
            "required_parameters" : {"ref" : ["ssw", "public_journal", "subject_page"]}
        },
        # ~~->PublicArticleQuery:Endpoint~~
        "article" : {
            "auth" : False,
            "role" : None,
            "query_validator" : "public_query_validator",
            "query_filters" : ["only_in_doaj"],
            "result_filters" : ["public_result_filter"],
            "dao" : "portality.models.Article", # ~~->Article:Model~~
            "required_parameters" : {"ref" : ["public_article", "toc", "subject_page"]}
        },
        # back-compat for fixed query widget
        # ~~->PublicJournalArticleQuery:Endpoint~~
        "journal,article" : {
            "auth" : False,
            "role" : None,
            "query_validator" : "public_query_validator",
            "query_filters" : ["only_in_doaj", "strip_facets", "es_type_fix"],
            "result_filters" : ["public_result_filter", "add_fqw_facets", "fqw_back_compat"],
            "dao" : "portality.models.JournalArticle",  # ~~->JournalArticle:Model~~
            "required_parameters" : {"ref" : ["fqw"]}
        }
    },
    "publisher_query" : {
        # ~~->PublisherJournalQuery:Endpoint~~
        "journal" : {
            "auth" : True,
            "role" : "publisher",
            "query_filters" : ["owner", "only_in_doaj"],
            "result_filters" : ["publisher_result_filter"],
            "dao" : "portality.models.Journal"  # ~~->Journal:Model~~
        },
        # ~~->PublisherApplicationQuery:Endpoint~~
        "applications" : {
            "auth" : True,
            "role" : "publisher",
            "query_filters" : ["owner", "not_update_request"],
            "result_filters" : ["publisher_result_filter"],
            "dao" : "portality.models.AllPublisherApplications" # ~~->AllPublisherApplications:Model~~
        },
        # ~~->PublisherUpdateRequestsQuery:Endpoint~~
        "update_requests" : {
            "auth" : True,
            "role" : "publisher",
            "query_filters" : ["owner", "update_request"],
            "result_filters" : ["publisher_result_filter"],
            "dao" : "portality.models.Application"  # ~~->Application:Model~~
        }
    },
    "admin_query" : {
        # ~~->AdminJournalQuery:Endpoint~~
        "journal" : {
            "auth" : True,
            "role" : "admin",
            "dao" : "portality.models.Journal"   # ~~->Journal:Model~~
        },
        # ~~->AdminApplicationQuery:Endpoint~~
        "suggestion" : {
            "auth" : True,
            "role" : "admin",
            "query_filters" : ["not_update_request"],
            "dao" : "portality.models.Application"    # ~~->Application:Model~~
        },
        # ~~->AdminUpdateRequestQuery:Endpoint~~
        "update_requests": {
            "auth": True,
            "role": "admin",
            "query_filters" : ["update_request"],
            "dao": "portality.models.Application"  # ~~->Application:Model~~
        },
        # ~~->AdminEditorGroupQuery:Endpoint~~
        "editor,group" : {
            "auth" : True,
            "role" : "admin",
            "dao" : "portality.models.EditorGroup"   # ~~->EditorGroup:Model~~
        },
        # ~~->AdminAccountQuery:Endpoint~~
        "account" : {
            "auth" : True,
            "role" : "admin",
            "dao" : "portality.models.Account"   # ~~->Account:Model~~
        },
        # ~~->AdminJournalArticleQuery:Endpoint~~
        "journal,article" : {
            "auth" : True,
            "role" : "admin",
            "dao" : "portality.models.search.JournalArticle"     # ~~->JournalArticle:Model~~
        },
        # ~~->AdminBackgroundJobQuery:Endpoint~~
        "background,job" : {
            "auth" : True,
            "role" : "admin",
            "dao" : "portality.models.BackgroundJob"     # ~~->BackgroundJob:Model~~
        },
        # ~~->APINotificationQuery:Endpoint~~
        "notifications" : {
            "auth" : False,
            "role" : "admin",
            "dao" : "portality.models.Notification", # ~~->Notification:Model~~
            "required_parameters" : None
        }
    },
    "associate_query" : {
        # ~~->AssEdJournalQuery:Endpoint~~
        "journal" : {
            "auth" : True,
            "role" : "associate_editor",
            "query_filters" : ["associate"],
            "dao" : "portality.models.Journal"  # ~~->Journal:Model~~
        },
        # ~~->AssEdApplicationQuery:Endpoint~~
        "suggestion" : {
            "auth" : True,
            "role" : "associate_editor",
            "query_filters" : ["associate"],
            "dao" : "portality.models.Application"  # ~~->Application:Model~~
        }
    },
    "editor_query" : {
        # ~~->EditorJournalQuery:Endpoint~~
        "journal" : {
            "auth" : True,
            "role" : "editor",
            "query_filters" : ["editor"],
            "dao" : "portality.models.Journal"  # ~~->Journal:Model~~
        },
        # ~~->EditorApplicationQuery:Endpoint~~
        "suggestion" : {
            "auth" : True,
            "role" : "editor",
            "query_filters" : ["editor"],
            "dao" : "portality.models.Application"  # ~~->Application:Model~~
        }
    },
    "api_query" : {
        # ~~->APIArticleQuery:Endpoint~~
        "article" : {
            "auth" : False,
            "role" : None,
            "query_filters" : ["only_in_doaj", "public_source"],
            "dao" : "portality.models.Article", # ~~->Article:Model~~
            "required_parameters" : None,
            "keepalive" : "10m"
        },
        # ~~->APIJournalQuery:Endpoint~~
        "journal" : {
            "auth" : False,
            "role" : None,
            "query_filters" : ["only_in_doaj", "public_source"],
            "dao" : "portality.models.Journal", # ~~->Journal:Model~~
            "required_parameters" : None
        },
        # ~~->APIApplicationQuery:Endpoint~~
        "application" : {
            "auth" : True,
            "role" : None,
            "query_filters" : ["owner", "private_source"],
            "dao" : "portality.models.Suggestion",  # ~~->Application:Model~~
            "required_parameters" : None
        }
    },
    "dashboard_query": {
        # ~~->APINotificationQuery:Endpoint~~
        "notifications" : {
            "auth" : False,
            "role" : "read_notifications",
            "query_filters" : ["who_current_user"], # ~~-> WhoCurrentUser:Query
            "dao" : "portality.models.Notification", # ~~->Notification:Model~~
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
    "strip_facets" : "portality.lib.query_filters.strip_facets",
    "es_type_fix" : "portality.lib.query_filters.es_type_fix",
    "last_update_fallback" : "portality.lib.query_filters.last_update_fallback",
    "not_update_request" : "portality.lib.query_filters.not_update_request",
    "who_current_user" : "portality.lib.query_filters.who_current_user",    # ~~-> WhoCurrentUser:Query ~~

    # result filters
    "public_result_filter": "portality.lib.query_filters.public_result_filter",
    "publisher_result_filter": "portality.lib.query_filters.publisher_result_filter",
    "add_fqw_facets" : "portality.lib.query_filters.add_fqw_facets",
    "fqw_back_compat" : "portality.lib.query_filters.fqw_back_compat",

    # source filters
    "private_source": "portality.lib.query_filters.private_source",
    "public_source": "portality.lib.query_filters.public_source",
}

####################################################
# Autocomplete

# ~~->BibJSON:Model~~
AUTOCOMPLETE_ADVANCED_FIELD_MAPS = {
    "bibjson.publisher.name" : "index.publisher_ac",
    "bibjson.institution.name" : "index.institution_ac"
}

####################################################
# Application Form
# ~~->ApplicationForm:Feature~~

# save the public application form as a draft every 60 seconds
PUBLIC_FORM_AUTOSAVE = 60000


############################################
# Atom Feed
# ~~->AtomFeed:Feature~~

FEED_TITLE = "DOAJ Recent Journals Added"

# Maximum number of feed entries to be given in a single response.  If this is omitted, it will
# default to 20
MAX_FEED_ENTRIES = 100

# Maximum age of feed entries (in seconds) (default value here is 30 days).
MAX_FEED_ENTRY_AGE = 2592000

# Licensing terms for feed content
# ~~->SiteLicence:Content~~
FEED_LICENCE = "(c) DOAJ 2013. CC BY-SA."

# name of the feed generator (goes in the atom:generator element)
FEED_GENERATOR = "CottageLabs feed generator"

# Larger image to use as the logo for all of the feeds
# ~~->Favicon:Content~~
FEED_LOGO = "https://doaj.org/static/doaj/images/favicon.ico"


###########################################
# OAI-PMH SETTINGS
# ~~->OAIPMH:Feature~~

# ~~->OAIAriticleXML:Crosswalk~~
# ~~->OAIJournalXML:Crosswalk~~
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


##########################################
# Article XML configuration

# paths to schema files to validate incoming documents against for the various
# crosswalks available
# ~~->CrossrefXML:Schema~~
# ~~->DOAJArticleXML:Schema~~
SCHEMAS = {
    "doaj": os.path.join(BASE_FILE_PATH, "static", "doaj", "doajArticles.xsd"),
    "crossref442": os.path.join(BASE_FILE_PATH, "static", "crossref", "crossref4.4.2.xsd"),
    "crossref531": os.path.join(BASE_FILE_PATH, "static", "crossref", "crossref5.3.1.xsd")
}

# placeholders for the loaded schemas
DOAJ_SCHEMA = None
CROSSREF442_SCHEMA = None
CROSSREF531_SCHEMA = None
LOAD_CROSSREF_THREAD = None

# mapping of format names to modules which implement the crosswalks
# ~~->DOAJArticleXML:Crosswalk~~
# ~~->CrossrefXML:Crosswalk~~
ARTICLE_CROSSWALKS = {
    "doaj": "portality.crosswalks.article_doaj_xml.DOAJXWalk",
    "crossref442": "portality.crosswalks.article_crossref_xml.CrossrefXWalk442",
    "crossref531": "portality.crosswalks.article_crossref_xml.CrossrefXWalk531"
}

# maximum size of files that can be provided by-reference (the default value is 250Mb)
MAX_REMOTE_SIZE = 262144000

#################################################
# Cache settings
# ~~->Cache:Feature~~

# number of seconds site statistics should be considered fresh
# 1800s = 30mins
SITE_STATISTICS_TIMEOUT = 1800

# directory into which to put files which are cached (e.g. the csv)
CACHE_DIR = os.path.join(ROOT_DIR, "cache")

# Article and Journal History directories - they should be different
# ~~->ArticleHistory:Feature~~
# ~~->JournalHistory:Feature~~
ARTICLE_HISTORY_DIR = os.path.join(ROOT_DIR, "history", "article")
JOURNAL_HISTORY_DIR = os.path.join(ROOT_DIR, "history", "journal")


#################################################
# Sitemap settings
# ~~->Sitemap:Feature~~

# approximate rate of change of the Table of Contents for journals
TOC_CHANGEFREQ = "monthly"



##################################################
# News feed settings
# ~~->News:Feature~~

BLOG_URL = "http://doajournals.wordpress.com/"

BLOG_FEED_URL = "http://doajournals.wordpress.com/feed/atom/"

FRONT_PAGE_NEWS_ITEMS = 6

NEWS_PAGE_NEWS_ITEMS = 20


##################################################
# Edit Lock settings
# ~~->Lock:Feature~~

# amount of time loading an editable page locks it for, in seconds.
EDIT_LOCK_TIMEOUT = 1200

# amount of time a background task can lock a resource for, in seconds
BACKGROUND_TASK_LOCK_TIMEOUT = 3600


###############################################
# Bit.ly configuration
# ~~->Bitly:ExternalService~~

# bit,ly api shortening service
BITLY_SHORTENING_API_URL = "https://api-ssl.bitly.com/v4/shorten"

# bitly oauth token
# ENTER YOUR OWN TOKEN IN APPROPRIATE .cfg FILE
BITLY_OAUTH_TOKEN = ""

###############################################
# Date handling
#
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

#################################################
# API configuration
# ~~->API:Feature~~
# ~~->APISearch:Feature~~

# maximum number of records to return per page
DISCOVERY_MAX_PAGE_SIZE = 100

# maximum number of records to return in total (a request for a page starting beyond this number will fail)
DISCOVERY_MAX_RECORDS_SIZE = 1000

# ~~->ArticleBibJSON:Model~~
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

# ~~->JournalBibJSON:Model~~
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


######################################################
# Hotjar configuration
# ~~->Hotjar:ExternalService~~

# hotjar id - only activate this in production
HOTJAR_ID = ""


######################################################
# Google Analytics configuration
# specify in environment .cfg file - avoids sending live analytics
# events from test and dev environments
# ~~->GoogleAnalytics:ExternalService~~

GOOGLE_ANALYTICS_ID = ''

# Where to put the google analytics logs
GOOGLE_ANALTYICS_LOG_DIR = None

# Google Analytics custom dimensions. These are configured in the GA interface.
GA_DIMENSIONS = {
    'oai_res_id': 'dimension1',                                                                    # In GA as OAI:Record
}

# GA for OAI-PMH
# ~~-> OAIPMH:Feature~~
GA_CATEGORY_OAI = 'OAI-PMH'

# GA for Atom
# ~~-> Atom:Feature~~
GA_CATEGORY_ATOM = 'Atom'
GA_ACTION_ACTION = 'Feed request'

# GA for JournalCSV
# ~~-> JournalCSV:Feature~~
GA_CATEGORY_JOURNALCSV = 'JournalCSV'
GA_ACTION_JOURNALCSV = 'Download'

# GA for OpenURL
# ~~->OpenURL:Feature~~
GA_CATEGORY_OPENURL = 'OpenURL'

# GA for API
# ~~-> API:Feature~~
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
# ~~->FixedQueryWidget:Feature~~
GA_CATEGORY_FQW = 'FQW'
GA_ACTION_FQW = 'Hit'

#####################################################
# Anonymised data export (for dev) configuration
# ~~->AnonExport:Feature~~

ANON_SALT = 'changeme'

# ========================================
# Quick Reject Feature Config
# ~~->QuickReject:Feature~~

QUICK_REJECT_REASONS = [
    "The journal has not published enough research content to qualify for DOAJ inclusion.",
    "The ISSN is incorrect, provisional or not registered with issn.org.",
    "The URL(s) provided in the application do not work.",
    "The journal is already in DOAJ.",
    "The journal is not Open Access.",
    "The journal title in the application and/or website does not match the title at issn.org.",
    "The application has incorrect answers or the URLs given do not provide the required information.",
    "This application is a duplicate.",
    "The full-text articles are not available article by article with individual links.",
    "The information in the journal implies that it does not employ a fair & robust peer review process.",
    "The journal or publisher has been previously rejected or removed from DOAJ.",
    "The journal's copyright policy is not available or unclear.",
    "The journal's licensing policy is not available or unclear.",
    "The information about the journal is in different languages.",
    "The information about the journal is not the same in all languages.",
    "The journal makes a false claim to be indexed in DOAJ or other databases or displays non-standard Impact Factors.",
    "The journal does not employ good publishing practices."
]

MINIMAL_OA_START_DATE = 1900


#############################################
## Harvester Configuration
# ~~->Harvester:Feature~~

## Configuration options for the DOAJ API Client

## EPMC Client configuration
# ~~-> EPMC:ExternalService~~
EPMC_REST_API = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
EPMC_TARGET_VERSION = "6.6"     # doc here: https://europepmc.org/docs/Europe_PMC_RESTful_Release_Notes.pdf
EPMC_HARVESTER_THROTTLE = 0.2

# General harvester configuration
HARVESTERS = [
    "portality.tasks.harvester_helpers.epmc.epmc_harvester.EPMCHarvester"
]

INITIAL_HARVEST_DATE = "2015-12-01T00:00:00Z"

# List of account ids to harvest from.  MUST NOT be checked into the repo, put these
# in the local.cfg instead
HARVEST_ACCOUNTS = []

# Amount of time a harvester record is allowed to be in "queued" or "processing" state before we
# assume it's a zombie, and ignore it
HARVESTER_ZOMBIE_AGE = 604800

#######################################################
# ReCAPTCHA configuration
# ~~->ReCAPTCHA:ExternalService

#Recaptcha test keys, should be overridden in dev.cfg by the keys obtained from Google ReCaptcha v2
RECAPTCHA_ENABLE = True
RECAPTCHA_SITE_KEY = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
RECAPTCHA_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"

#######################################################
# Preservation configuration
# ~~->Preservation:Feature
PRESERVATION_URL = "http://PresevatinURL"
PRESERVATION_USERNAME = "user_name"
PRESERVATION_PASSWD = "password"
PRESERVATION_COLLECTION = {}


#########################################################
# Background tasks --- anon export
TASKS_ANON_EXPORT_CLEAN = False
TASKS_ANON_EXPORT_LIMIT = None
TASKS_ANON_EXPORT_BATCH_SIZE = 100000
TASKS_ANON_EXPORT_SCROLL_TIMEOUT = '5m'

#########################################################
# Background tasks --- old_data_cleanup
TASK_DATA_RETENTION_DAYS = {
    "notification": 180, # ~~-> Notifications:Feature ~~
    "background_job": 180, # ~~-> BackgroundJobs:Feature ~~
}

########################################
# Editorial Dashboard - set to-do list size
TODO_LIST_SIZE = 48

#######################################################
# Plausible analytics
# root url of plausible
PLAUSIBLE_URL = "https://plausible.io"
PLAUSIBLE_JS_URL = PLAUSIBLE_URL + "/js/script.outbound-links.file-downloads.js"
PLAUSIBLE_API_URL = PLAUSIBLE_URL + "/api/event"
# site name / domain name that used to register in plausible
PLAUSIBLE_SITE_NAME = BASE_DOMAIN
PLAUSIBLE_LOG_DIR = None

#########################################################
# Background tasks --- monitor_bgjobs
TASKS_MONITOR_BGJOBS_TO = ["helpdesk@doaj.org",]
TASKS_MONITOR_BGJOBS_FROM = "helpdesk@doaj.org"


##################################
# Background monitor
# ~~->BackgroundMonitor:Feature~~

# Configures the age of the last completed job on the queue before the queue is marked as unstable
# (in seconds)
BG_MONITOR_LAST_COMPLETED = {
    'main_queue': 7200,     # 2 hours
    'long_running': 93600,  # 26 hours
}

# Configures the monitoring period and the allowed number of errors in that period before a queue is marked
# as unstable
BG_MONITOR_ERRORS_CONFIG = {
    # Main queue
    'journal_csv': {
        'check_sec': 3600,  # 1 hour, time period between scheduled runs
        'allowed_num_err': 0,
    },
    'ingest_articles': {
        'check_sec': 86400,
        'allowed_num_err': 0
    },

    # Long running
    'harvest': {
        'check_sec': 86400,
        'allowed_num_err': 0,
    },
    'public_data_dump': {
        'check_sec': 86400 * 7,
        'allowed_num_err': 0
    }
}

# Configures the total number of queued items and the age of the oldest of those queued items allowed
# before the queue is marked as unstable.  This is provided by type, so we can monitor all types separately
BG_MONITOR_QUEUED_CONFIG = {
    # Main queue
    'journal_csv': {
        'total': 2,
        'oldest': 1200,     # 20 mins
    },
    'ingest_articles': {
        'total': 250,
        'oldest': 86400
    },

    # Long running
    'harvest': {
        'total': 1,
        'oldest': 86400
    },
    'public_data_dump': {
        'total': 1,
        'oldest': 86400
    }
}

##################################################
## Public data dump settings

# how long should the temporary URL for public data dumps last
PUBLIC_DATA_DUMP_URL_TIMEOUT = 3600

##################################################
# Pages under maintenance

PRESERVATION_PAGE_UNDER_MAINTENANCE = False
