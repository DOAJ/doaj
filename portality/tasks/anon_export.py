import gzip
import os
import shutil
import uuid

from portality import background_helper
from portality import models, dao
from portality.background import BackgroundTask
from portality.core import app, es_connection
from portality.decorators import write_required
from portality.lib import dates
from portality.lib.anon import basic_hash, anon_email
from portality.lib.dataobj import DataStructureException
from portality.store import StoreFactory
from portality.tasks.redis_huey import main_queue, schedule

tmpStore = StoreFactory.tmp()
mainStore = StoreFactory.get("anon_data")
container = app.config.get("STORE_ANON_DATA_CONTAINER")


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


def anonymise_suggestion(record):
    try:
        sug = models.Suggestion(**record)
    except DataStructureException:
        return record

    sug = _anonymise_admin(sug)
    return sug.data


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
    'suggestion': anonymise_suggestion
}


def _copy_on_complete(path):
    name = os.path.basename(path)
    raw_size = os.path.getsize(path)
    print(("Compressing temporary file {x} (from {y} bytes)".format(x=path, y=raw_size)))
    zipped_name = name + ".gz"
    dir = os.path.dirname(path)
    zipped_path = os.path.join(dir, zipped_name)
    with open(path, "rb") as f_in, gzip.open(zipped_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    zipped_size = os.path.getsize(zipped_path)
    print(("Storing from temporary file {x} ({y} bytes)".format(x=zipped_name, y=zipped_size)))
    mainStore.store(container, name, source_path=zipped_path)
    tmpStore.delete_file(container, name)
    tmpStore.delete_file(container, zipped_name)


def run_anon_export(clean=False, limit=None, batch_size=100000):
    if clean:
        mainStore.delete_container(container)

    doaj_types = es_connection.indices.get(app.config['ELASTIC_SEARCH_DB_PREFIX'] + '*')
    type_list = [t[len(app.config['ELASTIC_SEARCH_DB_PREFIX']):] for t in doaj_types]

    for type_ in type_list:
        model = models.lookup_models_by_type(type_, dao.DomainObject)
        if not model:
            print("unable to locate model for " + type_)
            continue

        filename = type_ + ".bulk"
        output_file = tmpStore.path(container, filename, create_container=True, must_exist=False)
        print((dates.now() + " " + type_ + " => " + output_file + ".*"))
        iter_q = {"query": {"match_all": {}}, "sort": [{"_id": {"order": "asc"}}]}
        transform = None
        if type_ in anonymisation_procedures:
            transform = anonymisation_procedures[type_]

        # Use the model's dump method to write out this type to file
        _ = model.dump(q=iter_q, limit=limit, transform=transform, out_template=output_file, out_batch_sizes=batch_size,
                       out_rollover_callback=_copy_on_complete, es_bulk_fields=["_id"], scroll_keepalive='3m')

        print((dates.now() + " done\n"))

    tmpStore.delete_container(container)


class AnonExportBackgroundTask(BackgroundTask):
    __action__ = "anon_export"

    def run(self):
        # KTODO get params
        run_anon_export()
        self.background_job.add_audit_message("Anon export completed")

    def cleanup(self):
        pass

    @classmethod
    def prepare(cls, username, **kwargs):
        # KTODO set params
        # params = {}
        # cls.set_param(params, 'clean', False if "clean" not in kwargs else kwargs["clean"] if kwargs["clean"] is not None else False)
        # cls.set_param(params, "prune", False if "prune" not in kwargs else kwargs["prune"] if kwargs["prune"] is not None else False)
        # cls.set_param(params, "types", "all" if "types" not in kwargs else kwargs["types"] if kwargs["types"] in ["all", "journal", "article"] else "all")
        return background_helper.create_job(username=username,
                                            action=cls.__action__)

    @classmethod
    def submit(cls, background_job):
        background_job.save()
        anon_export.schedule(args=(background_job.id,), delay=10)


@main_queue.periodic_task(schedule(AnonExportBackgroundTask.__action__))
@write_required(script=True)
def scheduled_anon_export():
    # KTODO assign params
    background_helper.submit_by_bg_task_type(AnonExportBackgroundTask)


@main_queue.task()
@write_required(script=True)
def anon_export(job_id):
    background_helper.execute_by_job_id(job_id, AnonExportBackgroundTask)
