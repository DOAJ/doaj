import os

from portality.core import app
from lxml import etree
import re
from portality.bll import exceptions
from portality.crosswalks.exceptions import CrosswalkException
from portality import models
from datetime import datetime

from portality.settings import BASE_FILE_PATH


class CrossrefXWalk(object):
    format_name = "crossref"
    schema_path = app.config.get("SCHEMAS", {}).get("crossref")

    def __init__(self):
        self.validation_log = ""

        # load the schema into memory for more efficient usage in repeat calls to the crosswalk
        if self.schema_path is None:
            raise exceptions.IngestException(
                message="Unable to validate for CrossrefXWalk, as schema path is not set in config")

        try:
            schema_file = open(self.schema_path)
            schema_doc = etree.parse(schema_file)
            self.schema = etree.XMLSchema(schema_doc)
        except Exception as e:
            raise exceptions.IngestException(
                message="There was an error attempting to load schema from " + self.schema_path, inner=e)

    def validate_file(self, file_handle):
        # first try to parse the file
        try:
            doc = etree.parse(file_handle)
        except etree.XMLSyntaxError as e:  # although the treatment is the same, pulling this out so we remember what the primary kind of exception should be
            raise CrosswalkException(message="Unable to parse XML file", inner=e)
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

    def crosswalk_file(self, file_handle, import_journal_info):
        doc = self.validate_file(file_handle)
        return self.crosswalk_doc(doc)

    def crosswalk_doc(self, doc):
        # go through the records in the doc and crosswalk each one individually
        articles = []
        root = doc.getroot()
        head = root.findall("head")
        body = root.findall("body")
        journal = body.findall("journal")
        for record in journal.findall("journal_article"):
            article = self.crosswalk_article(record, head, body, journal)
            articles.append(article)

        return articles

    def crosswalk_article(self, record, head, body, journal):
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
                    <title>Article 12292005 9:32</title>
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

        '''
        # language
        lang = _element(record, "language")
        if lang is not None:
            bibjson.journal_language = lang
        '''

        '''
        # publisher
        pub = _element(record, "publisher")
        if pub is not None:
            bibjson.publisher = pub
        '''

        # journal title
        jt = _element(_element(journal, "journal_metadata"), "full_title")
        if jt is not None:
            bibjson.journal_title = jt

        # p-issn
        issn = _element(_element(journal, "issn"), "issn")
        if issn is not None:
            if issn.attrib["mediatype"] == 'print':
                bibjson.add_identifier(bibjson.P_ISSN, issn.upper())

        # e-issn
        eissn = _element(record, "eissn")
        if eissn is not None:
            bibjson.add_identifier(bibjson.E_ISSN, eissn.upper())

        # publication date
        pd = _element(record, "publicationDate")
        if pd is not None:
            y, m = _year_month(pd)
            if y is not None:
                bibjson.year = y
            if m is not None:
                bibjson.month = m

        # volume
        vol = _element(record, "volume")
        if vol is not None:
            bibjson.volume = vol

        # issue
        iss = _element(record, "issue")
        if iss is not None:
            bibjson.number = iss

        # start page
        sp = _element(record, "startPage")
        if sp is not None:
            bibjson.start_page = sp

        # end page
        ep = _element(record, "endPage")
        if ep is not None:
            bibjson.end_page = ep

        # doi
        doi = _element(record, "doi")
        if doi is not None:
            bibjson.add_identifier(bibjson.DOI, doi)

        # publisher record id
        pri = _element(record, "publisherRecordId")
        if pri is not None:
            article.set_publisher_record_id(pri)

        # document type
        dt = _element(record, "documentType")
        if dt is not None:
            # FIXME: outstanding question as to what to do with this
            pass

        # title
        title = _element(record, "title")
        if title is not None:
            bibjson.title = title

        # authors
        ## first we need to extract the affiliations
        affiliations = {}
        affel = record.find("affiliationsList")
        if affel is not None:
            for ael in affel:
                affid = ael.get("affiliationId")
                aff = ael.text
                affiliations[affid] = aff
        ## now crosswalk each author and dereference their affiliation from the table
        authorsel = record.find("authors")
        if authorsel is not None:
            for ael in authorsel:
                name = _element(ael, "name")
                affid = _element(ael, "affiliationId")
                aff = affiliations.get(affid)
                bibjson.add_author(name, affiliation=aff)

        # abstract
        abstract = _element(record, "abstract")
        if abstract is not None:
            bibjson.abstract = abstract[:30000]  # avoids Elasticsearch
            # exceptions about .exact analyser not being able to handle
            # more than 32766 UTF8 characters

        # fulltext
        ftel = record.find("fullTextUrl")
        if ftel is not None and ftel.text is not None and ftel.text != "":
            ct = ftel.get("format")
            url = ftel.text
            bibjson.add_url(url, "fulltext", ct)

        # keywords
        keyel = record.find("keywords")
        if keyel is not None:
            for kel in keyel:
                if kel.text != "":
                    bibjson.add_keyword(kel.text)

        # add the journal info if requested
        if add_journal_info:
            article.add_journal_metadata()

        return article


###############################################################################
## some convenient utilities
###############################################################################

def _year_month(date):
    try:
        stamp = datetime.strptime(date, "%Y-%m-%d")
        return stamp.year, stamp.month
    except:
        pass
    try:
        stamp = datetime.strptime(date, "%Y-%m")
        return stamp.year, stamp.month
    except:
        pass
    try:
        stamp = datetime.strptime(date, "%Y")
        return stamp.year, None
    except:
        pass
    return None, None


def _element(xml, field):
    el = xml.find(field)
    if el is not None and el.text is not None and el.text != "":
        return el.text.strip()
    return None
