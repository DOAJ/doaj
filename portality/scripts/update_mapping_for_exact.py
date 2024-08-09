import argparse

from portality import core
from portality.core import es_connection


def main():
    """
    Update mapping for exact field
    """

    parser = argparse.ArgumentParser(description='Update mapping for exact field')
    parser.add_argument('index_type', help='Index name')
    parser.add_argument('field_name', help='Field name (e.g. index.editor_group_name)')

    args = parser.parse_args()

    index = core.get_doaj_index_name(args.index_type)
    field_name = args.field_name
    exact_mapping = {
        "exact": {
            "type": "keyword",
            "store": True
        }
    }

    print(f'Updating mapping for field: [{field_name}] in index: [{index}]')

    conn = es_connection
    org_mapping = conn.indices.get_field_mapping(field_name, index=index)
    org_field_mapping = org_mapping[index]['mappings'][field_name]['mapping']
    org_field_mapping = next(iter(org_field_mapping.values()))
    org_field_mapping['fields'].update(**exact_mapping)
    new_mapping = {
        'properties': {
            field_name: org_field_mapping
        }
    }
    print(new_mapping)
    conn.indices.put_mapping(body=new_mapping, index=index)


if __name__ == '__main__':
    main()
