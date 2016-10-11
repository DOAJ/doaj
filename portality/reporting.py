from portality import models
from portality.clcsv import UnicodeWriter
from portality.lib import dates
import codecs, os

def provenance_reports(fr, to, outdir):
    pipeline = []
    pipeline.append(ActionCounter("edit", "month"))
    pipeline.append(ActionCounter("edit", "year"))
    pipeline.append(StatusCounter("month"))
    pipeline.append(StatusCounter("year"))

    q = ProvenanceList(fr, to)
    for prov in models.Provenance.iterate(q.query()):
        for filt in pipeline:
            filt.count(prov)

    outfiles = []
    for p in pipeline:
        table = p.tabulate()
        outfile = os.path.join(outdir, p.filename(fr, to))
        outfiles.append(outfile)
        with codecs.open(outfile, "wb") as f:
            writer = UnicodeWriter(f)
            for row in table:
                writer.writerow(row)

    return outfiles


def content_reports(fr, to, outdir):
    report = {}

    q = ContentByDate(fr, to)
    res = models.Suggestion.query(q=q.query())
    year_buckets = res.get("aggregations", {}).get("years", {}).get("buckets", [])
    for years in year_buckets:
        ds = years.get("key_as_string")
        do = dates.parse(ds)
        year = do.year
        if year not in report:
            report[year] = {}
        country_buckets = years.get("countries", {}).get("buckets", [])
        for country in country_buckets:
            cn = country.get("key")
            if cn not in report[year]:
                report[year][cn] = {}
            count = country.get("doc_count")
            report[year][cn]["count"] = count

    table = _tabulate_time_entity_group(report, "Country")

    filename = "applications_by_year_by_country__" + fr + "_to_" + to + "__on_" + dates.now() + ".csv"
    outfiles = []
    outfile = os.path.join(outdir, filename)
    outfiles.append(outfile)
    with codecs.open(outfile, "wb") as f:
        writer = UnicodeWriter(f)
        for row in table:
            writer.writerow(row)

    return outfiles


def _tabulate_time_entity_group(group, entityKey):
    date_keys = group.keys()
    date_keys.sort()
    table = []
    padding = []
    for db in date_keys:
        users = group[db].keys()
        for u in users:
            c = group[db][u]["count"]
            existing = False
            for row in table:
                if row[0] == u:
                    row.append(c)
                    existing = True
            if not existing:
                table.append([u] + padding + [c])
        padding.append(0)

    for row in table:
        if len(row) < len(date_keys) + 1:
            row += [0] * (len(date_keys) - len(row) + 1)

    table.sort(key=lambda user: user[0])
    table = [[entityKey] + date_keys] + table
    return table


class ReportCounter(object):
    def __init__(self, period):
        self.period = period

    def _flatten_timestamp(self, ts):
        if self.period == "month":
            return ts.strftime("%Y-%m")
        elif self.period == "year":
            return ts.strftime("%Y")

    def count(self, prov):
        raise NotImplementedError()

    def tabulate(self):
        raise NotImplementedError()

    def filename(self, fr, to):
        raise NotImplementedError()


class ActionCounter(ReportCounter):
    def __init__(self, action, period):
        self.action = action
        self.report = {}
        self._last_period = None
        super(ActionCounter, self).__init__(period)

    def count(self, prov):
        if prov.action != self.action:
            return

        p = self._flatten_timestamp(prov.created_timestamp)
        if p not in self.report:
            self.report[p] = {}

        if prov.user not in self.report[p]:
            self.report[p][prov.user] = {"ids" : []}

        if prov.resource_id not in self.report[p][prov.user]["ids"]:
            self.report[p][prov.user]["ids"].append(prov.resource_id)

        if p != self._last_period:
            self._count_down(self._last_period)
            self._last_period = p

    def tabulate(self):
        self._count_down(self._last_period)
        return _tabulate_time_entity_group(self.report, "User")

    def filename(self, fr, to):
        return self.action + "_by_" + self.period + "__from_" + fr + "_to_" + to + "__on_" + dates.now() + ".csv"

    def _count_down(self, p):
        if p is None:
            return
        for k in self.report[p].keys():
            self.report[p][k]["count"] = len(self.report[p][k]["ids"])
            del self.report[p][k]["ids"]


class StatusCounter(ReportCounter):
    def __init__(self, period):
        self.report = {}
        self._last_period = None
        super(StatusCounter, self).__init__(period)

    def count(self, prov):
        if not prov.action.startswith("status:"):
            return

        role_precedence = ["associate_editor", "editor", "admin"]
        best_role = None
        for r in prov.roles:
            try:
                if best_role is None:
                    best_role = r
                if role_precedence.index(r) > role_precedence.index(best_role):
                    best_role = r
            except ValueError:
                pass                            # The user has a role not in our precedence list (e.g. api) - ignore it.

        countable = False
        if best_role == "admin" and (prov.action == "status:accepted" or prov.action == "status:rejected"):
            countable = True
        elif best_role == "editor" and prov.action == "status:ready":
            countable = True
        elif best_role == "associate_editor" and prov.action == "status:completed":
            countable = True

        if not countable:
            return

        p = self._flatten_timestamp(prov.created_timestamp)
        if p not in self.report:
            self.report[p] = {}

        if prov.user not in self.report[p]:
            self.report[p][prov.user] = {"ids" : []}

        if prov.resource_id not in self.report[p][prov.user]["ids"]:
            self.report[p][prov.user]["ids"].append(prov.resource_id)

        if p != self._last_period:
            self._count_down(self._last_period)
            self._last_period = p

    def tabulate(self):
        self._count_down(self._last_period)
        return _tabulate_time_entity_group(self.report, "User")

    def filename(self, fr, to):
        return "completion_by_" + self.period + "__from_" + fr + "_to_" + to + "__on_" + dates.now() + ".csv"

    def _count_down(self, p):
        if p is None:
            return
        for k in self.report[p].keys():
            self.report[p][k]["count"] = len(self.report[p][k]["ids"])
            del self.report[p][k]["ids"]


class ProvenanceList(object):
    def __init__(self, fr, to):
        self.fr = fr
        self.to = to

    def query(self):
        return {
            "query" : {
                "bool" : {
                    "must" : [
                        {"range" : {"created_date" : {"gt" : self.fr, "lte" : self.to}}}
                    ]
                }
            },
            "sort" : [{"created_date" : {"order" : "asc"}}]
        }


class ContentByDate(object):
    def __init__(self, fr, to):
        self.fr = fr
        self.to = to

    def query(self):
        return {
            "query" : {
                "bool" : {
                    "must" : [
                        {"range" : {"created_date" : {"gt" : self.fr, "lte" : self.to}}}
                    ]
                }
            },
            "size" : 0,
            "aggs" : {
                "years" : {
                    "date_histogram" : {
                        "field" : "created_date",
                        "interval" : "year"
                    },
                    "aggs" : {
                        "countries" : {
                            "terms" : {"field" : "bibjson.country.exact"}
                        }
                    }
                }
            }
        }
