import re

from lxml import etree

from portality.core import app

DOI = r"^((https?://)?((dx\.)?doi\.org/|hdl\.handle\.net/)|doi:|info:doi/|info:hdl/)?(?P<id>10\.\S+/\S+)$"
DOI_COMPILED = re.compile(DOI, re.IGNORECASE)
ORCID_XPATH = '/xs:schema[@version="1.2"]/xs:complexType[@name="recordType"]/xs:sequence/xs:element[@name="authors"]/xs:complexType/xs:sequence/xs:element[@name="author"]/xs:complexType/xs:sequence/xs:element[@name="orcid_id"]/xs:simpleType/xs:restriction/xs:pattern/@value'


def _read_value(id):
    with open(app.config.get("SCHEMAS")["doaj"]) as xsd:
        doc = etree.parse(xsd)
        if id == 'orcid':
            data = doc.xpath(ORCID_XPATH, namespaces=doc.getroot().nsmap)
        else:
            data = doc.xpath(DOI_XPATH, namespaces=doc.getroot().nsmap)
    return data[0]


ORCID = r"^" + _read_value("orcid") + r"$"
ORCID_COMPILED = re.compile(ORCID)


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
