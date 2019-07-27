""" Use pycountry to write the XML Schema for ISO-639-2b: the bibliographic language codes, used by our XML importer."""

import os
import pycountry
from lxml import etree
from lxml.builder import ElementMaker
from portality.lib import paths

SCHEMA_TEMPLATE = '''\
<?xml version="1.0" encoding="UTF-8"?>
<xsd:schema attributeFormDefault="unqualified" elementFormDefault="qualified" targetNamespace="http://www.doaj.org/schemas/iso_639-2b/{schema_version}" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <xsd:annotation>
        <xsd:documentation>Codes for the representation of names of languages from the International Organization for Standardization (ISO) 639-2/B (bibliographic codes).</xsd:documentation>
    </xsd:annotation>
    <xsd:simpleType name="LanguageCodeType">
        <xsd:annotation>
            <xsd:documentation>A code list that enumerates languages.</xsd:documentation>
        </xsd:annotation>
        <xsd:restriction base="xsd:token">
        </xsd:restriction>
    </xsd:simpleType>
</xsd:schema>
'''


"""
Each language entry looks like this, listed within <xsd:restriction>:

<xsd:enumeration value="{language_code}">
    <xsd:annotation>
        <xsd:documentation>{language_name}</xsd:documentation>
    </xsd:annotation>
</xsd:enumeration>
"""


def write_lang_schema(out_file, schema_version):
    """ Generate an XML file with language data from pycountry
    :param out_file
    :param schema_version
    """

    # Set up our document as parsed XML
    parser = etree.XMLParser(remove_blank_text=True)
    schema = etree.XML(SCHEMA_TEMPLATE.format(schema_version=schema_version), parser=parser)
    schema_tree = etree.ElementTree(schema)
    language_list_element = schema.find('.//xsd:restriction', namespaces=schema.nsmap)
    language_list_element.text = None                                         # Fixes whitespace failure on pretty_print

    # Define the building blocks for a language entry in the Schema
    E = ElementMaker(namespace=schema.nsmap[schema.prefix], nsmap=schema.nsmap)
    ENUM = E.enumeration
    ANNOT = E.annotation
    DOCU = E.documentation

    # Gather the names and 3-char codes for only the languages with 2-character codes (ISO639-1)
    for l in pycountry.languages:
        try:
            _ = l.alpha_2
            # See docstring above for what this looks like
            language_entry = ENUM(
                                  {'value': l.alpha_3},
                                  ANNOT(
                                      DOCU(l.name)
                                       )
                                 )

            # Add the language to our document
            language_list_element.append(language_entry)
        except AttributeError:
            continue

    # Write the new XML Schema file
    schema_tree.write(out_file, pretty_print=True, encoding='utf-8')


def compare_lang_schemas(schema_a, schema_b):
    pass
# todo: compare with existing language list


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', help='Schema version for the target XSD, e.g. 2.1', required=True)
    parser.add_argument('-f', '--filename', help='filename for schema, including extension', default='iso_639-2b.xsd')
    args = parser.parse_args()

    dest_path = paths.rel2abs(__file__, '..', 'static', 'doaj', args.filename)

    if os.path.exists(dest_path):
        print('Schema already exists with name {n} - replace? [y/N]'.format(n=args.filename))
        resp = raw_input('Your existing file will be retained as {fn}.old : '.format(fn=args.filename))
        if resp.lower() == 'y':
            os.rename(dest_path, dest_path + '.old')

    with open(dest_path, 'w') as f:
        write_lang_schema(f, args.version)
        compare_lang_schemas(dest_path, dest_path + '.old')
