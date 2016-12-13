from copy import deepcopy
import json

from flask_login import current_user

from portality import models, lock
from portality.core import app

from portality.tasks.redis_huey import main_queue
from portality.decorators import write_required

from portality.background import BackgroundTask, BackgroundApi, BackgroundException


def suggestion_manage(selection_query, dry_run=True, editor_group='', note='', application_status=''):

    ids = SuggestionBulkEditBackgroundTask.resolve_selection_query(selection_query)
    if dry_run:
        return len(ids)

    job = SuggestionBulkEditBackgroundTask.prepare(
        current_user.id,
        selection_query=selection_query,
        editor_group=editor_group,
        note=note,
        application_status=application_status,
        ids=ids
    )

    SuggestionBulkEditBackgroundTask.submit(job)
    return len(ids)


class SuggestionBulkEditBackgroundTask(BackgroundTask):

    __action__ = "suggestion_bulk_edit"

    def run(self):
        """
        Execute the task as specified by the background_job
        :return:
        """
        job = self.background_job
        params = job.params

        ids = self.get_param(params, 'ids')
        editor_group = self.get_param(params, 'editor_group')
        note = self.get_param(params, 'note')
        application_status = self.get_param(params, 'application_status')

        if not self.get_param(params, 'ids') \
                and not self.get_param(params, 'editor_group') \
                and not self.get_param(params, 'note') \
                and not self.get_param(params, 'application_status'):
            raise RuntimeError(u"{}.prepare run without sufficient parameters".format(self.__class__.__name__))

        for suggestion_id in ids:
            updated = False

            s = models.Suggestion.pull(suggestion_id)
            if s is None:
                job.add_audit_message(u"Suggestion with id {} does not exist, skipping".format(suggestion_id))
                continue

            if editor_group:
                job.add_audit_message(u"Setting editor_group to {x} for suggestion {y}".format(x=str(editor_group), y=suggestion_id))
                s.set_editor_group(editor_group)
                updated = True

            if note:
                job.add_audit_message(u"Adding note to for suggestion {y}".format(y=suggestion_id))
                s.add_note(note)
                updated = True

            if application_status:
                s.set_application_status(application_status)
                updated = True

            if updated:
                s.save()

            job.add_audit_message(u"Suggestion {} set editor_group to {}".format(suggestion_id, editor_group))

    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        :return:
        """
        job = self.background_job
        params = job.params
        ids = self.get_param(params, 'ids')
        username = job.user

        lock.batch_unlock("suggestion", ids, username)

    @classmethod
    def resolve_selection_query(cls, selection_query):
        q = deepcopy(selection_query)
        q["_source"] = False
        return [s['_id'] for s in models.Suggestion.iterate(q=q, page_size=5000, wrap=False)]

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
        job.reference = {'selection_query': json.dumps(kwargs['selection_query'])}

        params = {}
        cls.set_param(params, 'ids', kwargs['ids'])
        cls.set_param(params, 'editor_group', kwargs.get('editor_group', ''))
        cls.set_param(params, 'note', kwargs.get('note', ''))
        cls.set_param(params, 'application_status', kwargs.get('application_status', ''))

        if not cls.get_param(params, 'ids')\
                and not cls.get_param(params, 'editor_group')\
                and not cls.get_param(params, 'note') \
                and not cls.get_param(params, 'application_status'):
            raise BackgroundException(u"{}.prepare run without sufficient parameters".format(cls.__name__))

        job.params = params

        # now ensure that we have the locks for all the suggestions
        # will raise an exception if this fails
        lock.batch_lock("suggestion", kwargs.get('ids', []), username, timeout=app.config.get("BACKGROUND_TASK_LOCK_TIMEOUT", 3600))

        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        suggestion_bulk_edit.schedule(args=(background_job.id,), delay=10)


@main_queue.task()
@write_required(script=True)
def suggestion_bulk_edit(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = SuggestionBulkEditBackgroundTask(job)
    BackgroundApi.execute(task)
