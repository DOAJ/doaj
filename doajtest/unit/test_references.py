from unittest import TestCase

from lxml import etree

from portality import models
from portality.api.current.data_objects.article import IncomingArticleDO, OutgoingArticleDO
from portality.crosswalks.article_crossref_xml import CrossrefXWalk442, CrossrefXWalk531
from portality.crosswalks.article_doaj_xml import DOAJXWalk
from portality.crosswalks.article_ris import ArticleRisXWalk
from portality.lib.reference import hyperlink_reference

DOAJ_XML = """<record>
    <journalTitle>Test Journal</journalTitle>
    <publicationDate>2023-01-01</publicationDate>
    <title>Test Article</title>
    <references>
        <reference>Smith, J. (2020) First reference. https://doi.org/10.1234/abc</reference>
        <reference>Jones, A. (2021) Second reference.</reference>
        <reference>   </reference>
    </references>
</record>"""

CROSSREF_XML = """<journal_article xmlns="http://www.crossref.org/schema/4.4.2">
    <citation_list>
        <citation key="ref1">
            <unstructured_citation>Smith, J. (2020) First reference.</unstructured_citation>
        </citation>
        <citation key="ref2">
            <author>Jones</author>
            <cYear>2021</cYear>
            <article_title>Second reference</article_title>
            <doi>10.1234/def</doi>
        </citation>
        <citation key="ref3"/>
    </citation_list>
</journal_article>"""


CROSSREF_531_XML = """<journal_article xmlns="http://www.crossref.org/schema/5.3.1">
    <citation_list>
        <citation key="ref1">
            <unstructured_citation>Smith, J. (2020) First reference.</unstructured_citation>
        </citation>
        <citation key="ref2">
            <author>Jones</author>
            <cYear>2021</cYear>
            <article_title>Second reference</article_title>
            <journal_title>Journal of Tests</journal_title>
            <volume>3</volume>
            <first_page>10</first_page>
            <doi>10.1234/def</doi>
        </citation>
        <citation key="ref3"/>
    </citation_list>
</journal_article>"""


class TestReferences(TestCase):

    def test_01_model(self):
        article = models.Article()
        bibjson = article.bibjson()

        assert bibjson.reference == []

        bibjson.add_reference("Smith, J. (2020) A reference.")
        assert bibjson.reference == ["Smith, J. (2020) A reference."]

        bibjson.set_reference(["one", "two"])
        assert bibjson.reference == ["one", "two"]
        assert bibjson.references == ["one", "two"]

    def test_02_doaj_xml_crosswalk(self):
        record = etree.fromstring(DOAJ_XML)
        article = DOAJXWalk().crosswalk_article(record, add_journal_info=False)
        assert article.bibjson().reference == [
            "Smith, J. (2020) First reference. https://doi.org/10.1234/abc",
            "Jones, A. (2021) Second reference."
        ]

    def test_03_doaj_xml_crosswalk_no_references(self):
        record = etree.fromstring("<record><title>No refs</title></record>")
        article = DOAJXWalk().crosswalk_article(record, add_journal_info=False)
        assert article.bibjson().reference == []

    def test_04_crossref_crosswalk(self):
        record = etree.fromstring(CROSSREF_XML)
        xwalk = CrossrefXWalk442.__new__(CrossrefXWalk442)
        bibjson = models.Article().bibjson()
        xwalk.extract_references(record, None, bibjson)
        assert bibjson.reference == [
            "Smith, J. (2020) First reference.",
            "Jones. 2021. Second reference. 10.1234/def"
        ]

    def test_04a_crossref_531_crosswalk(self):
        record = etree.fromstring(CROSSREF_531_XML)
        xwalk = CrossrefXWalk531.__new__(CrossrefXWalk531)
        bibjson = models.Article().bibjson()
        xwalk.extract_references(record, None, bibjson)
        assert bibjson.reference == [
            "Smith, J. (2020) First reference.",
            "Jones. 2021. Second reference. Journal of Tests. 3. 10. 10.1234/def"
        ]

    def test_04b_crossref_531_ignores_442_namespace(self):
        record = etree.fromstring(CROSSREF_XML)
        xwalk = CrossrefXWalk531.__new__(CrossrefXWalk531)
        bibjson = models.Article().bibjson()
        xwalk.extract_references(record, None, bibjson)
        assert bibjson.reference == []

    def test_05_ris_crosswalk(self):
        article = models.Article()
        bibjson = article.bibjson()
        bibjson.title = "Test Article"
        bibjson.set_reference(["First reference", "Second reference"])

        ris = ArticleRisXWalk.article2ris(article)
        assert ris["CR"] == ["First reference", "Second reference"]
        assert "CR  - First reference" in ris.to_text()

    def test_06_api_incoming_and_outgoing(self):
        source = {
            "bibjson": {
                "title": "Test Article",
                "identifier": [{"type": "eissn", "id": "1234-5678"}],
                "link": [{"type": "fulltext", "url": "https://example.com/article"}],
                "reference": ["First reference", "", "Second reference"]
            }
        }
        incoming = IncomingArticleDO(source)
        incoming.custom_validate()
        assert incoming.data["bibjson"]["reference"] == ["First reference", "Second reference"]

        article = incoming.to_article_model()
        assert article.bibjson().reference == ["First reference", "Second reference"]

        outgoing = OutgoingArticleDO.from_model(article)
        assert outgoing.data["bibjson"]["reference"] == ["First reference", "Second reference"]

    def test_07_hyperlink_reference(self):
        assert hyperlink_reference("") == ""
        assert hyperlink_reference(None) == ""

        # plain text is escaped and left alone
        assert hyperlink_reference("Smith & Jones") == "Smith &amp; Jones"

        # urls are linked, and trailing punctuation is not part of the link
        result = hyperlink_reference("See https://example.com/a-b.")
        assert result == 'See <a href="https://example.com/a-b" target="_blank" rel="noopener">https://example.com/a-b</a>.'

        # bare and prefixed dois are resolved via doi.org
        result = hyperlink_reference("Ref 10.1234/abc.def")
        assert result == 'Ref <a href="https://doi.org/10.1234/abc.def" target="_blank" rel="noopener">10.1234/abc.def</a>'

        result = hyperlink_reference("doi:10.1234/abc")
        assert result == '<a href="https://doi.org/10.1234/abc" target="_blank" rel="noopener">doi:10.1234/abc</a>'

        # a doi inside a url is only linked once
        result = hyperlink_reference("https://doi.org/10.1234/abc")
        assert result.count("<a href") == 1

    def test_08_hyperlink_reference_escapes_script(self):
        result = hyperlink_reference('<script>alert("x")</script>')
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
