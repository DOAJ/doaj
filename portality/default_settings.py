SECRET_KEY = "default-key" # make this something secret in your overriding app.cfg

# contact info
ADMIN_NAME = "Cottage Labs"
ADMIN_EMAIL = ""

# service info
SERVICE_NAME = "Portality"
SERVICE_TAGLINE = ""
HOST = "0.0.0.0"
DEBUG = True
PORT = 5004

# list of superuser account names
SUPER_USER = ["test"]

PUBLIC_REGISTER = False # Can people register publicly? If false, only the superuser can create new accounts

# elasticsearch settings
ELASTIC_SEARCH_HOST = "http://127.0.0.1:9200" # remember the http:// or https://
ELASTIC_SEARCH_DB = "portality"
INITIALISE_INDEX = True # whether or not to try creating the index and required index types on startup
NO_QUERY_VIA_API = ['account'] # list index types that should not be queryable via the API
PUBLIC_ACCESSIBLE_JSON = True # can not logged in people get JSON versions of pages by querying for them?

# location of media storage folder
MEDIA_FOLDER = "media"

# location for where page content should be written to disk, if anywhere
CONTENT_FOLDER = "content"

# etherpad endpoint if available for collaborative editing
COLLABORATIVE = 'http://pads.cottagelabs.com'

# disqus account shortname if available for page comments
COMMENTS = 'cottagelabs'

# if search filter is not false, anonymous users only see visible and accessible pages in query results
# if search sort and order are set, all queries from /query will return with default search unless one is provided
# placeholder image can be used in search result displays
ANONYMOUS_SEARCH_FILTER_TERMS = False #{'visible':True,'accessible':True}
SEARCH_SORT = ''
SEARCH_SORT_ORDER = ''


# a dict of the ES mappings. identify by name, and include name as first object name
# and identifier for how non-analyzed fields for faceting are differentiated in the mappings
FACET_FIELD = ".exact"
MAPPINGS = {
    "record" : {
        "record" : {
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

MAPPINGS['pages'] = {'pages':MAPPINGS['record']['record']}

