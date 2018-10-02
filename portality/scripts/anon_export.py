import esprit, os, shutil
from portality import models
from portality.core import app
from portality.lib.anon import basic_hash, anon_name, anon_email
from portality.lib.dataobj import DataStructureException
from portality.lib import dates
from portality.store import StoreFactory
from portality import constants


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


# transform functions - return the JSON data source since
# esprit doesn't understand our model classes

def anonymise_account(record):
    try:
        a = models.Account(**record)
    except DataStructureException:
        return record

    return _anonymise_email(a).data


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
    print("Storing from temporary file {x}".format(x=path))
    name = os.path.basename(path)
    mainStore.store(container, name, source_path=path)
    tmpStore.delete(container, name)

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-l", "--limit", type=int, help="Number of records to export from each type. If you specify e.g. 100, then only the first 100 accounts, 100 journals, 100 articles etc. will be exported. The \"first\" 100 will be ordered by whatever the esprit iterate functionality uses as default ordering, usually alphabetically by record id.")
    parser.add_argument("-c", "--clean", action="store_true", required=True, help="Clean any pre-existing output before continuing")
    parser.add_argument("-b", "--batch", default=100000, type=int, help="Output batch sizes")
    args = parser.parse_args()
    if args.limit > 0:
        limit = args.limit
    else:
        limit = None

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    tmpStore = StoreFactory.tmp()
    mainStore = StoreFactory.get("anon_data")
    container = container = constants.STORE_ANON_DATA

    if args.clean:
        mainStore.delete(container)

    for type_ in esprit.raw.list_types(connection=conn):
        filename = type_ + ".bulk"
        output_file = tmpStore.path(container, filename, create_container=True, must_exist=False)
        print(dates.now() + " " + type_ + " => " + output_file + ".*")
        if type_ in anonymisation_procedures:
            transform = anonymisation_procedures[type_]
            filenames = esprit.tasks.dump(conn, type_, limit=limit, transform=transform,
                                          out_template=output_file, out_batch_sizes=args.batch, out_rollover_callback=_copy_on_complete,
                                          es_bulk_fields=["_id"])
        else:
            filenames = esprit.tasks.dump(conn, type_, limit=limit,
                                          out_template=output_file, out_batch_sizes=args.batch, out_rollover_callback=_copy_on_complete,
                                          es_bulk_fields=["_id"])

        print(dates.now() + " done\n")

    tmpStore.delete(container)

