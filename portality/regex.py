import re

from lxml import etree

from portality.core import app

DOI_XPATH = '/xs:schema[@version="1.2"]/xs:complexType[@name="recordType"]/xs:sequence/xs:element[@name="doi"]/xs:simpleType/xs:restriction/xs:pattern/@value'
ORCID_XPATH = '/xs:schema[@version="1.2"]/xs:complexType[@name="recordType"]/xs:sequence/xs:element[@name="authors"]/xs:complexType/xs:sequence/xs:element[@name="author"]/xs:complexType/xs:sequence/xs:element[@name="orcid_id"]/xs:simpleType/xs:restriction/xs:pattern/@value'


def _read_value(id):
    with open(app.config.get("SCHEMAS")["doaj"]) as xsd:
        doc = etree.parse(xsd)
        if id == 'orcid':
            data = doc.xpath(ORCID_XPATH, namespaces=doc.getroot().nsmap)
        elif id == 'doi':
            data = doc.xpath(DOI_XPATH, namespaces=doc.getroot().nsmap)
            data[0] = data[0].partition("10\.")
    return data


ORCID = r"^" + _read_value("orcid")[0] + r"$"
ORCID_COMPILED = re.compile(ORCID)
doi_data = _read_value("doi")[0]
DOI = r"^" + doi_data[0] + r"(?P<id>" + doi_data[1] + doi_data[2] + r")$"
DOI_COMPILED = re.compile(DOI, re.IGNORECASE)

def is_match(pattern, string, *args, **kwargs):
    match = re.match(pattern, string, *args, **kwargs)
    print(match)
    return match is not None


def group_match(pattern, string, name, *args, **kwargs):
    match = re.match(pattern, string, *args, **kwargs)
    print(match)
    if match is None:
        return None
    return match.group(name)
