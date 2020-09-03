from copy import deepcopy
import json
from datetime import datetime

from flask_login import current_user
from werkzeug.datastructures import MultiDict

from portality import models, lock
from portality.core import app
# from portality.formcontext import formcontext
from portality.forms.application_forms import JournalFormFactory

from portality.tasks.redis_huey import main_queue
from portality.decorators import write_required

from portality.background import AdminBackgroundTask, BackgroundApi, BackgroundException, BackgroundSummary


def journal_manage(selection_query, dry_run=True, editor_group='', note='', **kwargs):

    ids = JournalBulkEditBackgroundTask.resolve_selection_query(selection_query)
    if dry_run:
        JournalBulkEditBackgroundTask.check_admin_privilege(current_user.id)
        return BackgroundSummary(None, affected={"journals" : len(ids)})

    if kwargs is None:
        kwargs = {}
    if editor_group != "":
        kwargs["editor_group"] = editor_group

    job = JournalBulkEditBackgroundTask.prepare(
        current_user.id,
        selection_query=selection_query,
        note=note,
        ids=ids,
        replacement_metadata=kwargs
    )
    JournalBulkEditBackgroundTask.submit(job)

    affected = len(ids)
    job_id = None
    if job is not None:
        job_id = job.id
    return BackgroundSummary(job_id, affected={"journals" : affected})


class JournalBulkEditBackgroundTask(AdminBackgroundTask):

    __action__ = "journal_bulk_edit"

    @classmethod
    def _job_parameter_check(cls, params):
        # we definitely need "ids" defined
        # we need at least one of "editor_group" or "note" defined as well
        ids = cls.get_param(params, "ids")
        ids_valid = ids is not None and len(ids) > 0

        note = cls.get_param(params, "note")
        note_valid = note is not None

        metadata = cls.get_param(params, "replacement_metadata", "{}")
        metadata = json.loads(metadata)
        metadata_valid = len(metadata.keys()) > 0

        return ids_valid and (note_valid or metadata_valid)

    def run(self):
        """
        Execute the task as specified by the background_job
        :return:
        """
        job = self.background_job
        params = job.params

        if not self._job_parameter_check(params):
            raise BackgroundException("{}.run run without sufficient parameters".format(self.__class__.__name__))

        # get the parameters for the job
        ids = self.get_param(params, 'ids')
        note = self.get_param(params, 'note')
        metadata = json.loads(self.get_param(params, 'replacement_metadata', "{}"))

        # if there is metadata, validate it
        if len(metadata.keys()) > 0:
            formdata = MultiDict(metadata)
            formulaic_context = JournalFormFactory.context("bulk_edit")
            fc = formulaic_context.processor(formdata=formdata)
            if not fc.validate():
                raise BackgroundException("Unable to validate replacement metadata: " + json.dumps(metadata))

        for journal_id in ids:
            updated = False

            j = models.Journal.pull(journal_id)

            if j is None:
                job.add_audit_message("Journal with id {} does not exist, skipping".format(journal_id))
                continue

            formulaic_context = JournalFormFactory.context("admin")
            fc = formulaic_context.processor(source=j)

            # turn on the "all fields optional" flag, so that bulk tasks don't cause errors that the user iterface
            # would allow you to bypass
            fc.form.make_all_fields_optional.data = True

            if "editor_group" in metadata:
                fc.form.editor.data = None
            elif j.editor_group is not None:
                # FIXME: this is a bit of a stop-gap, pending a more substantial referential-integrity-like solution
                # if the editor group is not being changed, validate that the editor is actually in the editor group,
                # and if not, unset them
                eg = models.EditorGroup.pull_by_key("name", j.editor_group)
                if eg is not None:
                    all_eds = eg.associates + [eg.editor]
                    if j.editor not in all_eds:
                        fc.form.editor.data = None
                else:
                    # if we didn't find the editor group, this is broken anyway, so reset the editor data anyway
                    fc.form.editor.data = None

            for k, v in metadata.items():
                job.add_audit_message("Setting {f} to {x} for journal {y}".format(f=k, x=v, y=journal_id))
                fc.form[k].data = v
                updated = True

            if note:
                job.add_audit_message("Adding note to for journal {y}".format(y=journal_id))
                fc.form.notes.append_entry(
                    {'note_date': datetime.now().strftime(app.config['DEFAULT_DATE_FORMAT']), 'note': note}
                )
                updated = True
            
            if updated:
                if fc.validate():
                    try:
                        fc.finalise()
                    except Exception as e:
                        job.add_audit_message("Form context exception while bulk editing journal {} :\n{}".format(journal_id, str(e)))
                else:
                    data_submitted = {}
                    for affected_field_name in fc.form.errors.keys():
                        affected_field = getattr(fc.form, affected_field_name,
                                                 ' Field {} does not exist on form. '.format(affected_field_name))
                        if isinstance(affected_field, str):  # ideally this should never happen, an error should not be reported on a field that is not present on the form
                            data_submitted[affected_field_name] = affected_field
                            continue

                        data_submitted[affected_field_name] = affected_field.data
                    job.add_audit_message(
                        "Data validation failed while bulk editing journal {} :\n"
                        "{}\n\n"
                        "The data from the fields with the errors is:\n{}".format(
                            journal_id, json.dumps(fc.form.errors), json.dumps(data_submitted)
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

        lock.batch_unlock("journal", ids, username)

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

        super(JournalBulkEditBackgroundTask, cls).prepare(username, **kwargs)

        # first prepare a job record
        job = models.BackgroundJob()
        job.user = username
        job.action = cls.__action__

        refs = {}
        cls.set_reference(refs, "selection_query", json.dumps(kwargs['selection_query']))
        job.reference = refs

        params = {}

        # get the named parameters we know may be there
        cls.set_param(params, 'ids', kwargs['ids'])
        if "note" in kwargs and kwargs["note"] is not None and kwargs["note"] != "":
            cls.set_param(params, 'note', kwargs.get('note', ''))

        # get the metadata overwrites
        if "replacement_metadata" in kwargs:
            metadata = {}
            for k, v in kwargs["replacement_metadata"].items():
                if v is not None and v != "":
                    metadata[k] = v
            if len(metadata.keys()) > 0:
                cls.set_param(params, 'replacement_metadata', json.dumps(metadata))

        if not cls._job_parameter_check(params):
            raise BackgroundException("{}.prepare run without sufficient parameters".format(cls.__name__))

        job.params = params

        # now ensure that we have the locks for all the journals
        # will raise an exception if this fails
        lock.batch_lock("journal", kwargs['ids'], username, timeout=app.config.get("BACKGROUND_TASK_LOCK_TIMEOUT", 3600))

        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save(blocking=True)
        journal_bulk_edit.schedule(args=(background_job.id,), delay=10)


@main_queue.task()
@write_required(script=True)
def journal_bulk_edit(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = JournalBulkEditBackgroundTask(job)
    BackgroundApi.execute(task)
