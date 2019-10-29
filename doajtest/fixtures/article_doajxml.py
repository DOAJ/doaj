import os
from lxml import etree
from io import BytesIO,StringIO
from copy import deepcopy

RESOURCES = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "unit", "resources")
ARTICLES = os.path.join(RESOURCES, "doajxml_article_uploads.xml")


class DoajXmlArticleFixtureFactory(object):

    @classmethod
    def _response_from_xpath(cls, xpath):
        with open(ARTICLES) as f:
            doc = etree.parse(f)
        records = doc.getroot()
        articles = records.xpath(xpath)
        nr = etree.Element("records")
        for a in articles:
            nr.append(a)
        out = etree.tostring(nr, encoding="UTF-8", xml_declaration=True)
        return BytesIO(out)

    @classmethod
    def upload_2_issns_correct(cls):
        return cls._response_from_xpath("//record[journalTitle='2 ISSNs Correct']")

    @classmethod
    def upload_2_issns_ambiguous(cls):
        return cls._response_from_xpath("//record[journalTitle='2 ISSNs Ambiguous']")

    @classmethod
    def upload_1_issn_correct(cls):
        return cls._response_from_xpath("//record[journalTitle='PISSN Correct']")

    @classmethod
    def upload_author_email_address(cls):
        return cls._response_from_xpath("//record[journalTitle='author email address']")

    @classmethod
    def upload_1_issn_superlong_should_not_clip(cls):
        return cls._response_from_xpath("//record[journalTitle='PISSN Correct Superlong Abstract Expected to Not be Clipped']")

    @classmethod
    def upload_1_issn_superlong_should_clip(cls):
        return cls._response_from_xpath("//record[journalTitle='PISSN Correct Superlong Abstract Expected to be Clipped']")

    @classmethod
    def invalid_schema_xml(cls):
        return StringIO("<this><isnot my='schema'></isnot></this>")

    @classmethod
    def noids(cls):
        return cls._response_from_xpath("//record[journalTitle='NOIDS']")

    @classmethod
    def valid_url_http(cls):
        return cls._response_from_xpath("//record[journalTitle='Url starting with http']")

    @classmethod
    def valid_url_https(cls):
        return cls._response_from_xpath("//record[journalTitle='Url starting with https']")

    @classmethod
    def valid_url_non_ascii_chars(cls):
        return cls._response_from_xpath("//record[journalTitle='Url containing non-ascii characters']")

    @classmethod
    def invalid_url(cls):
        return cls._response_from_xpath("//record[journalTitle='Invalid url']")

    @classmethod
    def invalid_url_http_missing(cls):
        return cls._response_from_xpath("//record[journalTitle='Url with http missing']")

    @classmethod
    def valid_url_http_anchor(cls):
        return cls._response_from_xpath("//record[journalTitle='Url with http anchor']")

    @classmethod
    def valid_url_parameters(cls):
        return cls._response_from_xpath("//record[journalTitle='Url with parameters']")
