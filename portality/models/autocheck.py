from portality.dao import DomainObject
from portality.lib.seamless import SeamlessMixin
from portality.lib.coerce import COERCE_MAP
from portality.lib import es_data_mapping
from portality.core import app

import json
from copy import deepcopy


AUTOCHECK_STRUCT = {
    "fields": {
        "id": {"coerce": "unicode"},
        "es_type": {"coerce": "unicode"},
        "created_date": {"coerce": "utcdatetime"},
        "last_updated": {"coerce": "utcdatetime"},
        "application": {"coerce": "unicode"},
        "journal": {"coerce": "unicode"}
    },
    "lists": {
        "checks": {"contains": "object"}
    },

    "structs": {
        "checks": {
            "fields": {
                "id": {"coerce": "unicode"},
                "field": {"coerce": "unicode"},
                "original_value": {"coerce": "unicode"},
                "replaced_value": {"coerce": "unicode"},
                "advice": {"coerce": "unicode"},
                "reference_url": {"coerce": "unicode"},
                "checked_by": {"coerce": "unicode"},
                "dismissed": {"coerce": "bool"},
                "context": {"coerce": "unicode"}
            },
            "lists": {
                "suggested_value": {"contains": "field", "coerce": "unicode"}
            }
        }
    }
}

MAPPING_OPTS = {
    "dynamic": None,
    "coerces": app.config["DATAOBJ_TO_MAPPING_DEFAULTS"]
}


class Autocheck(SeamlessMixin, DomainObject):
    __type__ = "autocheck"

    __SEAMLESS_STRUCT__ = [
        AUTOCHECK_STRUCT
    ]

    __SEAMLESS_COERCE__ = COERCE_MAP

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]
        super(Autocheck, self).__init__(raw=kwargs)

    def mappings(self):
        return es_data_mapping.create_mapping(self.__seamless_struct__.raw, MAPPING_OPTS)

    @property
    def data(self):
        return self.__seamless__.data

    @classmethod
    def for_application(cls, app_id):
        q = ApplicationQuery(app_id)
        res = cls.object_query(q.query())
        if len(res) > 0:
            return res[0]
        return None

    @classmethod
    def for_journal(cls, journal_id):
        q = JournalQuery(journal_id)
        res = cls.object_query(q.query())
        if len(res) > 0:
            return res[0]
        return None

    @property
    def application(self):
        return self.__seamless__.get_single("application")

    @application.setter
    def application(self, val):
        self.__seamless__.set_with_struct("application", val)

    @property
    def journal(self):
        return self.__seamless__.get_single("journal")

    @journal.setter
    def journal(self, val):
        self.__seamless__.set_with_struct("journal", val)

    def add_check(self, field=None, original_value=None, suggested_value=None, advice=None, reference_url=None, context=None, checked_by=None):
        obj = {}
        if field is not None:
            obj["field"] = field
        if original_value is not None:
            obj["original_value"] = original_value
        if suggested_value is not None:
            if not isinstance(suggested_value, list):
                suggested_value = [suggested_value]
            obj["suggested_value"] = suggested_value
        if advice is not None:
            obj["advice"] = advice
        if reference_url is not None:
            obj["reference_url"] = reference_url
        if checked_by is not None:
            obj["checked_by"] = checked_by
        if context is not None:
            obj["context"] = json.dumps(context)

        # ensure we add the check only once
        exists = self.__seamless__.exists_in_list("checks", matchsub=obj)

        # now give this check an id and add it
        if not exists:
            obj["id"] = self.makeid()
            self.__seamless__.add_to_list_with_struct("checks", obj)

    @property
    def checks(self):
        annos = self.__seamless__.get_list("checks")
        realised_checks = []
        for anno in annos:
            anno = deepcopy(anno)
            if "context" in anno:
                anno["context"] = json.loads(anno["context"])
            realised_checks.append(anno)
        return realised_checks

    @property
    def checks_raw(self):
        return self.__seamless__.get_list("checks")

    def dismiss(self, check_id):
        annos = self.checks_raw
        for anno in annos:
            if anno.get("id") == check_id:
                anno["dismissed"] = True
                break

    def undismiss(self, check_id):
        annos = self.checks_raw
        for anno in annos:
            if anno.get("id") == check_id:
                del anno["dismissed"]
                break


class ApplicationQuery(object):
    def __init__(self, app_id):
        self._app_id = app_id

    def query(self):
        return {
            "query" : {
                "bool": {
                    "must": [
                        {"term": {"application.exact": self._app_id}}
                    ]
                }
            },
            "size": 1,
            "sort": {
                "created_date": {"order": "desc"}
            }
        }


class JournalQuery(object):
    def __init__(self, journal_id):
        self._journal_id = journal_id

    def query(self):
        return {
            "query" : {
                "bool": {
                    "must": [
                        {"term": {"journal.exact": self._journal_id}}
                    ]
                }
            },
            "size": 1,
            "sort": {
                "created_date": {"order": "desc"}
            }
        }