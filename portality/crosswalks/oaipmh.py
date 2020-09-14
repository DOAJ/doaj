import base64, sys, re
from lxml import etree
from datetime import datetime
from portality.core import app
from portality import datasets
from copy import deepcopy


#####################################################################
# Crosswalks for OAI-PMH
#####################################################################

class OAI_Crosswalk(object):
    PMH_NAMESPACE = "http://www.openarchives.org/OAI/2.0/"
    PMH = "{%s}" % PMH_NAMESPACE

    XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
    XSI = "{%s}" % XSI_NAMESPACE

    NSMAP = {None: PMH_NAMESPACE, "xsi": XSI_NAMESPACE}

    def crosswalk(self, record):
        raise NotImplementedError()

    def header(self, record):
        raise NotImplementedError()

    def _generate_header_subjects(self, parent_element, subjects):
        if subjects is None:
            subjects = []

        for subs in subjects:
            scheme = subs.get("scheme", '')
            term = subs.get("term", '')

            if term:
                prefix = ''
                if scheme:
                    prefix = scheme + ':'

                subel = etree.SubElement(parent_element, self.PMH + "setSpec")
                set_text(subel, make_set_spec(prefix + term))


class OAI_DC(OAI_Crosswalk):
    OAIDC_NAMESPACE = "http://www.openarchives.org/OAI/2.0/oai_dc/"
    OAIDC = "{%s}" % OAIDC_NAMESPACE

    DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
    DC = "{%s}" % DC_NAMESPACE

    NSMAP = deepcopy(OAI_Crosswalk.NSMAP)
    NSMAP.update({"oai_dc": OAIDC_NAMESPACE, "dc": DC_NAMESPACE})

    def _generate_subjects(self, parent_element, subjects, keywords):
        if keywords is None:
            keywords = []
        if subjects is None:
            subjects = []

        for keyword in keywords:
            subj = etree.SubElement(parent_element, self.DC + "subject")
            set_text(subj, keyword)

        for subs in subjects:
            scheme = subs.get("scheme")
            code = subs.get("code")
            term = subs.get("term")

            if scheme and scheme.lower() == 'lcc':
                attrib = {"{{{nspace}}}type".format(nspace=self.XSI_NAMESPACE): "dcterms:LCSH"}
                termtext = term
                codetext = code
            else:
                attrib = {}
                termtext = scheme + ':' + term if term else None
                codetext = scheme + ':' + code if code else None

            if termtext:
                subel = etree.SubElement(parent_element, self.DC + "subject", **attrib)
                set_text(subel, termtext)

            if codetext:
                sel2 = etree.SubElement(parent_element, self.DC + "subject", **attrib)
                set_text(sel2, codetext)


