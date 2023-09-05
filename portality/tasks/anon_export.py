import functools
import gzip
import os
import shutil
import uuid
from typing import Callable, NoReturn

from portality import models, dao
from portality.background import BackgroundTask
from portality.core import app, es_connection
from portality.lib import dates
from portality.lib.anon import basic_hash, anon_email
from portality.lib.dataobj import DataStructureException
from portality.store import StoreFactory
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import long_running


def _anonymise_email(record):
    record.set_email(anon_email(record.email))
    return record


def _anonymise_admin(record):
    for note in record.notes[:]:
        record.remove_note(note)
        record.add_note(basic_hash(note['note']), id=note["id"])

    return record


def _reset_api_key(record):
    if record.api_key is not None:
        record.generate_api_key()
    return record


def _reset_password(record):
    record.set_password(uuid.uuid4().hex)
    return record


# transform functions - return the JSON data source since
# esprit doesn't understand our model classes
def anonymise_account(record):
    try:
        a = models.Account(**record)
    except DataStructureException:
        return record

    a = _anonymise_email(a)
    a = _reset_api_key(a)
    a = _reset_password(a)

    return a.data


def anonymise_journal(record):
    try:
        j = models.Journal(**record)
    except DataStructureException:
        return record

    return _anonymise_admin(j).data


def anonymise_application(record):
    try:
        appl = models.Application(**record)
    except DataStructureException:
        return record

    appl = _anonymise_admin(appl)
    return appl.data


def anonymise_background_job(record):
    try:
        bgjob = models.BackgroundJob(**record)
    except DataStructureException:
        return record

    if bgjob.params and 'suggestion_bulk_edit__note' in bgjob.params:
        bgjob.params['suggestion_bulk_edit__note'] = basic_hash(bgjob.params['suggestion_bulk_edit__note'])

    return bgjob.data


anonymisation_procedures = {
    'account': anonymise_account,
    'background_job': anonymise_background_job,
    'journal': anonymise_journal,
    'application': anonymise_application
}


def _copy_on_complete(path, logger_fn, tmpStore, mainStore, container):
    name = os.path.basename(path)
    raw_size = os.path.getsize(path)
    logger_fn(("Compressing temporary file {x} (from {y} bytes)".format(x=path, y=raw_size)))
    zipped_name = name + ".gz"
    dir = os.path.dirname(path)
    zipped_path = os.path.join(dir, zipped_name)
    with open(path, "rb") as f_in, gzip.open(zipped_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    zipped_size = os.path.getsize(zipped_path)
    logger_fn(("Storing from temporary file {x} ({y} bytes)".format(x=zipped_name, y=zipped_size)))
    mainStore.store(container, name, source_path=zipped_path)
    tmpStore.delete_file(container, name)
    tmpStore.delete_file(container, zipped_name)


def run_anon_export(tmpStore, mainStore, container, clean=False, limit=None, batch_size=100000,
                    logger_fn: Callable[[str], NoReturn] = None):
    if logger_fn is None:
        logger_fn = print
    if clean:
        mainStore.delete_container(container)

    doaj_types = es_connection.indices.get(app.config['ELASTIC_SEARCH_DB_PREFIX'] + '*')
    type_list = [t[len(app.config['ELASTIC_SEARCH_DB_PREFIX']):] for t in doaj_types]

    for type_ in type_list:
        model = models.lookup_models_by_type(type_, dao.DomainObject)
        if not model:
            logger_fn("unable to locate model for " + type_)
            continue

        filename = type_ + ".bulk"
        output_file = tmpStore.path(container, filename, create_container=True, must_exist=False)
        logger_fn((dates.now_str() + " " + type_ + " => " + output_file + ".*"))
        iter_q = {"query": {"match_all": {}}, "sort": [{"_id": {"order": "asc"}}]}
        transform = None
        if type_ in anonymisation_procedures:
            transform = anonymisation_procedures[type_]

        # Use the model's dump method to write out this type to file
        out_rollover_fn = functools.partial(_copy_on_complete, logger_fn=logger_fn, tmpStore=tmpStore,
                                            mainStore=mainStore, container=container)
        _ = model.dump(q=iter_q, limit=limit, transform=transform, out_template=output_file, out_batch_sizes=batch_size,
                       out_rollover_callback=out_rollover_fn, es_bulk_fields=["_id"], scroll_keepalive=app.config.get('TASKS_ANON_EXPORT_SCROLL_TIMEOUT', '5m'))

        logger_fn((dates.now_str() + " done\n"))

    tmpStore.delete_container(container)


class AnonExportBackgroundTask(BackgroundTask):
    """
    ~~AnonExport:Feature->BackgroundTask:Process~~
    """
    __action__ = "anon_export"

    def run(self):
        kwargs = self.create_raw_param_dict(self.background_job.params,
                                            ['clean', 'limit', 'batch_size'])
        kwargs['logger_fn'] = self.background_job.add_audit_message

        tmpStore = StoreFactory.tmp()
        mainStore = StoreFactory.get("anon_data")
        container = app.config.get("STORE_ANON_DATA_CONTAINER")

        run_anon_export(tmpStore, mainStore, container, **kwargs)
        self.background_job.add_audit_message("Anon export completed")

    def cleanup(self):
        pass

    @classmethod
    def prepare(cls, username, **kwargs):
        params = {}
        cls.set_param(params, 'clean', background_helper.get_value_safe('clean', False, kwargs))
        cls.set_param(params, "limit", kwargs.get('limit'))
        cls.set_param(params, "batch_size", background_helper.get_value_safe('batch_size', 100000, kwargs))
        return background_helper.create_job(username=username,
                                            action=cls.__action__,
                                            params=params,
                                            queue_id=huey_helper.queue_id, )

    @classmethod
    def submit(cls, background_job):
        background_job.save()
        anon_export.schedule(args=(background_job.id,), delay=10)


huey_helper = AnonExportBackgroundTask.create_huey_helper(long_running)


@huey_helper.register_schedule
def scheduled_anon_export():
    background_helper.submit_by_bg_task_type(AnonExportBackgroundTask,
                                             clean=app.config.get("TASKS_ANON_EXPORT_CLEAN", False),
                                             limit=app.config.get("TASKS_ANON_EXPORT_LIMIT", None),
                                             batch_size=app.config.get("TASKS_ANON_EXPORT_BATCH_SIZE", 100000))


@huey_helper.register_execute(is_load_config=False)
def anon_export(job_id):
    background_helper.execute_by_job_id(job_id, AnonExportBackgroundTask)
