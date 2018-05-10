"""
Home for all article upload and ingest processing code

Main point of entry is the ingest_file function, which will do the validation, and if 
a crosswalk is available pass the DOM to be xwalked

"""

from lxml import etree
from portality import models
from portality.core import app
from datetime import datetime
import sys, traceback, re


class XWalk(object):

    def __init__(self):
        self.validation_log = None

    @staticmethod
    def is_legitimate_owner(article, owner):
        # get all the issns for the article
        b = article.bibjson()
        issns = b.get_identifiers(b.P_ISSN)
        issns += b.get_identifiers(b.E_ISSN)

        # check each issn against the index, and if a related journal is found
        # record the owner of that journal
        owners = []
        seen_issns = {}
        for issn in issns:
            journals = models.Journal.find_by_issn(issn)
            if journals is not None and len(journals) > 0:
                for j in journals:
                    owners.append(j.owner)
                    if j.owner not in seen_issns:
                        seen_issns[j.owner] = []
                    seen_issns[j.owner] += j.bibjson().issns()

        # deduplicate the list of owners
        owners = list(set(owners))

        # no owner means we can't confirm
        if len(owners) == 0:
            return False

        # multiple owners means ownership of this article is confused
        if len(owners) > 1:
            return False

        # single owner must still know of all supplied issns
        compare = list(set(seen_issns[owners[0]]))
        if len(compare) == 2:   # we only want to check issn parity for journals where there is more than one issn available.
            for issn in issns:
                if issn not in compare:
                    return False

        # true if the found owner is the same as the desired owner, otherwise false
        return owners[0] == owner

    @staticmethod
    def issn_ownership_status(article, owner):
        # get all the issns for the article
        b = article.bibjson()
        issns = b.get_identifiers(b.P_ISSN)
        issns += b.get_identifiers(b.E_ISSN)

        owned = []
        shared = []
        unowned = []
        unmatched = []

        # check each issn against the index, and if a related journal is found
        # record the owner of that journal
        seen_issns = {}
        for issn in issns:
            journals = models.Journal.find_by_issn(issn)
            if journals is not None and len(journals) > 0:
                for j in journals:
                    if issn not in seen_issns:
                        seen_issns[issn] = set()
                    seen_issns[issn].add(j.owner)

        for issn in issns:
            if issn not in seen_issns.keys():
                unmatched.append(issn)

        for issn, owners in seen_issns.iteritems():
            owners = list(owners)
            if len(owners) == 0:
                unowned.append(issn)
            elif len(owners) == 1 and owners[0] == owner:
                owned.append(issn)
            elif len(owners) == 1 and owners[0] != owner:
                unowned.append(issn)
            elif len(owners) > 1:
                if owner in owners:
                    shared.append(issn)
                else:
                    unowned.append(issn)

        return owned, shared, unowned, unmatched

    @staticmethod
    def get_duplicate(article, owner=None):
        """Get the most recent duplicate article."""
        return XWalk.get_duplicates(article, owner, max_results=1)

    @staticmethod
    def get_duplicates(article, owner=None, max_results=10):
        """Get all duplicates (or previous versions) of an article."""

        possible_articles_dict = XWalk.discover_duplicates(article, owner, max_results)
        if not possible_articles_dict:
            return []

        # We don't need the details of duplicate types, so flatten the lists.
        all_possible_articles = [article for dup_type in possible_articles_dict.values() for article in dup_type]

        # An article may fulfil more than one duplication criteria, so needs to be de-duplicated
        ids = []
        possible_articles = []
        for a in all_possible_articles:
            if a.id not in ids:
                ids.append(a.id)
                possible_articles.append(a)

        # Sort the articles newest -> oldest by last_updated so we can get the most recent at [0]
        possible_articles.sort(key=lambda x: datetime.strptime(x.last_updated, "%Y-%m-%dT%H:%M:%SZ"), reverse=True)

        return possible_articles[:max_results]

    @staticmethod
    def discover_duplicates(article, owner=None, results_per_match_type=10):
        """Identify duplicate articles, separated by duplication criteria"""
        # Get the owner's ISSNs
        issns = []
        if owner is not None:
            issns = models.Journal.issns_by_owner(owner)

        # We'll need the article bibjson a few times
        b = article.bibjson()

        # if we get more than one result, we'll record them here, and then at the end
        # if we haven't got a definitive match we'll pick the most likely candidate
        # (this isn't as bad as it sounds - the identifiers are pretty reliable, this catches
        # issues like where there are already duplicates in the data, and not matching one
        # of them propagates the issue)
        possible_articles = {}
        found = False

        # Checking by DOI is our first step
        dois = b.get_identifiers(b.DOI)
        if len(dois) > 0:
            # there should only be the one
            doi = dois[0]
            if isinstance(doi, basestring) and doi != '':
                articles = models.Article.duplicates(issns=issns, doi=doi, size=results_per_match_type)
                possible_articles['doi'] = [a for a in articles if a.id != article.id]
                if len(possible_articles['doi']) > 0:
                    found = True

        # Second test is to look by fulltext url
        urls = b.get_urls(b.FULLTEXT)
        if len(urls) > 0:
            # there should be only one, but let's allow for multiple
            articles = models.Article.duplicates(issns=issns, fulltexts=urls, size=results_per_match_type)
            possible_articles['fulltext'] = [a for a in articles if a.id != article.id]
            if possible_articles['fulltext']:
                found = True

        return possible_articles if found else None


