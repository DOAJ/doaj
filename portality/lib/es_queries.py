from portality.lib.dates import FMT_DATETIME_STD

ES_DATETIME_FMT = FMT_DATETIME_STD


def query_all():
    return {
        "query": {
            "match_all": {}
        }
    }