class OAI_DC_Article(OAI_DC):
    def crosswalk(self, record):
        bibjson = record.bibjson()

        metadata = etree.Element(self.PMH + "metadata", nsmap=self.NSMAP)
        oai_dc = etree.SubElement(metadata, self.OAIDC + "dc")
        oai_dc.set(self.XSI + "schemaLocation",
            "http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd")

        if bibjson.title is not None:
            title = etree.SubElement(oai_dc, self.DC + "title")
            set_text(title, bibjson.title)

        # all the external identifiers (ISSNs, etc)
        for identifier in bibjson.get_identifiers():
            idel = etree.SubElement(oai_dc, self.DC + "identifier")
            set_text(idel, identifier.get("id"))

        # our internal identifier
        url = app.config['BASE_URL'] + "/article/" + record.id
        idel = etree.SubElement(oai_dc, self.DC + "identifier")
        set_text(idel, url)

        # work out the date of publication
        date = bibjson.get_publication_date()
        if date != "":
            monthyear = etree.SubElement(oai_dc, self.DC + "date")
            set_text(monthyear, date)

        for url in bibjson.get_urls():
            urlel = etree.SubElement(oai_dc, self.DC + "relation")
            set_text(urlel, url.get("url"))

        for identifier in bibjson.get_identifiers(idtype=bibjson.P_ISSN) + bibjson.get_identifiers(idtype=bibjson.E_ISSN):
            journallink = etree.SubElement(oai_dc, self.DC + "relation")
            set_text(journallink, app.config['BASE_URL'] + "/toc/" + identifier)

        if bibjson.abstract is not None:
            abstract = etree.SubElement(oai_dc, self.DC + "description")
            set_text(abstract, bibjson.abstract)

        if len(bibjson.author) > 0:
            for author in bibjson.author:
                ael = etree.SubElement(oai_dc, self.DC + "creator")
                set_text(ael, author.get("name"))
                if author.get("orcid_id"):
                    ael.set('id', author.get("orcid_id"))

        if bibjson.publisher is not None:
            pubel = etree.SubElement(oai_dc, self.DC + "publisher")
            set_text(pubel, bibjson.publisher)

        objecttype = etree.SubElement(oai_dc, self.DC + "type")
        set_text(objecttype, "article")

        self._generate_subjects(parent_element=oai_dc, subjects=bibjson.subjects(), keywords=bibjson.keywords)

        jlangs = bibjson.journal_language
        if jlangs is not None:
            for language in jlangs:
                langel = etree.SubElement(oai_dc, self.DC + "language")
                set_text(langel, language)

        if bibjson.get_journal_license() is not None:
            prov = etree.SubElement(oai_dc, self.DC + "provenance")
            set_text(prov, "Journal Licence(s): " + ", ".join([lic.get("type") for lic in bibjson.journal_licenses if "type" in lic]))

        citation = self._make_citation(bibjson)
        if citation is not None:
            cite = etree.SubElement(oai_dc, self.DC + "source")
            set_text(cite, citation)

        return metadata

    def header(self, record):
        bibjson = record.bibjson()
        head = etree.Element(self.PMH + "header", nsmap=self.NSMAP)

        identifier = etree.SubElement(head, self.PMH + "identifier")
        set_text(identifier, make_oai_identifier(record.id, "article"))

        datestamp = etree.SubElement(head, self.PMH + "datestamp")
        set_text(datestamp, normalise_date(record.last_updated))

        self._generate_header_subjects(parent_element=head, subjects=bibjson.subjects())
        return head

    def _make_citation(self, bibjson):
        # [title], Vol [vol], Iss [iss], Pp [start]-end (year)
        ctitle = bibjson.journal_title
        cvol = bibjson.volume
        ciss = bibjson.number
        cstart = bibjson.start_page
        cend = bibjson.end_page
        cyear = bibjson.year

        citation = ""
        if ctitle is not None:
            citation += ctitle

        if cvol is not None:
            if citation != "":
                citation += ", "
            citation += "Vol " + cvol

        if ciss is not None:
            if citation != "":
                citation += ", "
            citation += "Iss " + ciss

        if cstart is not None or cend is not None:
            if citation != "":
                citation += ", "
            if (cstart is None and cend is not None) or (cstart is not None and cend is None):
                citation += "p "
            else:
                citation += "Pp "
            if cstart is not None:
                citation += cstart
            if cend is not None:
                if cstart is not None:
                    citation += "-"
                citation += cend

        if cyear is not None:
            if citation != "":
                citation += " "
            citation += "(" + cyear + ")"

        return citation if citation != "" else None


