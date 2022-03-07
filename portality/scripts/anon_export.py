# FIXME: this has been speedily upgraded following ES upgrade, will need another pass to strip out esprit fully. (SE 2022-02-25)

import os, shutil, gzip, uuid, json

from portality import models, dao
from portality.core import app, es_connection
from portality.lib.anon import basic_hash, anon_email
from portality.lib.dataobj import DataStructureException
from portality.lib import dates
from portality.store import StoreFactory
from portality.util import ipt_prefix
import sys

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


def dump(type, q=None, page_size=1000, limit=None,
         out=None, out_template=None, out_batch_sizes=100000, out_rollover_callback=None,
         transform=None,
         es_bulk_format=True, idkey='id', es_bulk_fields=None):

    q = q if q is not None else {"query": {"match_all": {}}}

    filenames = []
    n = 1
    current_file = None
    if out_template is not None:
        current_file = out_template + "." + str(n)
        filenames.append(current_file)
    if out is None and current_file is not None:
        out = open(current_file, "w")
    else:
        out = sys.stdout

    model = models.lookup_models_by_type(type, dao.DomainObject)
    if not model:
        raise Exception("unable to locate model for " + type)

    count = 0
    for record in model.scroll(q, page_size=page_size, limit=limit, wrap=False):
        if transform is not None:
            record = transform(record)

        if es_bulk_format:
            kwargs = {}
            if es_bulk_fields is None:
                es_bulk_fields = ["_id", "_index", "_type"]
            for key in es_bulk_fields:
                if key == "_id":
                    kwargs["idkey"] = idkey
                if key == "_index":
                    kwargs["index"] = model.index_name()
                if key == "_type":
                    kwargs["type_"] = type
            data = model.to_bulk_single_rec(record, **kwargs)
        else:
            data = json.dumps(record) + "\n"

        out.write(data)
        if out_template is not None:
            count += 1
            if count > out_batch_sizes:
                out.close()
                if out_rollover_callback is not None:
                    out_rollover_callback(current_file)

                count = 0
                n += 1
                current_file = out_template + "." + str(n)
                filenames.append(current_file)
                out = open(current_file, "w")

    if out_template is not None:
        out.close()
    if out_rollover_callback is not None:
        out_rollover_callback(current_file)

    return filenames


def anon_export(clean=False, limit=None, batch_size=100000):

    if clean:
        mainStore.delete_container(container)

    doaj_types = es_connection.indices.get(app.config['ELASTIC_SEARCH_DB_PREFIX'] + '*')
    type_list = [t[len(app.config['ELASTIC_SEARCH_DB_PREFIX']):] for t in doaj_types]

    # if app.config['ELASTIC_SEARCH_INDEX_PER_TYPE']:
    #     doaj_types = es_connection.indices.get(app.config['ELASTIC_SEARCH_DB_PREFIX'] + '*')
    #     type_list = [t[len(app.config['ELASTIC_SEARCH_DB_PREFIX']):] for t in doaj_types]
    #     print(type_list)
    # else:
    #     #type_list = esprit.raw.list_types(connection=es_connection)
    #     print("FIXME: shared index has been stripped out, use only with index per type")
    #     exit(1)
    #
    # esprit.raw.INDEX_PER_TYPE_SUBSTITUTE = app.config.get('INDEX_PER_TYPE_SUBSTITUTE', '_doc')          # fixme, this is gum and tape.
    # conn = esprit.raw.Connection(app.config.get("ELASTIC_SEARCH_HOST"), index='')

    for type_ in type_list:
        filename = type_ + ".bulk"
        output_file = tmpStore.path(container, filename, create_container=True, must_exist=False)
        print((dates.now() + " " + type_ + " => " + output_file + ".*"))
        iter_q = {"query": {"match_all": {}}, "sort": [{"_id": {"order": "asc"}}]}
        transform = None
        if type_ in anonymisation_procedures:
            transform = anonymisation_procedures[type_]
            # filenames = esprit.tasks.dump(conn, ipt_prefix(type_), q=iter_q, limit=limit, transform=transform,
            #                               out_template=output_file, out_batch_sizes=args.batch, out_rollover_callback=_copy_on_complete,
            #                               es_bulk_fields=["_id"])
        filenames = dump(type_, q=iter_q, limit=limit, transform=transform, out_template=output_file, out_batch_sizes=batch_size, out_rollover_callback=_copy_on_complete,
                    es_bulk_fields=["_id"])

        print((dates.now() + " done\n"))

    tmpStore.delete_container(container)


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-l", "--limit", type=int, help="Number of records to export from each type. If you specify e.g. 100, then only the first 100 accounts, 100 journals, 100 articles etc. will be exported. The \"first\" 100 will be ordered by whatever the esprit iterate functionality uses as default ordering, usually alphabetically by record id.")
    parser.add_argument("-c", "--clean", action="store_true", help="Clean any pre-existing output before continuing")
    parser.add_argument("-b", "--batch", default=100000, type=int, help="Output batch sizes")
    args = parser.parse_args()
    if args.limit is not None and args.limit > 0:
        limit = args.limit
    else:
        limit = None

    anon_export(args.clean, limit, args.batch)

