""" Use pycountry to write the XML Schema for ISO-639-2b: the bibliographic language codes, used by our XML importer."""

import os
import pycountry
import difflib
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

    # Gather names and 3-char codes (bibliographic preferred) for only the languages with 2-character codes (ISO639-1)
    for l in pycountry.languages:
        try:
            _ = l.alpha_2
        except AttributeError:
            continue                                                               # Skip languages without 2-char codes

        try:
            code = l.bibliographic
        except AttributeError:
            code = l.alpha_3                                            # Fallback to alpha_3 when no bibliographic code

        # See docstring above for what the XML for this looks like
        language_entry = ENUM(
            {'value': code},
            ANNOT(
                DOCU(l.name)
            )
        )

        # Add the language to our document
        language_list_element.append(language_entry)

    # Write the new XML Schema file
    schema_tree.write(out_file, pretty_print=True, encoding='utf-8')


def compare_lang_schemas(schema_old, schema_new, ofile):
    """ Generate a simplified view of the old and new schema, then diff their contents """
    # Parse the XML Schemata for comparison
    old_tree = etree.parse(schema_old).getroot()
    new_tree = etree.parse(schema_new).getroot()

    # Extract the language information from both trees
    old_lc = [a.attrib['value'] for a in old_tree.findall('.//xsd:restriction/xsd:enumeration', namespaces=old_tree.nsmap)]
    old_ln = [a.text for a in old_tree.findall('.//xsd:restriction/xsd:enumeration/xsd:annotation/xsd:documentation',
                                           namespaces=old_tree.nsmap)]

    new_lc = [b.attrib['value'] for b in new_tree.findall('.//xsd:restriction/xsd:enumeration', namespaces=old_tree.nsmap)]
    new_ln = [b.text for b in new_tree.findall('.//xsd:restriction/xsd:enumeration/xsd:annotation/xsd:documentation',
                                           namespaces=new_tree.nsmap)]

    # List the simplified language entries
    old_strlist = [u'{0}\t{1}'.format(t[0], t[1]) for t in zip(old_lc, old_ln)]
    new_strlist = [u'{0}\t{1}'.format(t[0], t[1]) for t in zip(new_lc, new_ln)]

    old_file = schema_old.split('/').pop()
    new_file = schema_new.split('/').pop()

    # fixme: hilariously, this won't handle utf-8 correctly until Python 3.5 (upgrade required)
    diff = difflib.HtmlDiff().make_file(old_strlist, new_strlist, fromdesc=old_file, todesc=new_file, context=True)

    with open(ofile, 'w') as o:
        o.writelines(l.encode('utf8') for l in diff)

    print("Diff saved to " + ofile)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', help='Schema version for the target XSD, e.g. 2.1', required=True)
    parser.add_argument('-f', '--filename', help='filename for schema, including extension', default='iso_639-2b.xsd')
    parser.add_argument('-c', '--compare', help='Write a comparison of new and old schemas (optional: filename)',
                        nargs='?', const='isolang_diff.html', default=None)

    args = parser.parse_args()

    dest_path = paths.rel2abs(__file__, '..', 'static', 'doaj', args.filename)

    if os.path.exists(dest_path):
        print('Schema already exists with name {n} - replace? [y/N]'.format(n=args.filename))
        resp = raw_input('Your existing file will be retained as {fn}.old : '.format(fn=args.filename))
        if resp.lower() == 'y':
            os.rename(dest_path, dest_path + '.old')

            with open(dest_path, 'w') as f:
                write_lang_schema(f, args.version)

        if args.compare and os.path.exists(dest_path + '.old'):
            compare_path = paths.rel2abs(__file__, '..', 'static', 'doaj', args.compare)
            compare_lang_schemas(dest_path + '.old', dest_path, compare_path)
