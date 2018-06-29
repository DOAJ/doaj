import esprit
from portality.core import app
from portality.lib.anon import basic_hash, anon_name, anon_email


def anonymise_email(record):
    if 'email' in record:
        record['email'] = anon_email(record['email'])
    return record


def anonymise_admin(record):
    if 'admin' in record:
        if 'contact' in record['admin']:
            if 'email' in record['admin']['contact']:
                record['admin']['contact']['email'] = anon_email(record['admin']['contact']['email'])
            if 'name' in record['admin']['contact']:
                record['admin']['contact']['name'] = anon_name(record['admin']['contact']['name'])

        if 'notes' in record['admin']:
            for note in record['admin']['notes']:
                note['note'] = basic_hash(note['note'])

    return record


def anonymise_account(record):
    anonymise_email(record)
    return record


def anonymise_journal(record):
    anonymise_admin(record)
    return record


def anonymise_suggestion(record):
    anonymise_admin(record)
    if 'suggestion' in record:
        if 'suggester' in record['suggestion']:
            if 'email' in record['suggestion']['suggester']:
                record['suggestion']['suggester']['email'] = anon_email(record['suggestion']['suggester']['email'])
            if 'name' in record['suggestion']['suggester']:
                record['suggestion']['suggester']['name'] = anon_name(record['suggestion']['suggester']['name'])
    return record


def anonymise_background_job(record):
    if 'params' in record:
        if 'suggestion_bulk_edit__note' in record['params']:
            record['params']['suggestion_bulk_edit__note'] =\
                basic_hash(record['params']['suggestion_bulk_edit__note'])

    return record


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
