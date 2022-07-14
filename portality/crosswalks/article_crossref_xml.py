from portality.core import app
from lxml import etree
import re
from portality.bll import exceptions
from portality.crosswalks.exceptions import CrosswalkException
from portality import models
from portality.ui.messages import Messages



class CrossrefXWalk442(object):
    """
    ~~Crossref442XML:Crosswalk->Crossref442:Feature~~
    """
    format_name = "crossref442"
    NS = {'x': 'http://www.crossref.org/schema/4.4.2', 'j': 'http://www.ncbi.nlm.nih.gov/JATS1'}

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

    def __init__(self):
        self.validation_log = ""
        self.schema_path = app.config.get("SCHEMAS", {}).get(self.format_name)

        # load the schema into memory for more efficient usage in repeat calls to the crosswalk
        if self.schema_path is None:
            raise exceptions.IngestException(
                message="Unable to validate for " + self.format_name + ", as schema path is not set in config")

        while app.config["CROSSREF442_SCHEMA"] is None:
            continue

        while app.config["CROSSREF531_SCHEMA"] is None:
            continue

        # ~~->CrossrefXML:Schema~~
        self.schema = app.config["CROSSREF442_SCHEMA"]

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
            msg = "Validation message from schema '{x}': {y}\n".format(x=self.format_name,
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
        body = root.find("x:body", self.NS)
        journals = body.findall("x:journal", self.NS)
        if journals is not None:
            for journal in journals:
                arts = journal.findall("x:journal_article", self.NS)
                for record in arts:
                    article = self.crosswalk_article(record, journal)
                    articles.append(article)

        return articles

    def crosswalk_article(self, record, journal):
        article = models.Article()  # ~~->Article:Model~~
        bibjson = article.bibjson()

        self.extract_title(journal, bibjson)
        self.extract_issns(journal, bibjson)
        self.extract_publication_date(record, journal, bibjson)
        self.extract_volume(journal, bibjson)
        self.extract_issue(journal, bibjson)
        self.extract_pages(record, journal, bibjson)
        self.extract_doi(record, journal, bibjson)
        self.extract_fulltext(record, journal, bibjson)
        self.extract_article_title(record, journal, bibjson)
        self.extract_authors(record, journal, bibjson)
        self.extract_abstract(record, journal, bibjson)

        return article


    ###############################################################################
    ## extractors
    ###############################################################################


    def extract_title(self, journal, bibjson):
        jm = journal.find("x:journal_metadata", self.NS)
        if jm is not None:
            jt = _element(jm, "x:full_title", self.NS)
            if jt is not None:
                bibjson.journal_title = jt

    def extract_issns(self, journal, bibjson):
        md = journal.find("x:journal_metadata", self.NS)
        if md is not None:
            issns = md.findall("x:issn", self.NS)

            # if more than 2 issns raise the exception
            if len(issns) > 2:
                raise CrosswalkException(message=Messages.EXCEPTION_TOO_MANY_ISSself.NS)
            if len(issns) == 1:
                if len(issns[0].attrib) == 0 or issns[0].attrib["media_type"] == 'electronic':
                    bibjson.add_identifier(bibjson.E_ISSN, issns[0].text.upper())
                elif issns[0].attrib["media_type"] == 'print':
                    bibjson.add_identifier(bibjson.P_ISSN, issns[0].text.upper())

            elif len(issns) == 2:
                attrs = [0, 0]
                if len(issns[0].attrib) != 0:
                    attrs[0] = issns[0].attrib["media_type"]
                if len(issns[1].attrib) != 0:
                    attrs[1] = issns[1].attrib["media_type"]

                # if both issns have the same type - raise the exception
                if attrs[0] != 0 and attrs[0] == attrs[1]:
                    raise CrosswalkException(
                        message=Messages.EXCEPTION_ISSNS_OF_THE_SAME_TYPE.format(type=issns[1].attrib["media_type"]))

                # if both issns have the same value - raise the exception
                if issns[0].text.upper() == issns[1].text.upper():
                    raise CrosswalkException(
                        message=Messages.EXCEPTION_IDENTICAL_PISSN_AND_EISSN.format(value=issns[0].text.upper()))

                if bool(attrs[0]) != bool(attrs[1]):
                    if attrs[0] != 0:
                        if attrs[0] == "electronic":
                            attrs[1] = "print"
                        else:
                            attrs[1] = "electronic"
                    else:
                        if attrs[1] == "electronic":
                            attrs[0] = "print"
                        else:
                            attrs[0] = "electronic"
                elif attrs[0] == 0:
                    attrs[0] = "electronic"
                    attrs[1] = "print"

                bibjson.add_identifier(bibjson.P_ISSN if attrs[0] == "print" else bibjson.E_ISSN, issns[0].text.upper())
                bibjson.add_identifier(bibjson.P_ISSN if attrs[1] == "print" else bibjson.E_ISSN, issns[1].text.upper())

    def extract_publication_date(self, record, journal, bibjson):
        pd = record.find("x:publication_date", self.NS)

        if pd is not None:
            bibjson.year = _element(pd, "x:year", self.NS)
            bibjson.month = _element(pd, "x:month", self.NS)

    def extract_volume(self, journal, bibjson):
        issue = journal.find("x:journal_issue", self.NS)

        if issue is not None:
            vol = issue.find("x:journal_volume", self.NS)
            if vol is not None:
                volume = _element(vol, "x:volume", self.NS)
                if volume is not None:
                    bibjson.volume = volume

    def extract_issue(self, journal, bibjson):
        issue = journal.find("x:journal_issue", self.NS)
        if issue is not None:
            number = _element(issue, "x:issue", self.NS)
            if number is not None:
                bibjson.number = number

    def extract_pages(self, record, journal, bibjson):
        pages = record.find('x:pages', self.NS)
        # start page
        if pages is not None:
            sp = _element(pages, "x:first_page", self.NS)
            if sp is not None:
                bibjson.start_page = sp

            # end page
            ep = _element(pages, "x:last_page", self.NS)
            if ep is not None:
                bibjson.end_page = ep

    def extract_doi(self, record, journal, bibjson):
        d = record.find("x:doi_data", self.NS)
        if d is not None:
            # doi
            doi = _element(d, "x:doi", self.NS)
            if doi is not None:
                bibjson.add_identifier(bibjson.DOI, doi)

    def extract_fulltext(self, record, journal, bibjson):
        d = record.find("x:doi_data", self.NS)
        ftel = _element(d, "x:resource", self.NS)
        if ftel is not None:
            bibjson.add_url(ftel, "fulltext", self.NS)

    def extract_article_title(self, record, journal, bibjson):
        titles = record.find('x:titles', self.NS)
        if titles is not None:
            title = _element(titles, "x:title", self.NS)
            if title is not None:
                bibjson.title = title

    def extract_authors(self, record, journal, bibjson):
        contributors = record.find("x:contributors", self.NS)
        if contributors is None:
            raise CrosswalkException(message=Messages.EXCEPTION_NO_CONTRIBUTORS_FOUND,
                                     inner_message=Messages.EXCEPTION_NO_CONTRIBUTORS_EXPLANATION)
        contribs = contributors.findall("x:person_name", self.NS)
        if contribs is not None:
            for ctb in contribs:
                if ctb.attrib["contributor_role"] == 'author':
                    name = _element(ctb, "x:surname", self.NS)
                    e = _element(ctb, "x:given_name", self.NS)
                    name = e + ' ' + name if e else name
                    e = _element(ctb, "x:affiliation", self.NS)
                    affiliation = e if e else None
                    e = _element(ctb, "x:ORCID", self.NS)
                    orcid = e if e else None
                    bibjson.add_author(name, affiliation, orcid)

    def extract_abstract(self, record, journal, bibjson):
        abstract_par = record.find("j:abstract", self.NS)
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

###############################################################################
## Crossref 5.3.1 Xwalk
###############################################################################

class CrossrefXWalk531(CrossrefXWalk442):
    """
        ~~Crossref531XML:Crosswalk->Crossref531:Feature~~
        """
    format_name = "crossref531"
    NS = {'x': 'http://www.crossref.org/schema/5.3.1', 'j': 'http://www.ncbi.nlm.nih.gov/JATS1'}

    def __init__(self):
        super(CrossrefXWalk531,self).__init__()
        self.schema = app.config["CROSSREF531_SCHEMA"]

###############################################################################
## some convenient utilities
###############################################################################

def _element(xml, field, namespace):
    el = xml.find(field, namespace)
    if el is not None:
        # self converts the entire element to a string, so that we can handle the possibility of
        # embedded html tags, etc.
        # etree.tostring doesn't actually produce a string, but a byte array, so we must specify
        # the encoding and THEN also decode it using that same encoding to get an actual string
        string = etree.tostring(el, encoding="utf-8").decode("utf-8")
        start = string.index(">") + 1
        end = string.rindex('</')
        text = string[start:end]
        return text if text else None
    else:
        return None
