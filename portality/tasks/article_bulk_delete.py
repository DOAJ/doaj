from copy import deepcopy
import json

from flask_login import current_user

from portality import models

from portality.tasks.redis_huey import main_queue
from portality.decorators import write_required
from portality.util import batch_up

from portality.background import AdminBackgroundTask, BackgroundApi, BackgroundException, BackgroundSummary


def article_bulk_delete_manage(selection_query, dry_run=True):

    if dry_run:
        ArticleBulkDeleteBackgroundTask.check_admin_privilege(current_user.id)
        estimate = ArticleBulkDeleteBackgroundTask.estimate_delete_counts(selection_query)
        return BackgroundSummary(None, affected={"articles" : estimate})

    ids = ArticleBulkDeleteBackgroundTask.resolve_selection_query(selection_query)
    job = ArticleBulkDeleteBackgroundTask.prepare(
        current_user.id,
        selection_query=selection_query,
        ids=ids
    )
    ArticleBulkDeleteBackgroundTask.submit(job)

    affected = len(ids)
    job_id = None
    if job is not None:
        job_id = job.id
    return BackgroundSummary(job_id, affected={"articles" : affected})


class ArticleBulkDeleteBackgroundTask(AdminBackgroundTask):

    BATCH_SIZE = 1000

    __action__ = "article_bulk_delete"

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
            raise BackgroundException(u"{}.run run without sufficient parameters".format(self.__class__.__name__))

        batches_count = len(ids) // self.BATCH_SIZE + (0 if len(ids) % self.BATCH_SIZE == 0 else 1)
        job.add_audit_message(u"About to delete {} articles in {} batches".format(len(ids), batches_count))

        for batch_num, batch in enumerate(batch_up(ids, self.BATCH_SIZE), start=1):
            article_delete_q_by_ids = models.Article.make_query(should_terms={'_id': batch}, consistent_order=False)
            models.Article.delete_selected(query=article_delete_q_by_ids, snapshot=True)
            job.add_audit_message(u"Deleted {} articles in batch {} of {}".format(len(batch), batch_num, batches_count))

        job.add_audit_message(u"Deleted {} articles".format(len(ids)))

    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        :return:
        """
        pass

    @classmethod
    def estimate_delete_counts(cls, selection_query):
        q = deepcopy(selection_query)
        res = models.Article.query(q=q, raise_es_errors=True)
        return res['hits']['total']

    @classmethod
    def resolve_selection_query(cls, selection_query):
        q = deepcopy(selection_query)
        q["_source"] = False
        iterator = models.Article.iterate(q=q, page_size=5000, wrap=False)
        return [j['_id'] for j in iterator]

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """

        super(ArticleBulkDeleteBackgroundTask, cls).prepare(username, **kwargs)

        # first prepare a job record
        job = models.BackgroundJob()
        job.user = username
        job.action = cls.__action__
        refs = {}
        cls.set_reference(refs, "selection_query", json.dumps(kwargs['selection_query']))
        job.reference = refs

        params = {}
        cls.set_param(params, 'ids', kwargs['ids'])

        if not cls._job_parameter_check(params):
            raise BackgroundException(u"{}.prepare run without sufficient parameters".format(cls.__name__))

        job.params = params

        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save(blocking=True)
        article_bulk_delete.schedule(args=(background_job.id,), delay=10)


@main_queue.task()
@write_required(script=True)
def article_bulk_delete(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = ArticleBulkDeleteBackgroundTask(job)
    BackgroundApi.execute(task)
