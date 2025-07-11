"""
~~AppSettings:Config~~
"""
import os
from portality import constants
from portality.lib import paths

###########################################
# Application Version information
# ~~->API:Feature~~

DOAJ_VERSION = "8.3.3"
API_VERSION = "4.0.0"

######################################
# Deployment configuration

HOST = '0.0.0.0'
DEBUG = False
DEBUG_DEV_LOG = False  # show all log of each module
PORT = 5004
SSL = True
VALID_ENVIRONMENTS = ['dev', 'test', 'staging', 'production', 'harvester']
CMS_BUILD_ASSETS_ON_STARTUP = False
# Cookies security
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_SECURE = True
REMEMBER_COOKIE_SECURE = True

####################################
# Testdrive for setting up the test environment.
# CAUTION - this can modify the index so should NEVER be used in production!
TESTDRIVE_ENABLED = False

####################################
# Debug Mode

# PyCharm debug settings
DEBUG_PYCHARM = False  # do not try to connect to the PyCharm debugger by default
DEBUG_PYCHARM_SERVER = 'localhost'
DEBUG_PYCHARM_PORT = 6000

# ~~->DebugToolbar:Framework~~
DEBUG_TB_TEMPLATE_EDITOR_ENABLED = True
DEBUG_TB_INTERCEPT_REDIRECTS = False

# set to True to enable the env list panel in the debug toolbar
DEBUG_TB_ENV_LIST_ENABLED = False

#######################################
# Elasticsearch configuration
# ~~->Elasticsearch:Technology

# elasticsearch settings # TODO: changing from single host / esprit to multi host on ES & correct the default
ELASTICSEARCH_HOSTS = [{'host': 'localhost', 'port': 9200}, {'host': 'localhost', 'port': 9201}]
ELASTIC_SEARCH_VERIFY_CERTS = True  # Verify the SSL certificate of the ES host.  Set to False in dev.cfg to avoid having to configure your local certificates

# 2 sets of elasticsearch DB settings - index-per-project and index-per-type. Keep both for now so we can migrate.
# e.g. host:port/index/type/id
ELASTIC_SEARCH_DB = "doaj"
ELASTIC_SEARCH_TEST_DB = "doajtest"

# e.g. host:port/type/doc/id
ELASTIC_SEARCH_INDEX_PER_TYPE = True
INDEX_PER_TYPE_SUBSTITUTE = '_doc'  # Migrated from esprit
ELASTIC_SEARCH_DB_PREFIX = "doaj-"  # note: include the separator
ELASTIC_SEARCH_TEST_DB_PREFIX = "doajtest-"

INITIALISE_INDEX = True  # whether or not to try creating the index and required index types on startup
ELASTIC_SEARCH_VERSION = "7.10.2"
ELASTIC_SEARCH_SNAPSHOT_REPOSITORY = None
ELASTIC_SEARCH_SNAPSHOT_TTL = 366

ES_TERMS_LIMIT = 1024
ELASTICSEARCH_REQ_TIMEOUT = 20  # Seconds - used in core.py for whole ES connection request timeout
ES_READ_TIMEOUT = '2m'  # Minutes - used in DAO for searches

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

# Process events immediately/synchronously
EVENT_SEND_FUNCTION = "portality.events.shortcircuit.send_event"

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
FEATURES = ['api1', 'api2', 'api3', 'api4']
VALID_FEATURES = ['api1', 'api2', 'api3', 'api4']

########################################
# File Path and URL Path settings

# root of the git repo
ROOT_DIR = paths.rel2abs(__file__, "..")

# base path, to the directory where this settings file lives
BASE_FILE_PATH = paths.abs_dir_path(__file__)

BASE_URL = "https://doaj.org"
if BASE_URL.startswith('https://'):
    BASE_DOMAIN = BASE_URL[8:]
elif BASE_URL.startswith('http://'):
    BASE_DOMAIN = BASE_URL[7:]
else:
    BASE_DOMAIN = BASE_URL

# ~~->API:Feature~~
BASE_API_URL = "https://doaj.org/api/"
API_CURRENT_BLUEPRINT_NAME = "api_v4"  # change if upgrading API to new version and creating new view
CURRENT_API_MAJOR_VERSION = "4"

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
UPLOAD_DIR = os.path.join(ROOT_DIR, "upload")
UPLOAD_ASYNC_DIR = os.path.join(ROOT_DIR, "upload_async")
FAILED_ARTICLE_DIR = os.path.join(ROOT_DIR, "failed_articles")

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
STORE_EXPORT_CONTAINER = "doaj-export-placeholder"

