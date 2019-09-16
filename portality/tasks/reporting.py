from portality import models
from portality.clcsv import UnicodeWriter
from portality.lib import dates
from portality import datasets
from portality.core import app

from portality.background import BackgroundApi, BackgroundTask
from portality.tasks.redis_huey import main_queue, schedule
from portality.app_email import email_archive
from portality.decorators import write_required

import codecs, os, shutil


def provenance_reports(fr, to, outdir):
    pipeline = [
        ActionCounter("edit", "month"),
        ActionCounter("edit", "year"),
        StatusCounter("month"),
        StatusCounter("year")
    ]

    q = ProvenanceList(fr, to)
    for prov in models.Provenance.iterate(q.query()):
        for filt in pipeline:
            filt.count(prov)

    outfiles = []
    for p in pipeline:
        table = p.tabulate()
        outfile = os.path.join(outdir, p.filename(fr, to))
        outfiles.append(outfile)
        with codecs.open(outfile, "wb", "utf-8") as f:
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
            cc = country.get("key")
            cn = datasets.get_country_name(cc)
            if cn not in report[year]:
                report[year][cn] = {}
            count = country.get("doc_count")
            report[year][cn]["count"] = count

    table = _tabulate_time_entity_group(report, "Country")

    filename = "applications_by_year_by_country__" + _fft(fr) + "_to_" + _fft(to) + "__on_" + dates.today() + ".csv"
    outfiles = []
    outfile = os.path.join(outdir, filename)
    outfiles.append(outfile)
    with codecs.open(outfile, "wb", "utf-8") as f:
        writer = UnicodeWriter(f)
        for row in table:
            writer.writerow(row)

    return outfiles


def _tabulate_time_entity_group(group, entityKey):
    date_keys = list(group.keys())
    date_keys.sort()
    table = []
    padding = []
    for db in date_keys:
        users_active_this_period = list(group[db].keys())
        for u in users_active_this_period:
            c = group[db][u]["count"]
            existing = False
            for row in table:
                if row[0] == u:
                    row.append(c)
                    existing = True
            if not existing:
                table.append([u] + padding + [c])

        # Add a 0 for each user who has been added to the table but doesn't
        # have any actions in the current time period we're looping over. E.g.
        # if we're counting edits by month, this would be "users who were active
        # in a previous month but haven't made any edits this month".
        users_in_table = set([each_row[0] for each_row in table])
        previously_active_users = users_in_table - set(users_active_this_period)
        for row in table:
            if row[0] in previously_active_users:
                row.append(0)

        # The following is only prefix padding. E.g. if "dom" started making edits in
        # Jan 2015 but "emanuil" only started in Mar 2015, then "emanuil" needs
        # 0s filled in for Jan + Feb 2015.
        padding.append(0)

    for row in table:
        if len(row) < len(date_keys) + 1:
            row += [0] * (len(date_keys) - len(row) + 1)

    table.sort(key=lambda user: user[0])
    table = [[entityKey] + date_keys] + table
    return table


def _fft(timestamp):
    """File Friendly Timestamp - Windows doesn't appreciate : / etc in filenames; strip these out"""
    return dates.reformat(timestamp, app.config.get("DEFAULT_DATE_FORMAT"), "%Y-%m-%d")


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
        return self.action + "_by_" + self.period + "__from_" + _fft(fr) + "_to_" + _fft(to) + "__on_" + dates.today() + ".csv"

    def _count_down(self, p):
        if p is None:
            return
        for k in list(self.report[p].keys()):
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

        best_role = self._get_best_role(prov.roles)
        countable = self._is_countable(prov, best_role)

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

    @staticmethod
    def _get_best_role(roles):
        role_precedence = ["associate_editor", "editor", "admin"]
        best_role = None
        for r in roles:
            try:
                if best_role is None and r in role_precedence:
                    best_role = r
                if role_precedence.index(r) > role_precedence.index(best_role):
                    best_role = r
            except ValueError:
                pass                            # The user has a role not in our precedence list (e.g. api) - ignore it.

        return best_role

    @staticmethod
    def _is_countable(prov, role):
        """ Determine whether to include this provenance record in the report"""

        """
        # We now disregard role and count all completion events per user https://github.com/DOAJ/doaj/issues/1385
        countable = False

        if role == "admin" and (prov.action == "status:accepted" or prov.action == "status:rejected"):
            countable = True
        elif role == "editor" and prov.action == "status:ready":
            countable = True
        elif role == "associate_editor" and prov.action == "status:completed":
            countable = True
        """

        return prov.action in ["status:accepted", "status:rejected", "status:ready", "status:completed"]

    def tabulate(self):
        self._count_down(self._last_period)
        return _tabulate_time_entity_group(self.report, "User")

    def filename(self, fr, to):
        return "completion_by_" + self.period + "__from_" + _fft(fr) + "_to_" + _fft(to) + "__on_" + dates.today() + ".csv"

    def _count_down(self, p):
        if p is None:
            return
        for k in list(self.report[p].keys()):
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
                            "terms" : {
                                "field" : "bibjson.country.exact",
                                "size" : 1000
                            }
                        }
                    }
                }
            }
        }