class OAI_DC_Journal(OAI_DC):
    def crosswalk(self, record):
        bibjson = record.bibjson()

        metadata = etree.Element(self.PMH + "metadata", nsmap=self.NSMAP)
        oai_dc = etree.SubElement(metadata, self.OAIDC + "dc")
        oai_dc.set(self.XSI + "schemaLocation",
            "http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd")

        if bibjson.title is not None:
            title = etree.SubElement(oai_dc, self.DC + "title")
            set_text(title, bibjson.title)

        # external identifiers (ISSNs, etc)
        for identifier in bibjson.get_identifiers():
            idel = etree.SubElement(oai_dc, self.DC + "identifier")
            set_text(idel, identifier.get("id"))

        # our internal identifier
        url = app.config["BASE_URL"] + "/toc/" + record.toc_id
        idel = etree.SubElement(oai_dc, self.DC + "identifier")
        set_text(idel, url)

        if bibjson.language is not None and len(bibjson.language) > 0:
            for language in bibjson.language:
                lang = etree.SubElement(oai_dc, self.DC + "language")
                set_text(lang, language)

        if bibjson.licenses is not None and len(bibjson.licenses) > 0:
            for license in bibjson.licenses:
                rights = etree.SubElement(oai_dc, self.DC + "rights")
                set_text(rights, license.get("type"))

        if bibjson.publisher is not None:
            pub = etree.SubElement(oai_dc, self.DC + "publisher")
            set_text(pub, bibjson.publisher)

        # We have removed the list of URLs in in model v2, so we need to gather the URLS one by one
        if bibjson.oa_statement_url is not None:
            urlel = etree.SubElement(oai_dc, self.DC + "relation")
            set_text(urlel, bibjson.oa_statement_url)

        if bibjson.journal_url is not None:
            urlel = etree.SubElement(oai_dc, self.DC + "relation")
            set_text(urlel, bibjson.journal_url)

        if bibjson.aims_scope_url is not None:
            urlel = etree.SubElement(oai_dc, self.DC + "relation")
            set_text(urlel, bibjson.aims_scope_url)

        if bibjson.author_instructions_url is not None:
            urlel = etree.SubElement(oai_dc, self.DC + "relation")
            set_text(urlel, bibjson.author_instructions_url)

        if bibjson.waiver_url is not None:
            urlel = etree.SubElement(oai_dc, self.DC + "relation")
            set_text(urlel, bibjson.waiver_url)

        # URLs end

        created = etree.SubElement(oai_dc, self.DC + "date")
        set_text(created, normalise_date(record.created_date))

        objecttype = etree.SubElement(oai_dc, self.DC + "type")
        set_text(objecttype, "journal")

        self._generate_subjects(parent_element=oai_dc, subjects=bibjson.subjects(), keywords=bibjson.keywords)

        return metadata

    def header(self, record):
        bibjson = record.bibjson()
        head = etree.Element(self.PMH + "header", nsmap=self.NSMAP)

        identifier = etree.SubElement(head, self.PMH + "identifier")
        set_text(identifier, make_oai_identifier(record.id, "journal"))

        datestamp = etree.SubElement(head, self.PMH + "datestamp")
        set_text(datestamp, normalise_date(record.last_updated))

        self._generate_header_subjects(parent_element=head, subjects=bibjson.subjects())
        return head