# S3 credentials for relevant scopes
# ~~->S3:Technology~~
STORE_S3_SCOPES = {
    "anon_data": {
        "aws_access_key_id": "put this in your dev/test/production.cfg",
        "aws_secret_access_key": "put this in your dev/test/production.cfg"
    },
    "cache": {
        "aws_access_key_id": "put this in your dev/test/production.cfg",
        "aws_secret_access_key": "put this in your dev/test/production.cfg"
    },
    # Used by the api_export script to dump data from the api
    constants.STORE__SCOPE__PUBLIC_DATA_DUMP: {
        "aws_access_key_id": "put this in your dev/test/production.cfg",
        "aws_secret_access_key": "put this in your dev/test/production.cfg"
    },
    # Used to store harvester run logs to S3
    "harvester": {
        "aws_access_key_id": "put this in your dev/test/production.cfg",
        "aws_secret_access_key": "put this in your dev/test/production.cfg"
    },
    # Used to store the admin-generated CSV reports
    "export": {
        "aws_access_key_id": "put this in your dev/test/production.cfg",
        "aws_secret_access_key": "put this in your dev/test/production.cfg"
    }
}

STORE_S3_MULTIPART_THRESHOLD = 5 * 1024 ** 3  # 5GB

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
# ~~->GitHub:ExternalService~~
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
SITE_NOTE_SLEEP = 259200  # every 3 days
SITE_NOTE_COOKIE_VALUE = "You have seen our most recent site wide announcement"

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

# "api" top-level role is added to all accounts on creation; it can be revoked per account by removal of the role.
TOP_LEVEL_ROLES = [
    "admin",
    "publisher",
    "editor",
    "associate_editor",
    "api",
    "ultra_bulk_delete",
    "preservation",
    constants.ROLE_PUBLIC_DATA_DUMP,
    constants.ROLE_PUBLISHER_JOURNAL_CSV,
    constants.ROLE_ADMIN_REPORT_WITH_NOTES
]

ROLE_MAP = {
    "editor": [
        "associate_editor",  # note, these don't cascade, so we still need to list all the low-level roles
        "edit_journal",
        "edit_suggestion",
        "edit_application",  # todo: switchover from suggestion to application
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

MAN_ED_IDLE_WEEKS = 4  # weeks before an application is considered reminder-worthy
ED_IDLE_WEEKS = 3  # weeks before the editor is warned about idle applications in their group
ASSOC_ED_IDLE_DAYS = 10
ASSOC_ED_IDLE_WEEKS = 3

# Which statuses the notification queries should be filtered to show
# ~~-> ApplicationStatuses:Config~~
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
APP_MACHINES_INTERNAL_IPS = [HOST + ':' + str(PORT)]  # This should be set in production.cfg (or dev.cfg etc)

###########################################
# Background Jobs settings
# ~~->Huey:Technology~~
# ~~->Redis:Technology~~
# ~~->BackgroundTasks:Feature~~

# huey/redis settings
REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
HUEY_IMMEDIATE = False
HUEY_ASYNC_DELAY = 10

# Crontab for never running a job - February 31st (use to disable tasks)
CRON_NEVER = {"month": "2", "day": "31", "day_of_week": "*", "hour": "*", "minute": "*"}

# Additional Logging for scheduled JournalCSV
EXTRA_JOURNALCSV_LOGGING = False

#  Crontab schedules must be for unique times to avoid delays due to perceived race conditions
HUEY_SCHEDULE = {
    "sitemap": {"month": "*", "day": "*", "day_of_week": "*", "hour": "8", "minute": "0"},
    "reporting": {"month": "*", "day": "1", "day_of_week": "*", "hour": "0", "minute": "0"},
    "journal_csv": {"month": "*", "day": "*", "day_of_week": "*", "hour": "*", "minute": "20"},
    "read_news": {"month": "*", "day": "*", "day_of_week": "*", "hour": "*", "minute": "30"},
    "article_cleanup_sync": {"month": "*", "day": "2", "day_of_week": "*", "hour": "0", "minute": "0"},
    "async_workflow_notifications": {"month": "*", "day": "*", "day_of_week": "1", "hour": "5", "minute": "0"},
    "request_es_backup": {"month": "*", "day": "*", "day_of_week": "*", "hour": "6", "minute": "0"},
    "check_latest_es_backup": {"month": "*", "day": "*", "day_of_week": "*", "hour": "9", "minute": "0"},
    "prune_es_backups": {"month": "*", "day": "*", "day_of_week": "*", "hour": "9", "minute": "15"},
    "public_data_dump": {"month": "*", "day": "*/6", "day_of_week": "*", "hour": "10", "minute": "0"},
    "harvest": {"month": "*", "day": "*", "day_of_week": "*", "hour": "5", "minute": "30"},
    "anon_export": {"month": "*", "day": "10", "day_of_week": "*", "hour": "1", "minute": "10"},
    "old_data_cleanup": {"month": "*", "day": "12", "day_of_week": "*", "hour": "6", "minute": "30"},
    "monitor_bgjobs": {"month": "*", "day": "*/6", "day_of_week": "*", "hour": "10", "minute": "0"},
    "find_discontinued_soon": {"month": "*", "day": "*", "day_of_week": "*", "hour": "0", "minute": "3"},
    "datalog_journal_added_update": {"month": "*", "day": "*", "day_of_week": "*", "hour": "4", "minute": "30"}
}


HUEY_TASKS = {
    "ingest_articles": {"retries": 10, "retry_delay": 15},
    "preserve": {"retries": 0, "retry_delay": 15},
    "application_autochecks": {"retries": 0, "retry_delay": 15},
    "journal_autochecks": {"retries": 0, "retry_delay": 15}
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
    "portality.models.background.BackgroundJob", # ~~-> BackgroundJob:Model~~
    "portality.models.autocheck.Autocheck", # ~~-> Autocheck:Model~~
    "portality.models.export.Export", # ~~-> Export:Model~~
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
                # "index": False,
                "store": True
            }
        }
    },
    "str": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
                # "index": False,
                "store": True
            }
        }
    },
    "unicode_upper": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
                # "index": False,
                "store": True
            }
        }
    },
    "unicode_lower": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
                # "index": False,
                "store": True
            }
        }
    },
    "isolang": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
                # "index": False,
                "store": True
            }
        }
    },
    "isolang_2letter_strict": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
                # "index": False,
                "store": True
            }
        }
    },
    "isolang_2letter_lax": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
                # "index": False,
                "store": True
            }
        }
    },
    "country_code": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
                # "index": False,
                "store": True
            }
        }
    },
    "currency_code_strict": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
                # "index": False,
                "store": True
            }
        }
    },
    "currency_code_lax": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
                # "index": False,
                "store": True
            }
        }
    },
    "issn": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
                # "index": False,
                "store": True
            }
        }
    },
    "url": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
                # "index": False,
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

