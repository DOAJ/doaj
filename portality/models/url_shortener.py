from portality.dao import DomainObject


class UrlShortener(DomainObject):
    """~~UrlShortener:Model->DomainObject:Model~~"""
    __type__ = "url_shortener"

    def __init__(self, **kwargs):
        super(UrlShortener, self).__init__(**kwargs)

    @property
    def url(self):
        return self.data.get("url")

    @url.setter
    def url(self, val):
        self.data["url"] = val

    @property
    def alias(self):
        return self.data.get("alias")

    @alias.setter
    def alias(self, val):
        self.data["alias"] = val


class UrlQuery:
    def __init__(self, alias: str):
        self.alias = alias

    def query(self):
        return {
            'query': {
                'bool': {
                    'must': [
                        {'term': {'alias.exact': self.alias}}
                    ]
                }
            },
            '_source': ['url'],
        }


class AliasQuery:
    def __init__(self, url: str):
        self.url = url

    def query(self):
        return {
            'query': {
                'bool': {
                    'must': [
                        {'term': {'url.exact': self.url}}
                    ]
                }
            },
            '_source': ['alias'],
        }


class CountWithinDaysQuery:
    def __init__(self, days: int):
        self.days = days

    def query(self):
        return {
            "size": 0,
            "query": {
                "range": {
                    "created_date": {
                        "gte": f"now-{self.days}d",
                    }
                }
            }
        }
