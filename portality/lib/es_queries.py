ES_DATETIME_FMT = '%Y-%m-%dT%H:%M:%SZ'


def query_all():
    return {
        'query': {
            'bool': {
                'must': [
                    {'match_all': {}}
                ]
            }
        }
    }