# Extension Map from dataobj coercion declarations to ES mappings.
# This is useful when some extensions required for some objects additional to defaults.
# ~~->DataObj:Library~~
# ~~->Seamless:Library~~
DATAOBJ_TO_MAPPING_COPY_TO_EXTENSIONS = {
    "unicode": {"copy_to": ["all_meta"]},
    "str": {"copy_to": ["all_meta"]},
    "unicode_upper": {"copy_to": ["all_meta"]},
    "unicode_lower": {"copy_to": ["all_meta"]},
    "issn": {"copy_to": ["all_meta"]},
    "url": {"copy_to": ["all_meta"]}
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
                            # "normalizer": "lowercase"
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
    'account': {  # ~~->Account:Model~~
        # 'aliases': {
        #     'account': {}
        # },
        'mappings': DEFAULT_DYNAMIC_MAPPING,
        'settings': DEFAULT_INDEX_SETTINGS
    }
}

MAPPINGS['article'] = MAPPINGS["account"]  # ~~->Article:Model~~
MAPPINGS['upload'] = MAPPINGS["account"]  # ~~->Upload:Model~~
MAPPINGS['bulk_articles'] = MAPPINGS["account"]  # ~~->BulkArticles:Model~~
MAPPINGS['cache'] = MAPPINGS["account"]  # ~~->Cache:Model~~
MAPPINGS['lcc'] = MAPPINGS["account"]  # ~~->LCC:Model~~
MAPPINGS['editor_group'] = MAPPINGS["account"]  # ~~->EditorGroup:Model~~
MAPPINGS['news'] = MAPPINGS["account"]  # ~~->News:Model~~
MAPPINGS['lock'] = MAPPINGS["account"]  # ~~->Lock:Model~~
MAPPINGS['provenance'] = MAPPINGS["account"]  # ~~->Provenance:Model~~
MAPPINGS['preserve'] = MAPPINGS["account"]  # ~~->Preservation:Model~~
MAPPINGS['notification'] = MAPPINGS["account"]  # ~~->Notification:Model~~
MAPPINGS['article_tombstone'] = MAPPINGS["account"]  # ~~->ArticleTombstone:Model~~
MAPPINGS['shortened_url'] = MAPPINGS["account"]    #~~->URLShortener:Model~~

#########################################
# Query Routes
# ~~->Query:WebRoute~~

