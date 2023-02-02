from portality.lib.dates import STD_DATETIME_FMT

ES_DATETIME_FMT = STD_DATETIME_FMT


def query_all():
    return {
        "query": {
            "match_all": {}
        }
    }
