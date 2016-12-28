from portality import models
from portality.clcsv import UnicodeWriter
from portality.lib import dates
from portality import datasets
from portality.core import app

from portality.background import BackgroundApi, BackgroundTask
from portality.tasks.redis_huey import main_queue, schedule
from portality.decorators import write_required

import codecs, os, shutil


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

    filename = "applications_by_year_by_country__" + fr + "_to_" + to + "__on_" + dates.now() + ".csv"
    outfiles = []
    outfile = os.path.join(outdir, filename)
    outfiles.append(outfile)
    with codecs.open(outfile, "wb", "utf-8") as f:
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
                            "terms" : {
                                "field" : "bibjson.country.exact",
                                "size" : 1000
                            }
                        }
                    }
                }
            }
        }

def email(data_dir, archv_name):
    """
    Compress and email the reports to the specified email address.
    :param data_dir: Directory containing the reports
    :param archv_name: Filename for the archive and resulting email attachment
    """
    import shutil
    from portality import app_email
    from portality.core import app

    email_to = app.config.get('REPORTS_EMAIL_TO', ['feedback@doaj.org'])
    email_from = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
    email_sub = app.config.get('SERVICE_NAME', '') + ' - generated {0}'.format(archv_name)
    msg = "Attached: {0}.zip\n".format(archv_name)

    # Create an archive of the reports
    archv = shutil.make_archive(archv_name, "zip", root_dir=data_dir)

    # Read the archive to create an attachment, send it with the app email
    with open(archv) as f:
        dat = f.read()
        attach = [app_email.make_attachment(filename=archv_name, content_type='application/zip', data=dat)]
        app_email.send_mail(to=email_to, fro=email_from, subject=email_sub, msg_body=msg, files=attach)

    # Clean up the archive
    os.remove(archv)

#########################################################
## Background task implementation

class ReportingBackgroundTask(BackgroundTask):

    __action__ = "reporting"

    def run(self):
        """
        Execute the task as specified by the background_jon
        :return:
        """
        job = self.background_job
        params = job.params

        outdir = params.get("reporting__outdir", "report_" + dates.now())
        fr = params.get("reporting__from", "1970-01-01T00:00:00Z")
        to = params.get("reporting__to", dates.now())

        job.add_audit_message("Saving reports to " + outdir)
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        prov_outfiles = provenance_reports(fr, to, outdir)
        cont_outfiles = content_reports(fr, to, outdir)
        job.add_reference("reporting__provenance_outfiles", prov_outfiles)
        job.add_reference("reporting__content_outfiles", cont_outfiles)

        msg = u"Generated reports for period {x} to {y}".format(x=fr, y=to)
        job.add_audit_message(msg)

        send_email = params.get("reporting__email", False)
        if send_email:
            archive_name = "reports_" + fr + "_to_" + to
            email(outdir, archive_name)
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
        outdir = params.get("reporting__outdir")

        if outdir is not None and os.path.exists(outdir):
            shutil.rmtree(outdir)

        self.background_job.add_audit_message(u"Deleted directory {x} due to job failure".format(x=outdir))

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

        params ={}
        params["reporting__outdir"] = kwargs.get("outdir", "report_" + dates.now())
        params["reporting__from"] = kwargs.get("from_date", "1970-01-01T00:00:00Z")
        params["reporting__to"] = kwargs.get("to_date", dates.now())
        params["reporting__email"] = kwargs.get("email", False)
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
    outdir = app.config.get("REPORTS_BASE_DIR")
    outdir = os.path.join(outdir, dates.now())
    job = ReportingBackgroundTask.prepare(user, outdir=outdir)
    ReportingBackgroundTask.submit(job)

@main_queue.task()
@write_required(script=True)
def run_reports(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = ReportingBackgroundTask(job)
    BackgroundApi.execute(task)