QUERY_ROUTE = {
    "query": {
        # ~~->PublicJournalQuery:Endpoint~~
        "journal": {
            "auth": False,
            "role": None,
            "query_validators": ["non_public_fields_validator", "public_query_validator"],
            "query_filters": ["only_in_doaj", "last_update_fallback", "search_all_meta"],
            "result_filters": ["public_result_filter"],
            "dao": "portality.models.Journal",  # ~~->Journal:Model~~
            "required_parameters": {"ref": ["ssw", "public_journal", "subject_page"]}
        },
        # ~~->PublicArticleQuery:Endpoint~~
        "article": {
            "auth": False,
            "role": None,
            "query_validators": ["non_public_fields_validator", "public_query_validator"],
            "query_filters": ["only_in_doaj"],
            "result_filters": ["public_result_filter"],
            "dao": "portality.models.Article",  # ~~->Article:Model~~
            "required_parameters": {"ref": ["public_article", "toc", "subject_page"]}
        },
        # back-compat for fixed query widget
        # ~~->PublicJournalArticleQuery:Endpoint~~
        "journal,article": {
            "auth": False,
            "role": None,
            "query_validators": ["non_public_fields_validator", "public_query_validator"],
            "query_filters": ["only_in_doaj", "strip_facets", "es_type_fix", "journal_article_filter"],
            "result_filters": ["public_result_filter", "add_fqw_facets", "fqw_back_compat"],
            "dao": "portality.models.JournalArticle",  # ~~->JournalArticle:Model~~
            "required_parameters": {"ref": ["fqw"]}
        }
    },
    "publisher_query": {
        # ~~->PublisherJournalQuery:Endpoint~~
        "journal": {
            "auth": True,
            "role": "publisher",
            "query_validators": ["non_public_fields_validator"],
            "query_filters": ["owner", "only_in_doaj", "search_all_meta"],
            "result_filters": ["publisher_result_filter"],
            "dao": "portality.models.Journal"  # ~~->Journal:Model~~
        },
        # ~~->PublisherApplicationQuery:Endpoint~~
        "applications": {
            "auth": True,
            "role": "publisher",
            "query_validators": ["non_public_fields_validator"],
            "query_filters": ["owner", "not_update_request", "search_all_meta"],
            "result_filters": ["publisher_result_filter"],
            "dao": "portality.models.AllPublisherApplications"  # ~~->AllPublisherApplications:Model~~
        },
        # ~~->PublisherUpdateRequestsQuery:Endpoint~~
        "update_requests": {
            "auth": True,
            "role": "publisher",
            "query_validators": ["non_public_fields_validator"],
            "query_filters": ["owner", "update_request", "search_all_meta"],
            "result_filters": ["publisher_result_filter"],
            "dao": "portality.models.Application"  # ~~->Application:Model~~
        }
    },
    "admin_query": {
        # ~~->AdminJournalQuery:Endpoint~~
        "journal": {
            "auth": True,
            "role": "admin",
            "dao": "portality.models.Journal"  # ~~->Journal:Model~~
        },
        # ~~->AdminApplicationQuery:Endpoint~~
        "suggestion": {
            "auth": True,
            "role": "admin",
            "query_filters": ["not_update_request"],
            "dao": "portality.models.Application"  # ~~->Application:Model~~
        },
        # ~~->AdminUpdateRequestQuery:Endpoint~~
        "update_requests": {
            "auth": True,
            "role": "admin",
            "query_filters": ["update_request"],
            "dao": "portality.models.Application"  # ~~->Application:Model~~
        },
        # ~~->AdminEditorGroupQuery:Endpoint~~
        "editor,group": {
            "auth": True,
            "role": "admin",
            "dao": "portality.models.EditorGroup"  # ~~->EditorGroup:Model~~
        },
        # ~~->AdminAccountQuery:Endpoint~~
        "account": {
            "auth": True,
            "role": "admin",
            "dao": "portality.models.Account"  # ~~->Account:Model~~
        },
        # ~~->AdminJournalArticleQuery:Endpoint~~
        "journal,article": {
            "auth": True,
            "role": "admin",
            "dao": "portality.models.search.JournalArticle"  # ~~->JournalArticle:Model~~
        },
        # ~~->AdminBackgroundJobQuery:Endpoint~~
        "background,job": {
            "auth": True,
            "role": "admin",
            "dao": "portality.models.BackgroundJob"  # ~~->BackgroundJob:Model~~
        },
        # ~~->APINotificationQuery:Endpoint~~
        "notifications": {
            "auth": False,
            "role": "admin",
            "dao": "portality.models.Notification",  # ~~->Notification:Model~~
            "required_parameters": None
        },
        "reports": {
            "auth": True,
            "role": "admin",
            "dao": "portality.models.Export"
        }
    },
    "associate_query": {
        # ~~->AssEdJournalQuery:Endpoint~~
        "journal": {
            "auth": True,
            "role": "associate_editor",
            "query_validators": ["non_public_fields_validator"],
            "query_filters": ["associate", "search_all_meta"],
            "dao": "portality.models.Journal"  # ~~->Journal:Model~~
        },
        # ~~->AssEdApplicationQuery:Endpoint~~
        "suggestion": {
            "auth": True,
            "role": "associate_editor",
            "query_validators": ["non_public_fields_validator"],
            "query_filters": ["associate", "search_all_meta"],
            "dao": "portality.models.Application"  # ~~->Application:Model~~
        }
    },
    "editor_query": {
        # ~~->EditorJournalQuery:Endpoint~~
        "journal": {
            "auth": True,
            "role": "editor",
            "query_validators": ["non_public_fields_validator"],
            "query_filters": ["editor", "search_all_meta"],
            "dao": "portality.models.Journal"  # ~~->Journal:Model~~
        },
        # ~~->EditorApplicationQuery:Endpoint~~
        "suggestion": {
            "auth": True,
            "role": "editor",
            "query_validators": ["non_public_fields_validator"],
            "query_filters": ["editor", "search_all_meta"],
            "dao": "portality.models.Application"  # ~~->Application:Model~~
        }
    },
    "api_query": {
        # ~~->APIArticleQuery:Endpoint~~
        "article": {
            "auth": False,
            "role": None,
            "query_filters": ["only_in_doaj", "public_source"],
            "dao": "portality.models.Article",  # ~~->Article:Model~~
            "required_parameters": None,
            "keepalive": "10m"
        },
        # ~~->APIJournalQuery:Endpoint~~
        "journal": {
            "auth": False,
            "role": None,
            "query_validators": ["non_public_fields_validator"],
            "query_filters": ["only_in_doaj", "public_source", "search_all_meta"],
            "dao": "portality.models.Journal",  # ~~->Journal:Model~~
            "required_parameters": None
        },
        # ~~->APIApplicationQuery:Endpoint~~
        "application": {
            "auth": True,
            "role": None,
            "query_validators": ["non_public_fields_validator"],
            "query_filters": ["owner", "private_source", "search_all_meta"],
            "dao": "portality.models.Suggestion",  # ~~->Application:Model~~
            "required_parameters": None
        }
    },
    "dashboard_query": {
        # ~~->APINotificationQuery:Endpoint~~
        "notifications": {
            "auth": False,
            "role": "read_notifications",
            "query_filters": ["who_current_user"],  # ~~-> WhoCurrentUser:Query
            "dao": "portality.models.Notification",  # ~~->Notification:Model~~
            "required_parameters": None
        }
    }
}

