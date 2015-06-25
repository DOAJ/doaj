import os
from lxml import etree
from StringIO import StringIO

RESOURCES = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "unit", "resources")
ARTICLES = os.path.join(RESOURCES, "article_uploads.xml")

class ArticleFixtureFactory(object):

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
        return StringIO(out)

    @classmethod
    def upload_2_issns_correct(cls):
        return cls._response_from_xpath("//record[journalTitle='2 ISSNs Correct']")

    @classmethod
    def upload_2_issns_ambiguous(cls):
        return cls._response_from_xpath("//record[journalTitle='2 ISSNs Ambiguous']")

    @classmethod
    def upload_1_issn_correct(cls):
        return cls._response_from_xpath("//record[journalTitle='PISSN Correct']")

