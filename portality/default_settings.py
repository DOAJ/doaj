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

PUBLIC_REGISTER = True # Can people register publicly? If false, only the superuser can create new accounts
SHOW_LOGIN = True # if this is false the login link is not shown in the default template, but login is not necessarily disabled

# if you make remote calls e.g. to google fonts or js plugins but have to run offline, then wrap those parts of your templates with a check for this, and then you can set it to true if you need to run your system without online access
OFFLINE = False 

# elasticsearch settings
ELASTIC_SEARCH_HOST = "http://127.0.0.1:9200" # remember the http:// or https://
ELASTIC_SEARCH_DB = "portality"
INITIALISE_INDEX = True # whether or not to try creating the index and required index types on startup
NO_QUERY_VIA_API = ['account'] # list index types that should not be queryable via the API
PUBLIC_ACCESSIBLE_JSON = True # can not logged in people get JSON versions of pages by querying for them?

# location of media storage folder
MEDIA_FOLDER = "media"

# if search filter is true, anonymous users only see visible and accessible pages in query results
# if search sort and order are set, all queries from /query will return with default search unless one is provided
# placeholder image can be used in search result displays
ANONYMOUS_SEARCH_FILTER = True
SEARCH_SORT = ''
SEARCH_SORT_ORDER = ''

# jsite settings
JSITE_OPTIONS = {
    "searchurl": "/query/record/_search?",
    "recordurl": "/query/record/",
    "savetourl": "",
    "datatype": "json",
    "collaborative": False,
    "pads_address": '',
    "pads_baseurl": "/p/",
    "comments": "",
    "twitter": "",
    "sharethis": False,
    "editable": True,
    "richtextedit": False,
    "facetview": {
        "search_url": "/query/record/_search?",
        "datatype": "json",
        "display_images": False
    },
    "facetview_displays": {
        "titles": {
            'result_display': [
                [
                    {
                        "pre": '<h4><a href="',
                        "field": "url",
                        "post": '">'
                    },
                    {
                        "field": "title",
                        "post": "</a></h4>"
                    }
                ]
            ],
            'searchwrap_start': '<table id="facetview_results" class="table table-bordered table-striped table-condensed">',
            'searchwrap_end': '</table>',
            'resultwrap_start': '<tr><td>',
            'resultwrap_end': '</td></tr>',
            "paging":{
                "from":0,
                "size":10
            }
        }
    }
}

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

