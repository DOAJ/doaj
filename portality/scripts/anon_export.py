import esprit
from portality import models
from portality.core import app
from portality.lib.anon import basic_hash, anon_name, anon_email


def anonymise_email(record):
    record.set_email(anon_email(record.email))
    return record


def anonymise_admin(record):
    new_email = anon_email(record.get_latest_contact_email())
    record.remove_contacts()
    record.add_contact(anon_name(), new_email)
    for note in record.notes[:]:
        record.remove_note(note)
        record.add_note(basic_hash(note['note']))

    return record


def anonymise_account(record):
    return anonymise_email(models.Account(**record))


def anonymise_journal(record):
    anonymise_admin(models.Journal(**record))
    return record


def anonymise_suggestion(record):
    sug = models.Suggestion(**record)
    sug = anonymise_admin(sug)
    sug.set_suggester(anon_name(), anon_email(sug.suggester['email']))
    return sug


def anonymise_background_job(record):
    bgjob = models.BackgroundJob(**record)
    bgjob.params['suggestion_bulk_edit__note'] = basic_hash(bgjob.params['suggestion_bulk_edit__note'])
    return bgjob


def anonymise_default(record):
    anonymise_email(record)
    anonymise_admin(record)
    return record

anonymisation_procedures = {
    '_default': anonymise_default,
    'account': anonymise_account,
    'background_job': anonymise_background_job,
    'journal': anonymise_journal,
    'suggestion': anonymise_suggestion
}

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-l", "--limit", type=int, help="Number of records to export from each type. If you specify e.g. 100, then only the first 100 accounts, 100 journals, 100 articles etc. will be exported. The \"first\" 100 will be ordered by whatever the esprit iterate functionality uses as default ordering, usually alphabetically by record id.")
    args = parser.parse_args()
    if args.limit > 0:
        limit = args.limit
    else:
        limit = None

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    for type_ in esprit.raw.list_types(connection=conn):
        transform = anonymisation_procedures[type_] if type_ in anonymisation_procedures else anonymisation_procedures['_default']
        esprit.tasks.dump(conn, type_, transform=transform, limit=limit)
