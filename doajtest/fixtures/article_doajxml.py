from io import BytesIO, StringIO
from pathlib import Path

from lxml import etree

from doajtest import test_constants
from portality.lib import paths

ARTICLES = test_constants.PATH_RESOURCES / "doajxml_article_uploads.xml"
PATH_XML = Path(paths.get_project_root()) / 'doajtest/xml_upload_test_package/'
NON_XML_FILE = PATH_XML / 'non_xml_file.txt'

PATH_XML_DOAJ = PATH_XML / 'DOAJ'
ARTICLE_UPLOAD_SUCCESSFUL = PATH_XML_DOAJ / 'successful.xml'
ARTICLE_UPLOAD_UPDATE = PATH_XML_DOAJ / 'update.xml'
SCHEMA_INVALID = PATH_XML_DOAJ / 'schema_invalid.xml'
XML_MALFORMED = PATH_XML_DOAJ / 'not_xml.xml'
NO_ISSN = PATH_XML_DOAJ / 'no_issn.xml'
IDENTICAL_ISSNS = PATH_XML_DOAJ / 'identical_issns.xml'
DUPLICATE_IN_FILE = PATH_XML_DOAJ / 'duplicate_in_file.xml'
UNOWNED_ISSN = PATH_XML_DOAJ / 'unowned_issn.xml'
WITHDRAWN_JOURNAL = PATH_XML_DOAJ / 'withdrawn_journal.xml'
UNMATCHED_ISSN = PATH_XML_DOAJ / 'unmatched_issn.xml'
SHARED_ISSN = PATH_XML_DOAJ / 'shared_issn.xml'


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
    def upload_no_issns(cls):
        return cls._response_from_xpath("//record[journalTitle='No issns']")

    @classmethod
    def upload_author_email_address(cls):
        return cls._response_from_xpath("//record[journalTitle='author email address']")

    @classmethod
    def upload_1_issn_superlong_should_not_clip(cls):
        return cls._response_from_xpath(
            "//record[journalTitle='PISSN Correct Superlong Abstract Expected to Not be Clipped']")

    @classmethod
    def upload_1_issn_superlong_should_clip(cls):
        return cls._response_from_xpath(
            "//record[journalTitle='PISSN Correct Superlong Abstract Expected to be Clipped']")

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

    @classmethod
    def valid_orcid_id(cls):
        return cls._response_from_xpath("//record[journalTitle='With valid orcid_id']")

    @classmethod
    def invalid_orcid_id(cls):
        return cls._response_from_xpath("//record[journalTitle='With invalid orcid_id']")

    @classmethod
    def upload_the_same_issns(cls):
        return cls._response_from_xpath("//record[journalTitle='2 The Same ISSNs']")
