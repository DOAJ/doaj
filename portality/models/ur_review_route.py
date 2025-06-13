from portality.core import app
from portality.dao import DomainObject
from portality.lib import es_data_mapping
from portality.lib.coerce import COERCE_MAP
from portality.lib.seamless import SeamlessMixin

STRUCT = {
    "fields": {
        "id": {"coerce": "unicode"},
        "created_date": {"coerce": "utcdatetime"},
        "last_updated": {"coerce": "utcdatetime"},
        "es_type": {"coerce": "unicode"},
        "account_id": {"coerce": "unicode"},
        "country": {"coerce": "unicode"},
        "target": {"coerce": "unicode"}
    }
}

MAPPING_OPTS = {
    "dynamic": None,
    "coerces": app.config["DATAOBJ_TO_MAPPING_DEFAULTS"]
}

class URReviewRoute(SeamlessMixin, DomainObject):
    __type__ = "ur_review_route"

    __SEAMLESS_STRUCT__ = STRUCT
    __SEAMLESS_COERCE__ = COERCE_MAP

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]
        super(URReviewRoute, self).__init__(raw=kwargs)

    def mappings(self):
        return es_data_mapping.create_mapping(self.__seamless_struct__.raw, MAPPING_OPTS)

    @classmethod
    def by_account(cls, account_id):
        """
        Get a URReviewRoute by account id
        :param account_id:
        :return:
        """
        q = {
            "query": {
                "term": {
                    "account_id.exact": account_id
                }
            },
            "sort": {
                "created_date": {
                    "order": "desc"
                }
            },
            "size": 1
        }
        res = cls.object_query(q)
        if res and len(res) > 0:
            return res[0]
        else:
            return None

    @classmethod
    def by_country_name(cls, country_name):
        """
        Get a URReviewRoute by country name
        :return:
        """
        q = {
            "query": {
                "term": {
                    "country.exact": country_name
                }
            },
            "sort": {
                "created_date": {
                    "order": "desc"
                }
            },
            "size": 1
        }
        res = cls.object_query(q)
        if res and len(res) > 0:
            return res[0]
        else:
            return None

    @property
    def data(self):
        return self.__seamless__.data

    @property
    def account_id(self):
        return self.__seamless__.get_single("account_id")

    @account_id.setter
    def account_id(self, val):
        self.__seamless__.set_with_struct("account_id", val)

    @property
    def country(self):
        return self.__seamless__.get_single("country")

    @country.setter
    def country(self, val):
        self.__seamless__.set_with_struct("country", val)

    @property
    def target(self):
        return self.__seamless__.get_single("target")

    @target.setter
    def target(self, val):
        self.__seamless__.set_with_struct("target", val)