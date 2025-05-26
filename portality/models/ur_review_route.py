from portality.lib.seamless import SeamlessMixin
from portality.dao import DomainObject
from portality.lib.coerce import COERCE_MAP
from portality.lib import es_data_mapping

STRUCT = {
    "fields": {
        "id": {"coerce": "unicode"},
        "created_date": {"coerce": "utcdatetime"},
        "last_updated": {"coerce": "utcdatetime"},
        "account_id": {"coerce": "unicode"},
        "country": {"coerce": "unicode"},
        "target": {"coerce": "unicode"}
    }
}

MAPPING_OPTS = {
    "dynamic": None
}

class URReviewRoute(SeamlessMixin, DomainObject):
    __type__ = "ur_review_route"

    __SEAMLESS_STRUCT__ = STRUCT
    __SEAMLESS_COERCE__ = COERCE_MAP

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
        return cls.object_query(q)

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
                    "order": "asc"
                }
            },
            "size": 1
        }
        return cls.object_query(q)

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