class OAI_DOAJ_Article(OAI_Crosswalk):
    OAI_DOAJ_NAMESPACE = "http://doaj.org/features/oai_doaj/1.0/"
    OAI_DOAJ = "{%s}" % OAI_DOAJ_NAMESPACE

    NSMAP = deepcopy(OAI_Crosswalk.NSMAP)
    NSMAP.update({"oai_doaj": OAI_DOAJ_NAMESPACE})

    def crosswalk(self, record):
        bibjson = record.bibjson()

        metadata = etree.Element(self.PMH + "metadata", nsmap=self.NSMAP)
        oai_doaj_article = etree.SubElement(metadata, self.OAI_DOAJ + "doajArticle")
        oai_doaj_article.set(self.XSI + "schemaLocation",
            "http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd http://doaj.org/features/oai_doaj/1.0/ https://doaj.org/static/doaj/doajArticles.xsd")

        # look up the journal's language
        jlangs = bibjson.journal_language
        # first, if there are any languages recorded, get the 3-char code
        # corresponding to the first language
        language = None
        if jlangs:
            if isinstance(jlangs, list):
                jlang = jlangs[0]
            lang = datasets.language_for(jlang)
            if lang is not None:
                language = lang.alpha_3

        # if the language code lookup was successful, add it to the
        # result
        if language:
            langel = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "language")
            set_text(langel, language)

        if bibjson.publisher:
            publel = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "publisher")
            set_text(publel, bibjson.publisher)

        if bibjson.journal_title:
            journtitel = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "journalTitle")
            set_text(journtitel, bibjson.journal_title)

        # all the external identifiers (ISSNs, etc)
        if bibjson.get_one_identifier(bibjson.P_ISSN):
            issn = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "issn")
            set_text(issn, bibjson.get_one_identifier(bibjson.P_ISSN))

        if bibjson.get_one_identifier(bibjson.E_ISSN):
            eissn = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "eissn")
            set_text(eissn, bibjson.get_one_identifier(bibjson.E_ISSN))

        # work out the date of publication
        date = bibjson.get_publication_date()
        # convert it to the format required by the XML schema by parsing
        # it into a Python datetime and getting it back out as string.
        # If it's not coming back properly from the bibjson, throw it
        # away.
        try:
            date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
            date = date.strftime("%Y-%m-%d")
        except:
            date = ""

        if date:
            monthyear = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "publicationDate")
            set_text(monthyear, date)

        if bibjson.volume:
            volume = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "volume")
            set_text(volume, bibjson.volume)

        if bibjson.number:
            issue = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "issue")
            set_text(issue, bibjson.number)

        if bibjson.start_page:
            start_page = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "startPage")
            set_text(start_page, bibjson.start_page)

        if bibjson.end_page:
            end_page = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "endPage")
            set_text(end_page, bibjson.end_page)

        if bibjson.get_one_identifier(bibjson.DOI):
            doi = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "doi")
            set_text(doi, bibjson.get_one_identifier(bibjson.DOI))

        if record.publisher_record_id():
            pubrecid = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "publisherRecordId")
            set_text(pubrecid, record.publisher_record_id())

        # document type
        # as of Mar 2015 this was not being ingested when people upload XML
        # conforming to the doajArticle schema, so it's not being output either

        if bibjson.title is not None:
            title = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "title")
            set_text(title, bibjson.title)

        affiliations = []
        if bibjson.author:
            authors_elem = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "authors")
            for author in bibjson.author:  # bibjson.author is a list, despite the name
                author_elem = etree.SubElement(authors_elem, self.OAI_DOAJ + "author")
                if author.get('name'):
                    name_elem = etree.SubElement(author_elem, self.OAI_DOAJ + "name")
                    set_text(name_elem, author.get('name'))
                if author.get('email'):
                    email_elem = etree.SubElement(author_elem, self.OAI_DOAJ + "email")
                    set_text(email_elem, author.get('email'))
                if author.get('affiliation'):
                    new_affid = len(affiliations)  # use the length of the list as the id for each new item
                    affiliations.append((new_affid, author['affiliation']))
                    author_affiliation_elem = etree.SubElement(author_elem, self.OAI_DOAJ + "affiliationId")
                    set_text(author_affiliation_elem, str(new_affid))
                if author.get('orcid_id'):
                    orcid_elem = etree.SubElement(author_elem, self.OAI_DOAJ + "orcid_id")
                    set_text(orcid_elem, author.get("orcid_id"))

        if affiliations:
            affiliations_elem = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "affiliationsList")
            for affid, affiliation in affiliations:
                attrib = {"affiliationId": str(affid)}
                affiliation_elem = etree.SubElement(affiliations_elem, self.OAI_DOAJ + "affiliationName", **attrib)
                set_text(affiliation_elem, affiliation)

        if bibjson.abstract:
            abstract = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "abstract")
            set_text(abstract, bibjson.abstract)

        ftobj = bibjson.get_single_url('fulltext', unpack_urlobj=False)
        if ftobj:
            attrib = {}
            if "content_type" in ftobj:
                attrib['format'] = ftobj['content_type']

            fulltext_url_elem = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + "fullTextUrl", **attrib)

            if "url" in ftobj:
                set_text(fulltext_url_elem, ftobj['url'])

        if bibjson.keywords:
            keywords_elem = etree.SubElement(oai_doaj_article, self.OAI_DOAJ + 'keywords')
            for keyword in bibjson.keywords:
                kel = etree.SubElement(keywords_elem, self.OAI_DOAJ + 'keyword')
                set_text(kel, keyword)

        return metadata

    def header(self, record):
        bibjson = record.bibjson()
        head = etree.Element(self.PMH + "header", nsmap=self.NSMAP)

        identifier = etree.SubElement(head, self.PMH + "identifier")
        set_text(identifier, make_oai_identifier(record.id, "article"))

        datestamp = etree.SubElement(head, self.PMH + "datestamp")
        set_text(datestamp, normalise_date(record.last_updated))

        self._generate_header_subjects(parent_element=head, subjects=bibjson.subjects())
        return head


