from copy import deepcopy
import json
from datetime import datetime

from flask_login import current_user

from portality import models, lock
from portality.core import app
from portality.formcontext import formcontext

from portality.tasks.redis_huey import main_queue
from portality.decorators import write_required

from portality.background import AdminBackgroundTask, BackgroundApi, BackgroundException, BackgroundSummary


def suggestion_manage(selection_query, dry_run=True, editor_group='', note='', application_status=''):
    ids = SuggestionBulkEditBackgroundTask.resolve_selection_query(selection_query)
    if dry_run:
        SuggestionBulkEditBackgroundTask.check_admin_privilege(current_user.id)
        return BackgroundSummary(None, affected={"applications" : len(ids)})
        # return len(ids)

    job = SuggestionBulkEditBackgroundTask.prepare(
        current_user.id,
        selection_query=selection_query,
        editor_group=editor_group,
        note=note,
        application_status=application_status,
        ids=ids
    )
    SuggestionBulkEditBackgroundTask.submit(job)

    affected = len(ids)
    job_id = None
    if job is not None:
        job_id = job.id
    return BackgroundSummary(job_id, affected={"applications" : affected})

    # return len(ids)


class SuggestionBulkEditBackgroundTask(AdminBackgroundTask):
    __action__ = "suggestion_bulk_edit"

    @classmethod
    def _job_parameter_check(cls, params):
        # we definitely need "ids" defined
        # we need at least one of, "editor_group" or "note" or "application_status"
        return bool(
            cls.get_param(params, 'ids') and \
            (cls.get_param(params, 'editor_group') or cls.get_param(params, 'note') or cls.get_param(params, 'application_status'))
        )

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

        if not self._job_parameter_check(params):
            raise BackgroundException("{}.run run without sufficient parameters".format(self.__class__.__name__))

        for suggestion_id in ids:
            updated = False

            s = models.Suggestion.pull(suggestion_id)

            if s is None:
                job.add_audit_message("Suggestion with id {} does not exist, skipping".format(suggestion_id))
                continue

            fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=s)

            if editor_group:
                job.add_audit_message(
                    "Setting editor_group to {x} for suggestion {y}".format(x=str(editor_group), y=suggestion_id))

                # set the editor group
                f = fc.form.editor_group
                f.data = editor_group

                # clear the editor
                ed = fc.form.editor
                ed.data = None

                updated = True

            if note:
                job.add_audit_message("Adding note to for suggestion {y}".format(y=suggestion_id))
                fc.form.notes.append_entry(
                    {'date': datetime.now().strftime(app.config['DEFAULT_DATE_FORMAT']), 'note': note}
                )
                updated = True

            if application_status:
                job.add_audit_message(
                    "Setting application_status to {x} for suggestion {y}".format(x=str(editor_group), y=suggestion_id))
                f = fc.form.application_status
                f.data = application_status
                updated = True

            if updated:
                if fc.validate():
                    try:
                        fc.finalise()
                    except formcontext.FormContextException as e:
                        job.add_audit_message(
                            "Form context exception while bulk editing suggestion {} :\n{}".format(suggestion_id, str(e)))
                else:
                    data_submitted = {}
                    for affected_field_name in list(fc.form.errors.keys()):
                        affected_field = getattr(fc.form, affected_field_name,
                                                 ' Field {} does not exist on form. '.format(affected_field_name))
                        if isinstance(affected_field, str):  # ideally this should never happen, an error should not be reported on a field that is not present on the form
                            data_submitted[affected_field_name] = affected_field
                            continue

                        data_submitted[affected_field_name] = affected_field.data
                    job.add_audit_message(
                        "Data validation failed while bulk editing suggestion {} :\n"
                        "{}\n\n"
                        "The data from the fields with the errors is:\n{}".format(
                            suggestion_id, json.dumps(fc.form.errors), json.dumps(data_submitted)
                        )
                    )

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
        iterator = models.Suggestion.iterate(q=q, page_size=5000, wrap=False)
        return [s['_id'] for s in iterator]

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """

        super(SuggestionBulkEditBackgroundTask, cls).prepare(username, **kwargs)

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

        if not cls._job_parameter_check(params):
            raise BackgroundException("{}.prepare run without sufficient parameters".format(cls.__name__))

        job.params = params

        # now ensure that we have the locks for all the suggestions
        # will raise an exception if this fails
        lock.batch_lock("suggestion", kwargs['ids'], username, timeout=app.config.get("BACKGROUND_TASK_LOCK_TIMEOUT", 3600))

        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save(blocking=True)
        suggestion_bulk_edit.schedule(args=(background_job.id,), delay=10)


@main_queue.task()
@write_required(script=True)
def suggestion_bulk_edit(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = SuggestionBulkEditBackgroundTask(job)
    BackgroundApi.execute(task)
