from portality.dao import DomainObject


class ApiLog(DomainObject):
    """~~ApiLog:Model->DomainObject:Model~~"""
    __type__ = "api_rate"

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

    @property
    def created_date(self):
        return self.data.get("created_date")

    @created_date.setter
    def created_date(self, val):
        self.data["created_date"] = val