class FormXWalk(XWalk):
    format_name = "form"
    
    def crosswalk_form(self, form, add_journal_info=True, limit_to_owner=None):
        article = models.Article()
        bibjson = article.bibjson()
        
        # title
        bibjson.title = form.title.data
        
        # doi
        doi = form.doi.data
        if doi is not None and doi != "":
            bibjson.add_identifier(bibjson.DOI, doi)
        
        # authors
        for subfield in form.authors:
            author = subfield.form.name.data
            aff = subfield.form.affiliation.data
            if author is not None and author != "":
                bibjson.add_author(author, affiliation=aff)
                
        # abstract
        abstract = form.abstract.data
        if abstract is not None and abstract != "":
            bibjson.abstract = abstract
        
        # keywords
        keywords = form.keywords.data
        if keywords is not None and keywords != "":
            ks = [k.strip() for k in keywords.split(",")]
            bibjson.set_keywords(ks)
            
        # fulltext
        ft = form.fulltext.data
        if ft is not None and ft != "":
            bibjson.add_url(ft, "fulltext")
        
        # publication year/month
        py = form.publication_year.data
        pm = form.publication_month.data
        if pm is not None:
            bibjson.month = pm
        if py is not None:
            bibjson.year = py
            
        # pissn
        pissn = form.pissn.data
        if pissn is not None and pissn != "":
            bibjson.add_identifier(bibjson.P_ISSN, pissn)
        
        # eissn
        eissn = form.eissn.data
        if eissn is not None and eissn != "":
            bibjson.add_identifier(bibjson.E_ISSN, eissn)
        
        # volume
        volume = form.volume.data
        if volume is not None and volume != "":
            bibjson.volume = volume
        
        # number
        number = form.number.data
        if number is not None and number != "":
            bibjson.number = number
        
        # start date
        start = form.start.data
        if start is not None and start != "":
            bibjson.start_page = start
        
        # end date
        end = form.end.data
        if end is not None and end != "":
            bibjson.end_page = end
        
        # add the journal info if requested
        if add_journal_info:
            article.add_journal_metadata()
        
        # before finalising, we need to determine whether this is a new article
        # or an update
        duplicate = self.get_duplicate(article, limit_to_owner)
        # print duplicate
        if duplicate is not None:
            article.merge(duplicate) # merge will take the old id, so this will overwrite
        
        return article