QUERY_FILTERS = {
    # sanitisers
    "public_query_validator": "portality.lib.query_filters.public_query_validator",
    "non_public_fields_validator": "portality.lib.query_filters.non_public_fields_validator",

    # query filters
    "only_in_doaj": "portality.lib.query_filters.only_in_doaj",
    "owner": "portality.lib.query_filters.owner",
    "update_request": "portality.lib.query_filters.update_request",
    "associate": "portality.lib.query_filters.associate",
    "editor": "portality.lib.query_filters.editor",
    "strip_facets": "portality.lib.query_filters.strip_facets",
    "es_type_fix": "portality.lib.query_filters.es_type_fix",
    "last_update_fallback": "portality.lib.query_filters.last_update_fallback",
    "not_update_request": "portality.lib.query_filters.not_update_request",
    "who_current_user": "portality.lib.query_filters.who_current_user",  # ~~-> WhoCurrentUser:Query ~~
    "search_all_meta": "portality.lib.query_filters.search_all_meta",  # ~~-> SearchAllMeta:Query ~~
    "journal_article_filter": "portality.lib.query_filters.journal_article_filter",
    # ~~-> JournalArticleFilter:Query ~~

    # result filters
    "public_result_filter": "portality.lib.query_filters.public_result_filter",
    "publisher_result_filter": "portality.lib.query_filters.publisher_result_filter",
    "add_fqw_facets": "portality.lib.query_filters.add_fqw_facets",
    "fqw_back_compat": "portality.lib.query_filters.fqw_back_compat",

    # source filters
    "private_source": "portality.lib.query_filters.private_source",
    "public_source": "portality.lib.query_filters.public_source",
}
# Exclude the fields that doesn't want to be searched by public queries
# This is part of non_public_fields_validator.
PUBLIC_QUERY_VALIDATOR__EXCLUDED_FIELDS = [
    "admin.notes.note",
    "admin.notes.id",
    "admin.notes.author_id"
]

ADMIN_NOTES_INDEX_ONLY_FIELDS = {
    "all_meta": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
                "store": True
            }
        }
    }
}

ADMIN_NOTES_SEARCH_MAPPING = {
    "admin.notes.id": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
                "store": True
            }
        }
    },
    "admin.notes.note": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
                "store": True
            }
        }
    },
    "admin.notes.author_id": {
        "type": "text",
        "fields": {
            "exact": {
                "type": "keyword",
                "store": True
            }
        }
    }
}

####################################################
# Autocomplete

