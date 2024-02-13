import datetime

from portality.dao import DomainObject
from portality.lib import dates


class ApiLog(DomainObject):
    """~~ApiLog:Model->DomainObject:Model~~"""
    __type__ = "api_log"

    def __init__(self, **kwargs):
        super(ApiLog, self).__init__(**kwargs)

    @property
    def src(self):
        return self.data.get("src")

    @src.setter
    def src(self, val: str):
        """
        Parameters
        ----------
        val
            can be IP address or API key
        """
        self.data["src"] = val

    @property
    def target(self):
        return self.data.get("target")

    @target.setter
    def target(self, target: str):
        """

        Parameters
        ----------
        target
            value format should be "METHOD /api/endpoint"

        Returns
        -------

        """
        self.data["target"] = target

    @classmethod
    def create(cls, src: str, target: str):
        api_log = ApiLog()
        api_log.src = src
        api_log.target = target
        api_log.set_created()
        api_log.save()
        return api_log


class ApiRateQuery:

    def __init__(self, src: str, target: str, since):
        if isinstance(since, datetime.datetime):
            since = dates.format(since)
        self._src = src
        self._target = target
        self._since = since

    def query(self):
        return {
            'query': {
                'bool': {
                    'must': [
                        {'range': {'created_date': {'gte': self._since}}},
                        {'term': {'src': self._src}},
                        {'term': {'target': self._target}},
                    ]
                }
            }
        }
