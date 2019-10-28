from portality.lib import dataobj
from portality.dao import DomainObject
from portality.lib import dates, es_data_mapping
from portality.core import app


class HarvesterPlugin(object):
    def get_name(self):
        raise NotImplementedError()

    def iterate(self, issn, since, to=None):
        """
        Iterate over the records associated with the issn from "since" until "to"

        This should return a generator (i.e. it should yield), and it needs to yeild a tuple
        containing (<doaj article>, <harvest date for this record>)

        :param issn:
        :param since:
        :param to:
        :return:
        """
        raise NotImplementedError()


class HarvestState(dataobj.DataObj, DomainObject):
    __type__ = 'harvester_state'

    def __init__(self, **raw):
        struct = {
            "fields" : {
                "id" : {"coerce" : "unicode"},
                "last_updated" : {"coerce" : "utcdatetime"},
                "created_date" : {"coerce" : "utcdatetime"},
                "issn" : {"coerce" : "unicode"},
                "status" : {"coerce" : "unicode", "allowed_values" : [u"suspended", u"active"]},
                "account" : {"coerce" : "unicode"},
            },
            "lists" : {
                "last_harvest" : {"contains" : "object"}
            },

            "structs" : {
                "last_harvest" : {
                    "fields" : {
                        "plugin" : {"coerce" : "unicode"},
                        "date" : {"coerce" : "utcdatetime"}
                    }
                }
            }
        }

        if "_source" in raw:
            raw = raw["_source"]
        super(HarvestState, self).__init__(raw, struct)

    def mappings(self):
        return es_data_mapping.create_mapping(self.get_struct(), MAPPING_OPTS)

    @classmethod
    def find_by_issn(cls, account, issn):
        q = ISSNQuery(account, issn)
        obs = cls.q2obj(q=q.query())
        if len(obs) > 0:
            return obs[0]
        return None

    @classmethod
    def find_by_account(cls, account):
        q = AccountQuery(account)
        # FIXME: in time we need to put scroll on the base DAO
        return cls.all(q=q.query())
        # return cls.scroll(q=q.query())

    def _coerce_and_kwargs(self, path, dir):
        type, struct, instructions = dataobj.construct_lookup(path, self._struct)
        c = self._coerce_map.get(instructions.get("coerce", "unicode"))
        kwargs = dataobj.construct_kwargs(type, dir, instructions)
        return c, kwargs

    @property
    def account(self):
        c, kwargs = self._coerce_and_kwargs("account", "get")
        return self._get_single("account", coerce=c, **kwargs)

    @account.setter
    def account(self, val):
        c, kwargs = self._coerce_and_kwargs("account", "set")
        self._set_single("account", val, coerce=c, **kwargs)

    @property
    def issn(self):
        c, kwargs = self._coerce_and_kwargs("issn", "get")
        return self._get_single("issn", coerce=c, **kwargs)

    @issn.setter
    def issn(self, val):
        c, kwargs = self._coerce_and_kwargs("issn", "set")
        self._set_single("issn", val, coerce=c, **kwargs)

    def suspend(self):
        self.status = "suspended"

    @property
    def suspended(self):
        return self.status == "suspended"

    @property
    def status(self):
        c, kwargs = self._coerce_and_kwargs("status", "get")
        return self._get_single("status", coerce=c, **kwargs)

    @status.setter
    def status(self, val):
        c, kwargs = self._coerce_and_kwargs("status", "set")
        self._set_single("status", val, coerce=c, **kwargs)

    def reactivate(self):
        self.status = "active"

    def get_last_harvest(self, harvester_name):
        lhs = self._get_list("last_harvest")
        for lh in lhs:
            if lh.get("plugin") == harvester_name:
                return lh.get("date")
        return None

    def set_harvested(self, harvester_name, last_harvest_date=None):
        # first ensure we have a last harvest date, and that it's in the right format
        if last_harvest_date is None:
            last_harvest_date = dates.now()
        last_harvest_date = dates.reformat(last_harvest_date)

        self._delete_from_list("last_harvest", matchsub={"plugin" : harvester_name})
        self._add_to_list("last_harvest", {"plugin" : harvester_name, "date" : last_harvest_date})

    def prep(self):
        if self.status is None:
            self.status = "active"

    def save(self, *args, **kwargs):
        self.prep()
        super(HarvestState, self).save(*args, **kwargs)


class HarvesterProgressReport(object):
    current_states = {}
    last_harvest_dates_at_start_of_harvester = {}
    articles_processed = {}
    articles_saved_successfully = {}
    harvester_started = dates.now()
    error_messages = []

    @classmethod
    def set_start_by_issn(cls, plugin, issn, date):
        try:
            cls.last_harvest_dates_at_start_of_harvester[plugin][issn] = date
        except KeyError:
            cls.last_harvest_dates_at_start_of_harvester[plugin] = {issn: date}

    @classmethod
    def set_state_by_issn(cls, issn, state):
        cls.current_states[issn] = state

    @classmethod
    def increment_articles_processed(cls, plugin):
        try:
            cls.articles_processed[plugin] += 1
        except KeyError:
            cls.articles_processed[plugin] = 1

    @classmethod
    def increment_articles_saved_successfully(cls, plugin):
        try:
            cls.articles_saved_successfully[plugin] += 1
        except KeyError:
            cls.articles_saved_successfully[plugin] = 1

    @classmethod
    def record_error(cls, msg):
        cls.error_messages.append(msg)

    @classmethod
    def write_report(cls):
        report = ["Harvester ran from {d1} to {d2}.".format(d1=cls.harvester_started, d2=dates.now())]
        for p_name in list(cls.last_harvest_dates_at_start_of_harvester.keys()):
            report.append("Plugin {p} harvested {n_total} articles. "
                          "{n_succ} saved successfully to DOAJ; {n_fail} failed.".format(
                p=p_name,
                n_total=cls.articles_processed.get(p_name, 0),
                n_succ= cls.articles_saved_successfully.get(p_name, 0),
                n_fail=cls.articles_processed.get(p_name, 0) - cls.articles_saved_successfully.get(p_name, 0)
            ))

            for issn in list(cls.last_harvest_dates_at_start_of_harvester[p_name].keys()):
                report.append("ISSN {i} processed period {d1} until {d2}.".format(
                    i=issn,
                    d1=cls.last_harvest_dates_at_start_of_harvester[p_name][issn],
                    d2=cls.current_states[issn].get_last_harvest(p_name)
                ))
        report.append("Error messages/import failures:")
        report += cls.error_messages
        return "\n".join(report)


MAPPING_OPTS = {
    "dynamic": None,
    "coerces": app.config["DATAOBJ_TO_MAPPING_DEFAULTS"]
}


class ISSNQuery(object):
    def __init__(self, account, issn):
        self.issn = issn
        self.account = account

    def query(self):
        return {
            "query" : {
                "bool" : {
                    "must" : [
                        {"term" : {"issn.exact" : self.issn}},
                        {"term" : {"account.exact" : self.account}}
                    ]
                }
            }
        }

class AccountQuery(object):
    def __init__(self, account):
        self.account = account

    def query(self):
        return {
            "query" : {
                "bool" : {
                    "must" : [
                        {"term" : {"account.exact" : self.account}}
                    ]
                }
            }
        }