# ~~->BibJSON:Model~~
AUTOCOMPLETE_ADVANCED_FIELD_MAPS = {
    "bibjson.publisher.name": "index.publisher_ac",
    "bibjson.institution.name": "index.institution_ac"
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
FEED_LICENCE = "(c) DOAJ 2024. CC BY-SA."

# name of the feed generator (goes in the atom:generator element)
FEED_GENERATOR = "CottageLabs feed generator"

# Larger image to use as the logo for all of the feeds
# ~~->Favicon:Content~~
FEED_LOGO = "https://doaj.org/static/doaj/images/favicon.ico"

###########################################
# OAI-PMH SETTINGS
# ~~->OAIPMH:Feature~~

OAI_ADMIN_EMAIL = 'helpdesk+oai@doaj.org'

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

BLOG_URL = "https://blog.doaj.org/"

BLOG_FEED_URL = "https://blog.doaj.org/feed/"

FRONT_PAGE_NEWS_ITEMS = 4

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
# BITLY_SHORTENING_API_URL = "https://api-ssl.bitly.com/v4/shorten"

# bitly oauth token
# ENTER YOUR OWN TOKEN IN APPROPRIATE .cfg FILE
# BITLY_OAUTH_TOKEN = ""


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
    "title": "bibjson.title",
    "doi": "bibjson.identifier.id.exact",
    "issn": "index.issn.exact",
    "publisher": "bibjson.journal.publisher",
    "journal": "bibjson.journal.title",
    "abstract": "bibjson.abstract"
}

DISCOVERY_ARTICLE_SORT_SUBS = {
    "title": "index.unpunctitle.exact"
}

# ~~->JournalBibJSON:Model~~
DISCOVERY_JOURNAL_SEARCH_SUBS = {
    "title": "index.title",
    "issn": "index.issn.exact",
    "publisher": "bibjson.publisher",
    "license": "index.license.exact",
    "username": "admin.owner.exact"
}

DISCOVERY_JOURNAL_SORT_SUBS = {
    "title": "index.unpunctitle.exact",
    "issn": "index.issn.exact"
}

DISCOVERY_APPLICATION_SEARCH_SUBS = {
    "title": "index.title",
    "issn": "index.issn.exact",
    "publisher": "bibjson.publisher",
    "license": "index.license.exact"
}

DISCOVERY_APPLICATION_SORT_SUBS = {
    "title": "index.unpunctitle.exact",
    "issn": "index.issn.exact"
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
# Analytics configuration
# specify in environment .cfg file - avoids sending live analytics events from test and dev environments

# ~~->PlausibleAnalytics:ExternalService~~
# Plausible analytics
# root url of plausible
PLAUSIBLE_URL = "https://plausible.io"
PLAUSIBLE_JS_URL = PLAUSIBLE_URL + "/js/script.outbound-links.file-downloads.js"
PLAUSIBLE_API_URL = PLAUSIBLE_URL + "/api/event"
# site name / domain name that used to register in plausible
PLAUSIBLE_SITE_NAME = BASE_DOMAIN
PLAUSIBLE_LOG_DIR = None

# Analytics custom dimensions. These are configured in the interface. #fixme: are these still configured since the move from GA?
ANALYTICS_DIMENSIONS = {
    'oai_res_id': 'dimension1',  # In analytics as OAI:Record
}

# Plausible for OAI-PMH
# ~~-> OAIPMH:Feature~~
ANALYTICS_CATEGORY_OAI = 'OAI-PMH'

# Plausible for Atom
# ~~-> Atom:Feature~~
ANALYTICS_CATEGORY_ATOM = 'Atom'
ANALYTICS_ACTION_ACTION = 'Feed request'

# Plausible for JournalCSV
# ~~-> JournalCSV:Feature~~
ANALYTICS_CATEGORY_JOURNALCSV = 'JournalCSV'
ANALYTICS_ACTION_JOURNALCSV = 'Download'

# Plausible for OpenURL
# ~~->OpenURL:Feature~~
ANALYTICS_CATEGORY_OPENURL = 'OpenURL'

# Plausible for PublicDataDump
# ~~->PublicDataDump:Feature~~
ANALYTICS_CATEGORY_PUBLICDATADUMP = 'PublicDataDump'
ANALYTICS_ACTION_PUBLICDATADUMP = 'Download'

# Plausible for RIS
# ~~->PublicDataDump:Feature~~
ANALYTICS_CATEGORY_RIS = 'RIS'
ANALYTICS_ACTION_RISEXPORT = 'Export'

# Plausible for Urlshort
# ~~->URLShortener:Feature~~
ANALYTICS_CATEGORY_URLSHORT = 'ShortURL'
ANALYTICS_ACTION_URLSHORT_ADD = 'Find or create short url'
ANALYTICS_ACTION_URLSHORT_REDIRECT = 'Redirect'

# Plausible for API
# ~~-> API:Feature~~
ANALYTICS_CATEGORY_API = 'API Hit'
ANALYTICS_ACTIONS_API = {
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
    'bulk_article_create_status': 'Bulk article create status',
    'bulk_article_delete': 'Bulk article delete'
}

# Plausible for fixed query widget
# ~~->FixedQueryWidget:Feature~~
ANALYTICS_CATEGORY_FQW = 'FQW'
ANALYTICS_ACTION_FQW = 'Hit'

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
# Harvester Configuration
# ~~->Harvester:Feature~~

# Configuration options for the DOAJ API Client

# EPMC Client configuration
# ~~-> EPMC:ExternalService~~
EPMC_REST_API = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
EPMC_TARGET_VERSION = "6.9"  # doc here: https://europepmc.org/docs/Europe_PMC_RESTful_Release_Notes.pdf
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
    "notification": 180,  # ~~-> Notifications:Feature ~~
    "background_job": 180,  # ~~-> BackgroundJobs:Feature ~~
}

