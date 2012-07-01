SECRET_KEY = 'default-key'

# service and super user account
SERVICE_NAME = "portality"
SUPER_USER = ["test"]
HOST = "0.0.0.0"
DEBUG = True
PORT = 5004

# elasticsearch settings
ELASTIC_SEARCH_HOST = "127.0.0.1:9200"
ELASTIC_SEARCH_DB = "portality"

# The default fields and settings for which faceting should be made available on
# these can be nested fields, e.g. links.url
SEARCH_FACET_FIELDS = [
    {
        "field":"type.exact",
        "order":"term",
        "size":10,
        "display":"type"
    },
    {
        "field":"batch.exact",
        "display":"batch"
    },
    {
        "field":"assembly.exact",
        "display":"assembly"
    },
    {
        "field":"created_date.exact",
        "size":10,
        "order":"reverse_term",
        "display":"created"
    },
    {
        "field":"updated_date.exact",
        "size":10,
        "order":"reverse_term",
        "display":"last updated"
    }
]

# search result display layout
# a list of lists. each list represents a line on the display.
# in each line, there are objects for each key to include on the line.
# must specify the key, and optional "pre" and "post" params for displaying round it
SEARCH_RESULT_DISPLAY = [
    [
        {
            "field":"type",
            "post":" "
        },
        {
            "pre":"<a title=\"view record\" href=\"/record/",
            "field":"id",
            "post":"\">"
        },
        {
            "field":"id",
            "post":"</a>"
        },
        {
            "pre":" - ",
            "field":"name"
        }
    ]
]

# a dict of the ES mappings. identify by name, and include name as first object name
# and identifier for how non-analyzed fields for faceting are differentiated in the mappings
FACET_FIELD = ".exact"
MAPPINGS = {
    "record" : {
        "record" : {
            "date_detection" : False,
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
    },
    "collection" : {
        "collection" : {
            "date_detection" : False,
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

