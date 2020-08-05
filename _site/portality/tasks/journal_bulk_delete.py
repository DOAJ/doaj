from copy import deepcopy
import json

from flask_login import current_user

from portality import models, lock
from portality.core import app

from portality.tasks.redis_huey import main_queue
from portality.decorators import write_required

from portality.background import AdminBackgroundTask, BackgroundApi, BackgroundException, BackgroundSummary


def journal_bulk_delete_manage(selection_query, dry_run=True):

    estimates = JournalBulkDeleteBackgroundTask.estimate_delete_counts(selection_query)

    if dry_run:
        JournalBulkDeleteBackgroundTask.check_admin_privilege(current_user.id)
        return BackgroundSummary(None, affected={"journals" : estimates["journals-to-be-deleted"], "articles" : estimates["articles-to-be-deleted"]})

    ids = JournalBulkDeleteBackgroundTask.resolve_selection_query(selection_query)
    job = JournalBulkDeleteBackgroundTask.prepare(
        current_user.id,
        selection_query=selection_query,
        ids=ids
    )
    JournalBulkDeleteBackgroundTask.submit(job)

    job_id = None
    if job is not None:
        job_id = job.id
    return BackgroundSummary(job_id, affected={"journals" : estimates["journals-to-be-deleted"], "articles" : estimates["articles-to-be-deleted"]})


class JournalBulkDeleteBackgroundTask(AdminBackgroundTask):

    __action__ = "journal_bulk_delete"

    @classmethod
    def _job_parameter_check(cls, params):
        # we definitely need "ids" defined
        return bool(cls.get_param(params, 'ids'))

    def run(self):
        """
        Execute the task as specified by the background_job
        :return:
        """
        job = self.background_job
        params = job.params

        ids = self.get_param(params, 'ids')

        if not self._job_parameter_check(params):
            raise BackgroundException("{}.run run without sufficient parameters".format(self.__class__.__name__))

        # repeat the estimations and log what they were at the time the job ran, in addition to what the user saw
        # when requesting the job in journal_bulk_delete_manage
        estimates = self.estimate_delete_counts(json.loads(job.reference['selection_query']))
        job.add_audit_message("About to delete an estimated {} journals with {} articles associated with their ISSNs."
                              .format(estimates['journals-to-be-deleted'], estimates['articles-to-be-deleted']))

        journal_delete_q_by_ids = models.Journal.make_query(should_terms={'_id': ids}, consistent_order=False)
        models.Journal.delete_selected(query=journal_delete_q_by_ids, articles=True, snapshot_journals=True, snapshot_articles=True)
        job.add_audit_message("Deleted {} journals and all articles associated with their ISSNs.".format(len(ids)))

    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        :return:
        """
        job = self.background_job
        params = job.params
        ids = self.get_param(params, 'ids')
        username = job.user

        lock.batch_unlock('journal', ids, username)

    @classmethod
    def estimate_delete_counts(cls, selection_query):
        jtotal = models.Journal.hit_count(selection_query, consistent_order=False)
        issns = models.Journal.issns_by_query(selection_query)
        atotal = models.Article.count_by_issns(issns)
        return {'journals-to-be-deleted': jtotal, 'articles-to-be-deleted': atotal}

    @classmethod
    def resolve_selection_query(cls, selection_query):
        q = deepcopy(selection_query)
        q["_source"] = False
        iterator = models.Journal.iterate(q=q, page_size=5000, wrap=False)
        return [j['_id'] for j in iterator]

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """

        super(JournalBulkDeleteBackgroundTask, cls).prepare(username, **kwargs)

        # first prepare a job record
        job = models.BackgroundJob()
        job.user = username
        job.action = cls.__action__
        job.reference = {'selection_query': json.dumps(kwargs['selection_query'])}

        params = {}
        cls.set_param(params, 'ids', kwargs['ids'])

        if not cls._job_parameter_check(params):
            raise BackgroundException("{}.prepare run without sufficient parameters".format(cls.__name__))

        job.params = params

        # now ensure that we have the locks for all the records, if they are lockable
        # will raise an exception if this fails
        lock.batch_lock('journal', kwargs['ids'], username, timeout=app.config.get("BACKGROUND_TASK_LOCK_TIMEOUT", 3600))

        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save(blocking=True)
        journal_bulk_delete.schedule(args=(background_job.id,), delay=10)


@main_queue.task()
@write_required(script=True)
def journal_bulk_delete(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = JournalBulkDeleteBackgroundTask(job)
    BackgroundApi.execute(task)
