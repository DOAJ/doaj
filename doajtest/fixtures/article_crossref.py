import os
import re
from lxml import etree
from io import BytesIO, StringIO
from copy import deepcopy

RESOURCES = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "unit", "resources")
ARTICLES = os.path.join(RESOURCES, "crossref_article_uploads.xml")

NS = {'x': 'http://www.crossref.org/schema/4.4.2'}

class CrossrefArticleFixtureFactory(object):

    @classmethod
    def _response_from_xpath(cls, xpath):
        with open(ARTICLES) as f:
            doc = etree.parse(f)
        records = doc.getroot()
        articles = records.xpath(xpath, namespaces=NS)
        ns = "{%s}" % NS['x']
        nr = etree.Element(ns + "doi_batch")
        nr.append(records.xpath("//x:head", namespaces=NS)[0])
        nr.append(etree.Element(ns + "body"))
        body = nr.find("x:body", NS)
        for a in articles:
            body.append(a)
        out = etree.tostring(nr, encoding="UTF-8", xml_declaration=True)
        return BytesIO(out)

    @classmethod
    def upload_2_issns_correct(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='2 ISSNs Correct']]")

    @classmethod
    def upload_2_issns_ambiguous(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='2 ISSNs Ambiguous']]")

    @classmethod
    def upload_1_issn_correct(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='PISSN Correct']]")

    @classmethod
    def upload_author_email_address(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='author email address']]")

    @classmethod
    def upload_1_issn_superlong_should_not_clip(cls):
        return cls._response_from_xpath(
            "//x:body/x:journal[x:journal_metadata[x:full_title='PISSN Correct Superlong Abstract Expected to Not be Clipped']]")

    @classmethod
    def upload_1_issn_superlong_should_clip(cls):
        return cls._response_from_xpath(
            "//x:body/x:journal[x:journal_metadata[x:full_title='PISSN Correct Superlong Abstract Expected to be Clipped']]")

    @classmethod
    def invalid_schema_xml(cls):
        return StringIO("<this><isnot my='schema'></isnot></this>")

    @classmethod
    def noids(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='NOIDS']]")

    @classmethod
    def upload_1_issn_electronic(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='1 ISSN - electronic']]")

    @classmethod
    def upload_1_issn_print(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='1 ISSN - print']]")

    @classmethod
    def upload_1_issn_no_type(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='1 ISSN - no type']]")

    @classmethod
    def upload_2_issns_1_electronic_2_no_type(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='2 ISSNs - electronic then no type']]")

    @classmethod
    def upload_2_issns_1_electronic_2_print(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='2 ISSNs - electronic then print']]")

    @classmethod
    def upload_2_issns_1_no_type_2_electronic(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='2 ISSNs - no type then electronic']]")

    @classmethod
    def upload_2_issns_1_print_2_no_type(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='2 ISSNs - print then no type']]")

    @classmethod
    def upload_2_issns_1_print_2_electronic(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='2 ISSNs - print then electronic']]")

    @classmethod
    def upload_2_issns_1_no_type_2_print(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='2 ISSNs - no type then print']]")

    @classmethod
    def upload_2_issns_no_type(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='2 ISSNs - no types']]")

    @classmethod
    def upload_2_issns_same_types(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='2 ISSNs - same types']]")

    @classmethod
    def upload_3_issns(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='3 ISSNs']]")

    @classmethod
    def upload_the_same_issns(cls):
        return cls._response_from_xpath("//x:body/x:journal[x:journal_metadata[x:full_title='2 The Same ISSNs']]")