class DOAJXWalk(XWalk):
    format_name = "doaj"
    schema_path = app.config.get("SCHEMAS", {}).get("doaj")
    
    def __init__(self):
        # load the schema into memory for more efficient usage in repeat calls to the crosswalk
        if self.schema_path is None:
            raise IngestException(message="Unable to validate for DOAJXWalk, as schema path is not set in config")

        try:
            schema_file = open(self.schema_path)
            schema_doc = etree.parse(schema_file)
            self.schema = etree.XMLSchema(schema_doc)
        except Exception as e:
            raise IngestException(message="There was an error attempting to load schema from " + self.schema_path, inner=e)
    
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

    # FIXME: this doesn't appear to be used anywhere, so maybe we should remove it?
    def crosswalk_file(self, handle, add_journal_info=True, article_callback=None, limit_to_owner=None, fail_callback=None):
        doc = etree.parse(handle)
        return self.crosswalk_doc(doc, add_journal_info=add_journal_info, article_callback=article_callback, 
                                    limit_to_owner=limit_to_owner, fail_callback=fail_callback)
    
    def crosswalk_doc(self, doc, add_journal_info=True, article_callback=None, limit_to_owner=None, fail_callback=None):
        success = 0
        fail = 0
        update = 0
        new = 0
        all_shared = set()
        all_unowned = set()
        all_unmatched = set()
        
        # go through the records in the doc and crosswalk each one individually
        last_success = None
        root = doc.getroot()
        for record in root.findall("record"):
            article = self.crosswalk_article(record, add_journal_info=add_journal_info)
            # print "processing record", article.bibjson().title
            
            # once we have an article from the record, determine if it belongs to
            # the stated owner.  If not, we need to reject it
            if limit_to_owner is not None:
                legit = self.is_legitimate_owner(article, limit_to_owner)
                if not legit:
                    owned, shared, unowned, unmatched = self.issn_ownership_status(article, limit_to_owner)
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
            duplicate = self.get_duplicate(article, limit_to_owner)
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


class IngestException(Exception):
    def __init__(self, *args, **kwargs):
        self.stack = None
        self.message = kwargs.get("message")
        self.inner_message = kwargs.get("inner_message")
        self.inner = kwargs.get("inner")

        tb = sys.exc_info()[2]
        if self.inner is not None:
            if self.inner_message is None and hasattr(self.inner, "message"):
                self.inner_message = self.inner.message

            if tb is not None:
                self.stack = "".join(traceback.format_exception(self.inner.__class__, self.inner, tb))
            else:
                self.stack = "".join(traceback.format_exception_only(self.inner.__class__, self.inner))
        else:
            if tb is not None:
                self.stack = "".join(traceback.format_tb(tb))
            else:
                self.stack = traceback.format_exc()

    def trace(self):
        return self.stack


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
    
################################################################################
## main entry point to this module
################################################################################

xwalk_map = {DOAJXWalk.format_name : DOAJXWalk}


def article_upload_closure(upload_id):
    def article_callback(article):
        article.set_upload_id(upload_id)
        article.save(differentiate=True)
    return article_callback


def article_save_callback(article):
    article.save(differentiate=True)


def ingest_file(handle, format_name=None, owner=None, upload_id=None, article_fail_callback=None):
    name, xwalk, doc = check_schema(handle, format_name)

    # do the crosswalk
    try:
        cb = article_save_callback if upload_id is None else article_upload_closure(upload_id)
        results = xwalk.crosswalk_doc(doc, article_callback=cb, limit_to_owner=owner, fail_callback=article_fail_callback)
        return results
    except Exception as e:
        raise IngestException(message="Error occurred ingesting the records in the document", inner=e)


def check_schema(handle, format_name=None):
    try:
        doc = etree.parse(handle)
    except etree.XMLSyntaxError as e:   # although the treatment is the same, pulling this out so we remember what the primary kind of exception should be
        raise IngestException(message="Unable to parse XML file", inner=e)
    except Exception as e:
        raise IngestException(message="Unable to parse XML file", inner=e)

    actual_format = format_name
    validation_logs = {}
    xwalk = None
    valid = False
    if format_name is not None:
        klazz = xwalk_map.get(format_name)
        if klazz is not None:
            xwalk = klazz()
            valid = xwalk.validate(doc)
            if not valid:
                validation_logs[format_name] = xwalk.validation_log

    if not valid: # which can happen if there was no format name or if the format name was wrong
        # look for an alternative
        xwalk = None
        for name, x in xwalk_map.iteritems():
            if format_name is not None and format_name != name:
                # we may have already tried validating with this one already
                continue
            inst = x()
            valid = inst.validate(doc)
            if valid:
                xwalk = inst
                actual_format = name
                break
            else:
                validation_logs[name] = inst.validation_log
                xwalk = None

    # did we manage to detect a crosswalk?
    if xwalk is None:
        msg = ""
        for k, v in validation_logs.iteritems():
            msg += "Validation messages from schema '{x}': \n".format(x=k)
            msg += v + "\n\n"
        raise IngestException(message="Unable to validate document with any available ingesters", inner_message=msg)

    return actual_format, xwalk, doc