#########################################################
# Background task implementation

class ReportingBackgroundTask(BackgroundTask):

    __action__ = "reporting"

    def run(self):
        """
        Execute the task as specified by the background_jon
        :return:
        """
        job = self.background_job
        params = job.params

        outdir = self.get_param(params, "outdir", "report_" + dates.today())
        fr = self.get_param(params, "from", "1970-01-01T00:00:00Z")
        to = self.get_param(params, "to", dates.now())

        job.add_audit_message("Saving reports to " + outdir)
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        prov_outfiles = provenance_reports(fr, to, outdir)
        cont_outfiles = content_reports(fr, to, outdir)
        refs = {}
        self.set_reference(refs, "provenance_outfiles", prov_outfiles)
        self.set_reference(refs, "content_outfiles", cont_outfiles)
        job.reference = refs

        msg = "Generated reports for period {x} to {y}".format(x=fr, y=to)
        job.add_audit_message(msg)

        send_email = self.get_param(params, "email", False)
        if send_email:
            ref_fr = dates.reformat(fr, app.config.get("DEFAULT_DATE_FORMAT"), "%Y-%m-%d")
            ref_to = dates.reformat(to, app.config.get("DEFAULT_DATE_FORMAT"), "%Y-%m-%d")
            archive_name = "reports_" + ref_fr + "_to_" + ref_to
            email_archive(outdir, archive_name)
            job.add_audit_message("email alert sent")
        else:
            job.add_audit_message("no email alert sent")

    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        :return:
        """
        failed = self.background_job.is_failed()
        if not failed:
            return

        params = self.background_job.params
        outdir = self.get_param(params, "outdir")

        if outdir is not None and os.path.exists(outdir):
            shutil.rmtree(outdir)

        self.background_job.add_audit_message("Deleted directory {x} due to job failure".format(x=outdir))

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """

        job = models.BackgroundJob()
        job.user = username
        job.action = cls.__action__

        params = {}
        cls.set_param(params, "outdir", kwargs.get("outdir", "report_" + dates.today()))
        cls.set_param(params, "from", kwargs.get("from_date", "1970-01-01T00:00:00Z"))
        cls.set_param(params, "to", kwargs.get("to_date", dates.now()))
        cls.set_param(params, "email", kwargs.get("email", False))
        job.params = params

        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        run_reports.schedule(args=(background_job.id,), delay=10)


@main_queue.periodic_task(schedule("reporting"))
@write_required(script=True)
def scheduled_reports():
    user = app.config.get("SYSTEM_USERNAME")
    mail = bool(app.config.get("REPORTS_EMAIL_TO", False))                          # Send email if recipient configured
    outdir = app.config.get("REPORTS_BASE_DIR")
    outdir = os.path.join(outdir, dates.today())
    job = ReportingBackgroundTask.prepare(user, outdir=outdir, email=mail)
    ReportingBackgroundTask.submit(job)


@main_queue.task()
@write_required(script=True)
def run_reports(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = ReportingBackgroundTask(job)
    BackgroundApi.execute(task)
