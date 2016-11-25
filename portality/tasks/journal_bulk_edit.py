from flask_login import current_user
from portality import models, lock
from portality.core import app

from portality.tasks.redis_huey import main_queue
from portality.decorators import write_required

from portality.background import BackgroundTask, BackgroundApi


def journal_manage(selection_query, dry_run=False, editor_group='', note=None):

    ids = JournalBulkEditBackgroundTask.resolve_selection_query(selection_query)
    if dry_run:
        return len(ids)

    note = note if note else []
    job = JournalBulkEditBackgroundTask.prepare(
        current_user.id,
        selection_query=selection_query,
        dry_run=dry_run,
        editor_group=editor_group,
        note=note,
        ids=ids
    )
    JournalBulkEditBackgroundTask.submit(job)

    return len(ids)


class JournalBulkEditBackgroundTask(BackgroundTask):

    __action__ = "journal_bulk_edit"

    def run(self):
        """
        Execute the task as specified by the background_jon
        :return:
        """
        job = self.background_job
        params = job.params

        ids = self.get_param(params, 'ids')
        editor_group = self.get_param(params, 'editor_group')
        note = self.get_param(params, 'note')

        if not self.get_param(params, 'ids') \
                and not self.get_param(params, 'editor_group') \
                and not self.get_param(params, 'note'):
            raise RuntimeError(u"{}.prepare run without sufficient parameters".format(self.__class__.__name__))

        for journal_id in ids:
            updated = False

            j = models.Journal.pull(journal_id)
            if j is None:
                job.add_audit_message(u"Journal with id {} does not exist, skipping".format(journal_id))
                continue
                
            if editor_group:
                job.add_audit_message(u"Setting editor_group to {x} for journal {y}".format(x=str(editor_group), y=journal_id))
                j.set_editor_group(editor_group)
                updated = True
                
            if note:
                job.add_audit_message(u"Adding note to for journal {y}".format(y=journal_id))
                j.add_note(note)
                updated = True
            
            if updated:
                j.save()

            job.add_audit_message(u"Journal {} set editor_group to {}".format(journal_id, editor_group))

    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        :return:
        """
        job = self.background_job
        params = job.params
        ids = self.get_param(params, 'ids')
        username = job.user

        lock.batch_unlock("journal", ids, username)

    @classmethod
    def resolve_selection_query(cls, selection_query):
        return [j['_id'] for j in models.Journal.query(q=selection_query)['hits']['hits']]

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """

        # first prepare a job record
        job = models.BackgroundJob()
        job.user = username
        job.action = cls.__action__
        job.reference = {'selection_query': kwargs['selection_query']}

        params = {}
        cls.set_param(params, 'ids', kwargs['ids'])
        cls.set_param(params, 'editor_group', kwargs.get('editor_group', ''))
        cls.set_param(params, 'note', kwargs.get('note', []))

        if not cls.get_param(params, 'ids')\
                and not cls.get_param(params, 'editor_group')\
                and not cls.get_param(params, 'note'):
            raise RuntimeError(u"{}.prepare run without sufficient parameters".format(cls.__name__))

        job.params = params

        # now ensure that we have the locks for all the journals
        # will raise an exception if this fails
        lock.batch_lock("journal", kwargs.get('ids', []), username, timeout=app.config.get("BACKGROUND_TASK_LOCK_TIMEOUT", 3600))

        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        journal_bulk_edit.schedule(args=(background_job.id,), delay=10)


@main_queue.task()
@write_required(script=True)
def journal_bulk_edit(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = JournalBulkEditBackgroundTask(job)
    BackgroundApi.execute(task)
