import datetime
import csv
import json

from portality.core import app
from portality import models,app_email

from portality.background import BackgroundTask


def _date():
    return (datetime.datetime.today() + datetime.timedelta(days=app.config.get('DISCONTINUED_DATE_DELTA', 1))).strftime(
        '%Y-%m-%d')
class DiscontinuedSoonQuery:
    @classmethod
    def query(cls):
        return {
            "query": {
                "bool": {
                    "filter": {
                        "bool" : {
                            "must": [
                                {"term" : {"bibjson.discontinued_date": _date()}}
                            ]
                        }
                    }
                }
            }
        }

# ~~FindDiscontinuedSoonBackgroundTask:Task~~

class FindDiscontinuedSoonBackgroundTask(BackgroundTask):
    __action__ = "find_discontinued_soon"

    def run(self):
        jdata = []

        for journal in models.Journal.iterate(q=DiscontinuedSoonQuery.query(), keepalive='5m', wrap=True):
            bibjson = journal.bibjson()
            owner = journal.owner
            account = models.Account.pull(owner)

            jdata.append({"id": journal.id,
                          "title":bibjson.title,
                          "eissn": bibjson.get_one_identifier(bibjson.E_ISSN),
                          "pissn": bibjson.get_one_identifier(bibjson.P_ISSN),
                          "account_email": account.email if account else "Not Found",
                          "publisher": bibjson.publisher})

        try:
            # send warning email about the service tag in article metadata detected
            to = app.config.get('SCRIPT_TAG_DETECTED_EMAIL_RECIPIENTS')
            fro = app.config.get("SYSTEM_EMAIL_FROM", "helpdesk@doaj.org")
            subject = app.config.get("SERVICE_NAME", "") + " - script tag detected in application metadata"
            es_type = "application"
            app_email.send_mail(to=to,
                                fro=fro,
                                subject=subject,
                                template_name="email/discontinue_soon.jinja2",
                                es_type=es_type,
                                days=app.config.get('DISCONTINUED_DATE_DELTA',1),
                                data=json.dumps({"data": jdata}, indent=4, separators=(',', ': ')))
        except app_email.EmailException:
            app.logger.exception('Error sending email with journals discountinuing soon - ' + jdata)

    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        :return:
        """
        pass

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """

        # first prepare a job record
        job = background_helper.create_job(username, cls.__action__,
                                           queue_id=huey_helper.queue_id, )
        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        find_discontinued_soon.schedule(args=(background_job.id,), delay=1)

huey_helper = RequestESBackupBackgroundTask.create_huey_helper(main_queue)

@huey_helper.register_schedule
def scheduled_find_discontinued_soon():
    user = app.config.get("SYSTEM_USERNAME")
    job = FindDiscontinuedSoonBackgroundTask.prepare(user)
    FindDiscontinuedSoonBackgroundTask.submit(job)


@huey_helper.register_execute(is_load_config=False)
def find_discontinued_soon(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = FindDiscontinuedSoonBackgroundTask(job)
    BackgroundApi.execute(task)
