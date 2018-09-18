import esprit, os, shutil
from portality import models
from portality.core import app
from portality.lib.anon import basic_hash, anon_name, anon_email
from portality.lib.dataobj import DataStructureException
from portality.lib import dates


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

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-l", "--limit", type=int, help="Number of records to export from each type. If you specify e.g. 100, then only the first 100 accounts, 100 journals, 100 articles etc. will be exported. The \"first\" 100 will be ordered by whatever the esprit iterate functionality uses as default ordering, usually alphabetically by record id.")
    parser.add_argument("-o", "--outdir", required=True, help="Directory to output results to")
    parser.add_argument("-c", "--clean", action="store_true", required=True, help="Clean the output directory before continuing")
    args = parser.parse_args()
    if args.limit > 0:
        limit = args.limit
    else:
        limit = None

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    if args.clean and os.path.exists(args.outdir):
        shutil.rmtree(args.outdir)
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    for type_ in esprit.raw.list_types(connection=conn):
        output_file = os.path.join(args.outdir, type_ + ".bulk")
        print(dates.now() + " " + type_ + " => " + output_file)
        if type_ in anonymisation_procedures:
            transform = anonymisation_procedures[type_]
            with open(output_file, 'wb') as o:
                esprit.tasks.dump(conn, type_, transform=transform, limit=limit, out=o)
        else:
            with open(output_file, 'wb') as o:
                esprit.tasks.dump(conn, type_, limit=limit, out=o)
        print(dates.now() + " anonymised\n")