CROSSWALKS = {
    "oai_dc": {
        "article": OAI_DC_Article,
        "journal": OAI_DC_Journal
    },
    'oai_doaj': {
        "article": OAI_DOAJ_Article
    }
}


#####################################################################
# Utility methods/objects
#####################################################################

def make_set_spec(setspec):
    b = base64.urlsafe_b64encode(setspec.encode("utf-8"))
    setspec_utf8 = b.decode("utf-8")
    s = setspec_utf8.replace('=', '~')
    return s


def make_oai_identifier(identifier, qualifier):
    return "oai:" + app.config.get("OAIPMH_IDENTIFIER_NAMESPACE") + "/" + qualifier + ":" + identifier


def normalise_date(date):
    # FIXME: do we need a more powerful date normalisation routine?
    try:
        datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
        return date
    except:
        return "T".join(date.split(" ")) + "Z"


###########################################################
# XML Character encoding hacks
###########################################################

_illegal_unichrs = [(0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F),
                    (0x7F, 0x84), (0x86, 0x9F),
                    (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF)]
if sys.maxunicode >= 0x10000:  # not narrow build
    _illegal_unichrs.extend([(0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF),
                             (0x3FFFE, 0x3FFFF), (0x4FFFE, 0x4FFFF),
                             (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
                             (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF),
                             (0x9FFFE, 0x9FFFF), (0xAFFFE, 0xAFFFF),
                             (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
                             (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF),
                             (0xFFFFE, 0xFFFFF), (0x10FFFE, 0x10FFFF)])
_illegal_ranges = ["%s-%s" % (chr(low), chr(high))
                   for (low, high) in _illegal_unichrs]
_illegal_xml_chars_RE = re.compile('[%s]' % ''.join(_illegal_ranges))


def valid_XML_char_ordinal(i):
    return ( # conditions ordered by presumed frequency
        0x20 <= i <= 0xD7FF
        or i in (0x9, 0xA, 0xD)
        or 0xE000 <= i <= 0xFFFD
        or 0x10000 <= i <= 0x10FFFF
        )


def clean_unreadable(input_string):
    try:
        if type(input_string) == str:
            return _illegal_xml_chars_RE.sub("", input_string)
        else:
            return _illegal_xml_chars_RE.sub("", input_string.decode("utf-8"))
    except TypeError as e:
        app.logger.error("Unable to strip illegal XML chars from: {x}, {y}".format(x=input_string, y=type(input_string)))
        return None


def xml_clean(input_string):
    cleaned_string = ''.join(c for c in input_string if valid_XML_char_ordinal(ord(c)))
    return cleaned_string


def set_text(element, input_string):
    if input_string is None:
        return
    input_string = clean_unreadable(input_string)
    try:
        element.text = input_string
    except ValueError:
        element.text = xml_clean(input_string)