########################################
# Editorial Dashboard - set to-do list size
TODO_LIST_SIZE = 48

#########################################################
# Background tasks --- monitor_bgjobs
TASKS_MONITOR_BGJOBS_TO = ["helpdesk@doaj.org", ]
TASKS_MONITOR_BGJOBS_FROM = "helpdesk@doaj.org"

##################################
# Background monitor
# ~~->BackgroundMonitor:Feature~~

# some time period for convenience
_MIN = 60
_HOUR = 3600
_DAY = 24 * _HOUR
_WEEK = 7 * _DAY

# Configures the age of the last completed job on the queue before the queue is marked as unstable
# (in seconds)
BG_MONITOR_LAST_COMPLETED = {
    'events': 2 * _HOUR,  # 2 hours
    'scheduled_short': 2 * _HOUR,  # 2 hours
    'scheduled_long': _DAY + 2 * _HOUR,  # 26 hours
}

# Default monitoring config for background job types which are not enumerated in BG_MONITOR_ERRORS_CONFIG below
BG_MONITOR_DEFAULT_CONFIG = {
    ## default values for queued config

    # the total number of items that are allowed to be in `queued` state at the same time.
    # Any more than this and the result is flagged
    'total': 2,

    # The age of the oldest record allowed to be in the `queued` state.
    # If the oldest queued item was created before this, the result is flagged
    'oldest': 20 * _MIN,

    ## default values for error config

    # The time period over which to check for errors, from now to now - check_sec
    'check_sec': _HOUR,

    # The number of errors allowed in the check period before the result is flagged
    'allowed_num_err': 0,

    # The last time this job ran within the specified time period, was it successful.
    # If the most recent job in the timeframe is an error, this will trigger an "unstable" state (0 turns this off)
    'last_run_successful_in': 0
}

# Configures the monitoring period and the allowed number of errors in that period before a queue is marked
# as unstable
BG_MONITOR_ERRORS_CONFIG = {
    'anon_export': {
        'check_sec': _WEEK,    # a week
        'allowed_num_err': 0
    },
    'article_bulk_create': {
        'check_sec': _DAY,  # 1 day
        'allowed_num_err': 0,
    },
    'article_cleanup_sync': {
        'check_sec': 2 * _DAY,    # 2 days
        'allowed_num_err': 0
    },
    'harvest': {
        'check_sec': _DAY,
        'allowed_num_err': 0,
    },
    'ingest_articles': {
        'check_sec': _DAY,
        'allowed_num_err': 0
    },
    'journal_csv': {
        'check_sec': 3 * _HOUR,
        'allowed_num_err': 1,
    },
    'public_data_dump': {
        'check_sec': 2 * _HOUR,
        'allowed_num_err': 0
    }
}

# Configures the total number of queued items and the age of the oldest of those queued items allowed
# before the queue is marked as unstable.  This is provided by type, so we can monitor all types separately
BG_MONITOR_QUEUED_CONFIG = {
    'anon_export': {
        'total': 1,
        'oldest': 20 * _MIN
    },
    'article_bulk_create': {
        'total': 3,
        'oldest': 10 * _MIN
    },
    'harvest': {
        'total': 1,
        'oldest': _DAY
    },
    'ingest_articles': {
        'total': 10,
        'oldest': 10 * _MIN
    },
    'journal_bulk_edit': {
        'total': 2,
        'oldest': 10 * _MIN
    },
    'journal_csv': {
        'total': 1,
        'oldest': 20 * _MIN
    },
    'public_data_dump': {
        'total': 1,
        'oldest': _DAY
    },
    'set_in_doaj': {
        'total': 2,
        'oldest': 10 * _MIN
    },
    'suggestion_bulk_edit': {
        'total': 2,
        'oldest': 10 * _MIN
    }
}

