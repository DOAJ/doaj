from portality import models

license_correct_dict = { "CC by" : "CC BY",
                         "CC by-nc" : "CC BY-NC",
                         "CC by-nc-nd" : "CC BY-NC-ND",
                         "CC by-nc-sa" : "CC BY-NC-SA",
                         "CC-BY-NC-SA" : "CC BY-NC-SA",
                         "CC by-sa" : "CC BY-SA",
                         "CC by-nd" : "CC BY-ND",
                         "not-cc-like" : "Not CC-like"
                        }

# Location of the ES index
ES_SEARCH = "localhost:9200/doaj/article/_search"

# The scroll query
ES_SCROLL = "?scroll=1m"
SCROLL_STR = "?scroll_id={0}"

# The scroll ID
scroll_id = ""

# Scroll search through the index and correct according to the above dict

# TODO: I don't think we can use the standard query endpoint for a scroll search - does this affect using the model?