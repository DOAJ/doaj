import esprit
from portality.core import app
from portality.lib.anon import basic_hash, anon_name, anon_email


def anonymise_email(record):
    if 'email' in record:
        record['email'] = anon_email(record['email'])
    return record


def anonymise_admin(record):
    if 'admin' in record:
        if 'owner' in record['admin']:
            record['admin']['owner'] = basic_hash(record['admin']['owner'])

        if 'editor' in record['admin']:
            record['admin']['editor'] = basic_hash(record['admin']['editor'])

        if 'contact' in record['admin']:
            if 'email' in record['admin']['contact']:
                record['admin']['contact']['email'] = anon_email(record['admin']['contact']['email'])
            if 'name' in record['admin']['contact']:
                record['admin']['contact']['name'] = anon_name(record['admin']['contact']['name'])

        if 'notes' in record['admin']:
            for note in record['admin']['notes']:
                note['note'] = basic_hash(note['note'])

    return record


def anonymise_id(record):
    if 'id' in record:
        record['id'] = basic_hash(record['id'])
    return record


def anonymise_account(record):
    anonymise_id(record)
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


def anonymise_editor_groups(record):
    if 'associates' in record:
        for (index, username) in enumerate(record['associates'][:]):
            record['associates'][index] = basic_hash(username)

    if 'editor' in record:
        record['editor'] = basic_hash(record['editor'])

    return record


def anonymise_user(record):
    if 'owner' in record:
        record['owner'] = basic_hash(record['owner'])

    if 'username' in record:
        record['username'] = basic_hash(record['username'])
        
    if 'user' in record:
        record['user'] = basic_hash(record['user'])

    return record


def anonymise_background_job(record):
    if 'params' in record:
        if 'suggestion_bulk_edit__note' in record['params']:
            record['params']['suggestion_bulk_edit__note'] =\
                basic_hash(record['params']['suggestion_bulk_edit__note'])

    return record


def anonymise_default(record):
    anonymise_user(record)
    anonymise_email(record)
    anonymise_admin(record)
    return record

anonymisation_procedures = {
    '_default': anonymise_default,
    'account': anonymise_account,
    'background_job': anonymise_background_job,
    'bulk_reapplication': anonymise_user,
    'bulk_upload': anonymise_user,
    'journal': anonymise_journal,
    'lock': anonymise_user,
    'provenance': anonymise_user,
    'suggestion': anonymise_suggestion,
    'upload': anonymise_user,
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
