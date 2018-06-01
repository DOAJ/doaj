from portality.core import app
from lxml import etree
import re
from portality.bll.doaj import DOAJ
from portality.bll import exceptions
from portality import models
from datetime import datetime

class DOAJXWalk(object):
    format_name = "doaj"
    schema_path = app.config.get("SCHEMAS", {}).get("doaj")

    def __init__(self):
        # load the schema into memory for more efficient usage in repeat calls to the crosswalk
        if self.schema_path is None:
            raise exceptions.IngestException(message="Unable to validate for DOAJXWalk, as schema path is not set in config")

        try:
            schema_file = open(self.schema_path)
            schema_doc = etree.parse(schema_file)
            self.schema = etree.XMLSchema(schema_doc)
        except Exception as e:
            raise exceptions.IngestException(message="There was an error attempting to load schema from " + self.schema_path, inner=e)

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

    def crosswalk_doc(self, doc, add_journal_info=True, article_callback=None, limit_to_owner=None, fail_callback=None):
        success = 0
        fail = 0
        update = 0
        new = 0
        all_shared = set()
        all_unowned = set()
        all_unmatched = set()

        articleService = DOAJ.articleService()

        # go through the records in the doc and crosswalk each one individually
        last_success = None
        root = doc.getroot()
        for record in root.findall("record"):
            article = self.crosswalk_article(record, add_journal_info=add_journal_info)
            # print "processing record", article.bibjson().title

            # once we have an article from the record, determine if it belongs to
            # the stated owner.  If not, we need to reject it
            if limit_to_owner is not None:
                legit = articleService.is_legitimate_owner(article, limit_to_owner)
                if not legit:
                    owned, shared, unowned, unmatched = articleService.issn_ownership_status(article, limit_to_owner)
                    all_shared.update(shared)
                    all_unowned.update(unowned)
                    all_unmatched.update(unmatched)
                    fail += 1
                    if fail_callback:
                        fail_callback(article)
                    continue

            # print "legit"

            # before finalising, we need to determine whether this is a new article
            # or an update
            duplicate = articleService.get_duplicate(article, limit_to_owner)
            # print duplicate
            if duplicate is not None:
                update += 1
                article.merge(duplicate) # merge will take the old id, so this will overwrite
            else:
                new += 1

            # if we get to here without failing, then we call the article callback
            # (which can do something like save)
            if article_callback is not None:
                article_callback(article)
                last_success = article
            success += 1

        # run the block so we are sure the records have saved
        if last_success is not None:
            models.Article.block(last_success.id, last_success.last_updated)

        # return some stats on the import
        return {"success" : success, "fail" : fail, "update" : update, "new" : new, "shared" : all_shared, "unowned" : all_unowned, "unmatched" : all_unmatched}

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
                <email>wim.thiery@ees.kuleuven.be</email>
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
                email = _element(ael, "email")
                affid = _element(ael, "affiliationId")
                aff = affiliations.get(affid)
                bibjson.add_author(name, email=email, affiliation=aff)

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