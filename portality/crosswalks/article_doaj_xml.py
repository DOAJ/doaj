from portality.core import app
from lxml import etree
import re
from portality.bll import exceptions
from portality.crosswalks.exceptions import CrosswalkException
from portality import models
from datetime import datetime
from urlparse import urlparse


class DOAJXWalk(object):
    format_name = "doaj"
    schema_path = app.config.get("SCHEMAS", {}).get("doaj")

    def __init__(self):
        self.validation_log = ""

        # load the schema into memory for more efficient usage in repeat calls to the crosswalk
        if self.schema_path is None:
            raise exceptions.IngestException(message="Unable to validate for DOAJXWalk, as schema path is not set in config")

        try:
            schema_file = open(self.schema_path)
            schema_doc = etree.parse(schema_file)
            self.schema = etree.XMLSchema(schema_doc)
        except Exception as e:
            raise exceptions.IngestException(message="There was an error attempting to load schema from " + self.schema_path, inner=e)

    def validate_file(self, file_handle):
        # first try to parse the file
        try:
            doc = etree.parse(file_handle)
        except etree.XMLSyntaxError as e:   # although the treatment is the same, pulling this out so we remember what the primary kind of exception should be
            raise CrosswalkException(message="Unable to parse XML file", inner=e)
        except Exception as e:
            raise CrosswalkException(message="Unable to parse XML file", inner=e)

        # then pass the doc to the validator
        valid = self.validate(doc)

        if not valid:
            msg = "Validation message from schema '{x}': {y}\n".format(x=DOAJXWalk.format_name, y=self.validation_log)
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

    def crosswalk_file(self, file_handle, add_journal_info=True):
        doc = self.validate_file(file_handle)
        return self.crosswalk_doc(doc, add_journal_info=add_journal_info)

    def crosswalk_doc(self, doc, add_journal_info=True):
        # go through the records in the doc and crosswalk each one individually
        articles = []
        root = doc.getroot()
        for record in root.findall("record"):
            article = self.crosswalk_article(record, add_journal_info=add_journal_info)
            articles.append(article)

        return articles

    def crosswalk_article(self, record, add_journal_info=True):
        """
        Example record:
        <record>
          <language>eng</language>
          <publisher>Co-Action Publishing</publisher>
          <journalTitle>Tellus A</journalTitle>
          <issn>0280-6495</issn>
          <eissn>1600-0870</eissn>
          <publicationDate>2014-02-05</publicationDate>
          <volume>66</volume>
          <issue>0</issue>
          <startPage>1</startPage>
          <endPage>18</endPage>
          <doi>10.3402/tellusa.v66.21390</doi>
          <publisherRecordId>21390</publisherRecordId>
          <documentType>Original</documentType>
          <title language="eng">LakeMIP Kivu...</title>
          <authors>
             <author>
                <name>WIM Thiery</name>
                <affiliationId>1</affiliationId>
            </author>
         </authors>
          <affiliationsList>
             <affiliationName affiliationId="1">
		            Department of Earth and Environmental Sciences...</affiliationName>
         </affiliationsList>

          <abstract language="eng">The African great...</abstract>
          <fullTextUrl format="pdf">http://www.tellusa.net/index.php/tellusa/article/download/21390/pdf_1</fullTextUrl>
          <keywords language="eng">
             <keyword>lake modelling</keyword>
         </keywords>
        </record>
        """
        article = models.Article()
        bibjson = article.bibjson()

        # language
        lang = _element(record, "language")
        if lang is not None:
            bibjson.journal_language = lang

        # publisher
        pub = _element(record, "publisher")
        if pub is not None:
            bibjson.publisher = pub

        # journal title
        jt = _element(record, "journalTitle")
        if jt is not None:
            bibjson.journal_title = jt

        # p-issn
        pissn = _element(record, "issn")
        if pissn is not None:
            bibjson.add_identifier(bibjson.P_ISSN, pissn.upper())

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
# some convenient utilities
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
