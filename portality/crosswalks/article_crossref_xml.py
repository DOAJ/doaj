import os

from portality.core import app
from lxml import etree
import re
from portality.bll import exceptions
from portality.crosswalks.exceptions import CrosswalkException
from portality import models

NS = {'x': 'http://www.crossref.org/schema/4.4.2', 'j': 'http://www.ncbi.nlm.nih.gov/JATS1'}


class CrossrefXWalk(object):
    format_name = "crossref"

    def __init__(self):
        self.validation_log = ""
        self.schema_path = app.config.get("SCHEMAS", {}).get("crossref")

        # load the schema into memory for more efficient usage in repeat calls to the crosswalk
        if self.schema_path is None:
            raise exceptions.IngestException(
                message="Unable to validate for CrossrefXWalk, as schema path is not set in config")

        while app.config["CROSSREF_SCHEMA"] is None:
            continue

        self.schema = app.config["CROSSREF_SCHEMA"]

    def validate_file(self, file_handle):
        # first try to parse the file
        try:
            doc = etree.parse(file_handle)
        except etree.XMLSyntaxError as e:  # although the treatment is the same, pulling this out so we remember what the primary kind of exception should be
            raise CrosswalkException(message="Unable to parse XML file", inner=e)
        except UnicodeDecodeError as e:
            msg = 'Text decode failed, expected utf-8 encoded XML.'
            raise CrosswalkException(message='Unable to parse XML file', inner=e, inner_message=msg)
        except Exception as e:
            raise CrosswalkException(message="Unable to parse XML file", inner=e)

        # then pass the doc to the validator
        valid = self.validate(doc)

        if not valid:
            msg = "Validation message from schema '{x}': {y}\n".format(x=CrossrefXWalk.format_name,
                                                                       y=self.validation_log)
            raise CrosswalkException(message="Unable to validate document with identified schema", inner_message=msg)

        return doc

    def validate(self, doc):
        valid = self.schema.validate(doc)
        if not valid:
            el = self.schema.error_log.__repr__()
            # strip the filename, as we don't want to leak the path to the UI
            rx = "[\da-f]{32}.xml:(.*)"
            match = re.search(rx, el)
            if match is not None:
                el = match.group(1)
            self.validation_log = el
        return valid

    def crosswalk_file(self, file_handle, add_journal_info):
        doc = self.validate_file(file_handle)
        return self.crosswalk_doc(doc)

    def crosswalk_doc(self, doc):
        # go through the records in the doc and crosswalk each one individually
        articles = []
        root = doc.getroot()
        body = root.find("x:body", NS)
        journals = body.findall("x:journal", NS)
        if journals is not None:
            for journal in journals:
                arts = journal.findall("x:journal_article", NS)
                for record in arts:
                    article = self.crosswalk_article(record, journal)
                    articles.append(article)

        return articles

    def crosswalk_article(self, record, journal):
        """
Example record:
<doi_batch version="4.4.2" xmlns="http://www.crossref.org/schema/4.4.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.crossref.org/schema/4.3.7 http://www.crossref.org/schema/deposit/crossref4.3.7.xsd">
    <head>
        <doi_batch_id>1dbb27d1030c6c9d9d-7ff0</doi_batch_id>
        <timestamp>200504260247</timestamp>
        <depositor>
            <depositor_name>your name</depositor_name>
            <email_address>your@email.com</email_address>
        </depositor>
        <registrant>WEB-FORM</registrant>
    </head>
    <body>
        <journal>
            <journal_metadata>
                <full_title>Test Publication</full_title>
                <abbrev_title>TP</abbrev_title>
                <issn media_type="print">2073-9813</issn>
            </journal_metadata>
            <journal_issue>
                <publication_date media_type="print">
                    <month>12</month>
                    <day>1</day>
                    <year>2005</year>
                </publication_date>
                <journal_volume>
                    <volume>12</volume>
                </journal_volume>
                <issue>1</issue>
            </journal_issue>
            <!-- ====== This is the article's metadata ======== -->
            <journal_article publication_type="full_text">
                <titles>
                    <title>First Article</title>
                </titles>
                <contributors>
                    <person_name sequence="first" contributor_role="author">
                        <given_name>Bob</given_name>
                        <surname>Surname</surname>
                        <ORCID>http://orcid.org/0000-0002-4011-3590</ORCID>
                    </person_name>
                </contributors>
                <publication_date media_type="print">
                    <month>12</month>
                    <day>1</day>
                    <year>2004</year>
                </publication_date>
                <pages>
                    <first_page>100</first_page>
                    <last_page>200</last_page>
                </pages>
                <doi_data>
                    <doi>10.50505/test_20051229930</doi>
                    <resource>http://www.crossref.org/</resource>
                </doi_data>
                <!-- =========  Here is the list of references cited in the above article -->
                <citation_list>
                    <citation key="ref1">
                        <journal_title>Current Opinion in Oncology</journal_title>
                        <author>Chauncey</author>
                        <volume>13</volume>
                        <first_page>21</first_page>
                        <cYear>2001</cYear>
                    </citation>
                    <citation key="ref2">
                        <doi>10.5555/small_md_0001</doi>
                    </citation>
                    <citation key="ref=3">
                    <unstructured_citation>Clow GD, McKay CP, Simmons Jr. GM, and Wharton RA, Jr. 1988. Climatological observations and           predicted sublimation rates at Lake Hoare, Antarctica. Journal of Climate 1:715-728.</unstructured_citation>
                    </citation>
                </citation_list>
            </journal_article>
        </journal>
    </body>
</doi_batch>
        """
        article = models.Article()
        bibjson = article.bibjson()

        # journal title
        jm = journal.find("x:journal_metadata", NS)
        if jm is not None:
            jt = _element(jm, "x:full_title", NS)
            if jt is not None:
                bibjson.journal_title = jt

        # p-issn and e-issn
        md = journal.find("x:journal_metadata", NS)
        if md is not None:
            issns = md.findall("x:issn", NS)
            if issns is not None:
                for issn in issns:
                    if issn.attrib["media_type"] is None or issn.attrib["media_type"] == 'print':
                        bibjson.add_identifier(bibjson.P_ISSN, issn.text.upper())
                    elif issn.attrib["media_type"] == 'electronic':
                        bibjson.add_identifier(bibjson.E_ISSN, issn.text.upper())


        # publication date
        pd = record.find("x:publication_date", NS)

        if pd is not None:
            bibjson.year = _element(pd, "x:year", NS)
            bibjson.month = _element(pd, "x:month", NS)

        # volume

        issue = journal.find("x:journal_issue", NS)

        if issue is not None:
            vol = issue.find("x:journal_volume", NS)
            if vol is not None:
                volume = _element(vol, "x:volume", NS)
                if volume is not None:
                    bibjson.volume = volume

            # issue
            number = _element(issue, "x:issue", NS)
            if number is not None:
                bibjson.number = number

        pages = record.find('x:pages', NS)
        # start page
        if pages is not None:
            sp = _element(pages, "x:first_page", NS)
            if sp is not None:
                bibjson.start_page = sp

            # end page
            ep = _element(pages, "x:last_page", NS)
            if ep is not None:
                bibjson.end_page = ep

        d = record.find("x:doi_data", NS)
        if d is not None:
            # doi
            doi = _element(d, "x:doi", NS)
            if doi is not None:
                bibjson.add_identifier(bibjson.DOI, doi)

            # fulltext
            ftel = _element(d, "x:resource", NS)
            if ftel is not None:
                bibjson.add_url(ftel, "fulltext", NS)

        # title
        titles = record.find('x:titles', NS)
        if titles is not None:
            title = _element(titles, "x:title", NS)
            if title is not None:
                bibjson.title = title

        # authors
        contributors = record.find("x:contributors", NS)
        contribs = contributors.findall("x:person_name", NS)
        if contribs is not None:
            for ctb in contribs:
                if ctb.attrib["contributor_role"] == 'author':
                    name = _element(ctb, "x:surname", NS)
                    name = name + ', ' + _element(ctb, "x:given_name", NS)
                    bibjson.add_author(name, affiliation=None)

        # abstract
        abstract_par = record.find("j:abstract", NS)
        if abstract_par is not None:
            text_elems = list(abstract_par.iter())
            text = ""
            if text_elems is not None:
                for elems in text_elems:
                    if elems.text is not None:
                        text = text + elems.text
            bibjson.abstract = text[:30000]  # avoids Elasticsearch
            # exceptions about .exact analyser not being able to handle
            # more than 32766 UTF8 characters


        return article


###############################################################################
## some convenient utilities
###############################################################################


def _element(xml, field, namepsace):
    el = xml.find(field, namepsace)
    if el is not None and el.text is not None and el.text != "":
        return el.text.strip()
    return None
