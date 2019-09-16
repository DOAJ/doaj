import esprit, os, shutil, gzip, uuid
from portality import models
from portality.core import app
from portality.lib.anon import basic_hash, anon_name, anon_email
from portality.lib.dataobj import DataStructureException
from portality.lib import dates
from portality.store import StoreFactory


def _anonymise_email(record):
    record.set_email(anon_email(record.email))
    return record


def _anonymise_admin(record):
    new_email = anon_email(record.get_latest_contact_email())
    record.remove_contacts()
    record.add_contact(anon_name(), new_email)
    for note in record.notes[:]:
        record.remove_note(note)
        record.add_note(basic_hash(note['note']))

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
    sug.set_suggester(anon_name(), anon_email(sug.suggester['email']))
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

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-l", "--limit", type=int, help="Number of records to export from each type. If you specify e.g. 100, then only the first 100 accounts, 100 journals, 100 articles etc. will be exported. The \"first\" 100 will be ordered by whatever the esprit iterate functionality uses as default ordering, usually alphabetically by record id.")
    parser.add_argument("-c", "--clean", action="store_true", help="Clean any pre-existing output before continuing")
    parser.add_argument("-b", "--batch", default=100000, type=int, help="Output batch sizes")
    args = parser.parse_args()
    if args.limit > 0:
        limit = args.limit
    else:
        limit = None

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    tmpStore = StoreFactory.tmp()
    mainStore = StoreFactory.get("anon_data")
    container = app.config.get("STORE_ANON_DATA_CONTAINER")

    if args.clean:
        mainStore.delete_container(container)

    for type_ in esprit.raw.list_types(connection=conn):
        filename = type_ + ".bulk"
        output_file = tmpStore.path(container, filename, create_container=True, must_exist=False)
        print((dates.now() + " " + type_ + " => " + output_file + ".*"))
        if type_ in anonymisation_procedures:
            transform = anonymisation_procedures[type_]
            filenames = esprit.tasks.dump(conn, type_, limit=limit, transform=transform,
                                          out_template=output_file, out_batch_sizes=args.batch, out_rollover_callback=_copy_on_complete,
                                          es_bulk_fields=["_id"])
        else:
            filenames = esprit.tasks.dump(conn, type_, limit=limit,
                                          out_template=output_file, out_batch_sizes=args.batch, out_rollover_callback=_copy_on_complete,
                                          es_bulk_fields=["_id"])

        print((dates.now() + " done\n"))

    tmpStore.delete_container(container)

