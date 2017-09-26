""" Report on reapplications for issue https://github.com/DOAJ/doaj/issues/1376 - this is copy of reporting.py, but
will be discarded in time as reapplications were a one-off. """

from portality import models
from portality.clcsv import UnicodeWriter
from portality.lib import dates
from portality.lib.dataobj import DataStructureException

from portality.background import BackgroundApi, BackgroundTask
from portality.tasks.redis_huey import main_queue
from portality.decorators import write_required

import codecs, os, shutil, re


def reapplication_reports(outdir):
    pipeline = [
        RejectedReapplicationReporter(),
        NoReapplicationReporter(),
        ContinuationNoteReporter(),
        TickReporter()
    ]

    for j in models.Journal.all_in_doaj(page_size=1000):
        for filt in pipeline:
            filt.test(j)

    outfiles = []
    all_errors = {}
    for p in pipeline:
        table = p.tabulate()
        outfile = os.path.join(outdir, p.filename())
        outfiles.append(outfile)
        merge_errors(all_errors, p.errors)
        with codecs.open(outfile, "wb", "utf-8") as f:
            writer = UnicodeWriter(f)
            for row in table:
                writer.writerow(row)

    return outfiles, all_errors


def _tabulate_journal(report, entity_key):
    categories = report.values()[0].keys()
    categories.sort()
    table = [[entity_key] + categories]

    for k, v in report.iteritems():
        row = [k]
        for c in categories:
            row.append(v[c])
        table.append(row)
    return table


class JournalReporter(object):

    def __init__(self):
        self.report = {}
        self.errors = {}

    def include(self, j):
        self.report[j.id] = {
            'Title': j.bibjson().title,
            'EISSN': j.bibjson().get_one_identifier('eissn') or '',
            'PISSN': j.bibjson().get_one_identifier('pissn') or ''
        }

    def tabulate(self):
        return _tabulate_journal(self.report, "Journal ID")

    def test(self, j):
        raise NotImplementedError()

    def filename(self):
        raise NotImplementedError()


class RejectedReapplicationReporter(JournalReporter):

    def test(self, j):
        if j.current_application is not None:
            try:
                cur_app = models.Suggestion.pull(j.current_application)
                if cur_app is not None:
                    if cur_app.current_journal and cur_app.application_status == 'rejected':    # rejected reapplication
                        self.include(j)
            except DataStructureException as e:
                self.errors[j.id] = '1_journals_with_rejected_reapplication: Reapp {0} - DataStructureException: {1}'.format(j.current_application, e)

    def filename(self):
        return '1_journals_with_rejected_reapplication_on_' + dates.today() + '.csv'


class NoReapplicationReporter(JournalReporter):

    def test(self, j):
        if j.current_application is None and not j.is_ticked():
            self.include(j)

    def filename(self):
        return '2_journals_without_reapplications_on_' + dates.today() + '.csv'


class ContinuationNoteReporter(JournalReporter):

    notes_regex = re.compile('^Continuation automatically extracted from journal .* during migration$', re.IGNORECASE)

    def test(self, j):
        for n in j.notes:
            if self.notes_regex.match(n['note']):
                self.include(j)

    def filename(self):
        return '3_journals_with_continued_note_on_' + dates.today() + '.csv'


class TickReporter(JournalReporter):

    def test(self, j):
        if not j.is_ticked():
            self.include(j)

    def filename(self):
        return '4_journals_without_tick_on_' + dates.today() + '.csv'


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


def merge_errors(base, update):
    """ Copy the errors from update into base. """
    for k, v in update.iteritems():
        try:
            base[k].append(v)
        except KeyError:
            base[k] = [v]


#########################################################
# Background task implementation

class ReportingBackgroundTask(BackgroundTask):

    __action__ = "reapplication_reporting"

    def run(self):
        """
        Execute the task as specified by the background_job
        :return:
        """
        job = self.background_job
        params = job.params

        outdir = self.get_param(params, "outdir", "reapplication_report_" + dates.today())

        job.add_audit_message("Saving reports to " + outdir)
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        reapp_outfiles, errors = reapplication_reports(outdir)
        refs = {}
        self.set_reference(refs, "reapplication_outfiles", reapp_outfiles)
        job.reference = refs
        [job.add_audit_message('Journal {0} errors: {1}'.format(k, ', '.join(v))) for k, v in errors.iteritems()]

        msg = u"Generated reapplication reports as of {0}".format(dates.now())
        job.add_audit_message(msg)

        send_email = self.get_param(params, "email", False)
        if send_email:
            archive_name = "reapplication_reports_" + dates.today()
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
        outdir = self.get_param(params, "outdir")

        if outdir is not None and os.path.exists(outdir):
            shutil.rmtree(outdir)

        self.background_job.add_audit_message(u"Deleted directory {x} due to job failure".format(x=outdir))

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

        :param username: user to run this job as
        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """

        job = models.BackgroundJob()
        job.user = username
        job.action = cls.__action__

        params = {}
        cls.set_param(params, "outdir", kwargs.get("outdir", "reapplication_report_" + dates.today()))
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


@main_queue.task()
@write_required(script=True)
def run_reports(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = ReportingBackgroundTask(job)
    BackgroundApi.execute(task)
