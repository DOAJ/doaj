from portality.lib.dates import FMT_STD_DATETIME

ES_DATETIME_FMT = FMT_STD_DATETIME


def query_all():
    return {
        "query": {
            "match_all": {}
        }
    }