BG_MONITOR_LAST_SUCCESSFULLY_RUN_CONFIG = {
    'anon_export': {
        'last_run_successful_in': 32 * _DAY
    },
    'article_cleanup_sync': {
        'last_run_successful_in': 33 * _DAY
    },
    'async_workflow_notifications': {
        'last_run_successful_in': _WEEK + _DAY
    },
    'check_latest_es_backup': {
        'last_run_successful_in': _DAY + _HOUR
    },
    'datalog_journal_added_update': {
        'last_run_successful_in': _HOUR
    },
    'find_discontinued_soon': {
        'last_run_successful_in': _DAY + _HOUR
    },
    'harvest': {
        'last_run_successful_in': _DAY + _HOUR
    },
    'journal_csv': {
        'last_run_successful_in': 2 * _HOUR
    },
    'monitor_bgjobs': {
        'last_run_successful_in': _WEEK + _DAY
    },
    'old_data_cleanup': {
        'last_run_successful_in': 32 * _DAY
    },
    'prune_es_backups': {
        'last_run_successful_in': _DAY + _HOUR
    },
    'public_data_dump': {
        'last_run_successful_in': 32 * _DAY
    },
    'read_news': {
        'last_run_successful_in': 2 * _HOUR
    },
    'reporting': {
        'last_run_successful_in': 32 * _DAY
    },
    'request_es_backup': {
        'last_run_successful_in': _DAY + _HOUR
    },
    'sitemap': {
        'last_run_successful_in': _DAY + _HOUR
    }
}

##################################################
# Public data dump settings

# how long should the temporary URL for public data dumps last
PUBLIC_DATA_DUMP_URL_TIMEOUT = 3600

##################################################
# Pages under maintenance

PRESERVATION_PAGE_UNDER_MAINTENANCE = False

# report journals that discontinue in ... days (eg. 1 = tomorrow)
DISCONTINUED_DATE_DELTA = 0

##################################################
# Feature tours currently active

TOUR_COOKIE_PREFIX = "doaj_tour_"
TOUR_COOKIE_MAX_AGE = 31536000

TOURS = {
    "/admin/journal/*": [
        {
            "roles": ["admin"],
            "selectors": [".autochecks-manager-toggle"],
            "content_id": "admin_journal_autochecks",
            "name": "Autochecks",
            "description": "Autochecks are available on some journals, and can help you to identify potential problems with the journal's metadata."
        }
    ],
    "/editor/": [
        {
            "roles": ["editor"],
            "content_id": "application_by_status",
            "name": "New Links in the Colour Legend",
            "description": "Discover how the colour legend labels now serve as links to quickly filter and view applications by group and status."
        }
    ],
    "/dashboard/": [
        {
            "roles": ["admin"],
            "content_id": "application_by_status",
            "name": "New Links in the Colour Legend",
            "description": "Discover how the colour legend labels now serve as links to quickly filter and view applications by group and status."
        }
    ]
}

#######################################################
# Selenium test environment

# url of selenium server, selenium remote will be used if it's not empty
# usually it's a docker container and the url should be 'http://localhost:4444/wd/hub'
SELENIUM_REMOTE_URL = 'http://localhost:4444/wd/hub'

# host and port that used to run doaj server in background for selenium testcases
# if you use docker selenium browser container, ip should be ip of docker network interface such as 172.17.0.1
# SELENIUM_DOAJ_HOST = 'localhost'
SELENIUM_DOAJ_HOST = '172.17.0.1'
SELENIUM_DOAJ_PORT = 5014

#################################################
# Concurrency timeout(s)

UR_CONCURRENCY_TIMEOUT = 10

#############################################
# Google Sheet
# ~~->GoogleSheet:ExternalService~~

# Google Sheet API
# value should be key file path of json, empty string means disabled
GOOGLE_KEY_PATH = ''

# The /export path to test users CSV file on google sheets (file is public)
TEST_USERS_CSV_DL_PATH = ""


#############################################
# Datalog
# ~~->Datalog:Feature~~

# Datalog for Journal Added

# google sheet filename for datalog ja
DATALOG_JA_FILENAME = 'DOAJ: journals added and withdrawn'

# worksheet name or tab name that datalog will write to
DATALOG_JA_WORKSHEET_NAME = 'Added'

##################################################
# Autocheck Resource configurations

# Should we autocheck incoming applications and update requests
AUTOCHECK_INCOMING = False

AUTOCHECK_RESOURCE_ISSN_ORG_TIMEOUT = 10
AUTOCHECK_RESOURCE_ISSN_ORG_THROTTLE = 1  # seconds between requests

##################################################
# Background jobs Management settings

# list of actions name that will be cleaned up if they are redundant
BGJOB_MANAGE_REDUNDANT_ACTIONS = [
    'read_news', 'journal_csv'
]

##################################################
# Honeypot bot-trap settings for forms (now: only registration form)
HONEYPOT_TIMER_THRESHOLD = 5000


################################
# Url Shortener
# ~~->URLShortener:Feature~~

# URLSHORT_LIMIT* used to limit the number of short URLs (URLSHORT_LIMIT) created
# by a user within a certain time period (URLSHORT_LIMIT_WITHIN_DAYS)
URLSHORT_LIMIT_WITHIN_DAYS = 7
URLSHORT_LIMIT = 50_000

URLSHORT_ALLOWED_SUPERDOMAINS = ['doaj.org']
URLSHORT_ALIAS_LENGTH = 6

##################################################
# Object validation settings

SEAMLESS_JOURNAL_LIKE_SILENT_PRUNE = False