""" Use pycountry to write the XML Schema for ISO-639-2b: the bibliographic language codes, used by our XML importer."""

import os
import pycountry
from portality.lib import paths
from portality.lib.dates import today


def write_lang_schema(out_file):
    pass
# get the path for a new file

# Write file header stuff

# Write entry for each language


def compare_lang_schemas(schema_a, schema_b):
    pass
# todo: compare with existing language list


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', help='filename for schema, including extension', default='iso_639-2b.xsd')
    args = parser.parse_args()

    dest_path = paths.rel2abs(__file__, '..', 'static', 'doaj', args.filename)

    if os.path.exists(dest_path):
        print('Schema already exists with name {n} - replace? [y/N]'.format(n=args.filename))
        resp = raw_input('Your existing file will be retained as {fn}.old : '.format(fn=args.filename))
        if resp.lower() == 'y':
            os.rename(dest_path, dest_path + '.old')

    with open(dest_path, 'w') as f:
        write_lang_schema(f)
        compare_lang_schemas(dest_path, dest_path + '.old')
