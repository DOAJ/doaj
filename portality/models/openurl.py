import re, json
from flask import url_for
from portality.models import Journal, Article
from portality.core import app
from copy import deepcopy
from portality.util import parse_date
from portality.lib import analytics

JOURNAL_SCHEMA_KEYS = ['doi', 'aulast', 'aufirst', 'auinit', 'auinit1', 'auinitm', 'ausuffix', 'au', 'aucorp', 'atitle',
                       'jtitle', 'stitle', 'date', 'chron', 'ssn', 'quarter', 'volume', 'part', 'issue', 'spage',
                       'epage', 'pages', 'artnum', 'issn', 'eissn', 'isbn', 'coden', 'sici', 'genre']

# The genres from the OpenURL schema we support
SUPPORTED_GENRES = ['journal', 'article']

# Mapping from OpenURL schema to both supported models (Journal, Article)
OPENURL_TO_ES = {
    'au': (None, 'author.name.exact'),
    'aucorp': (None, 'author.affiliation.exact'),
    'atitle': (None, 'bibjson.title.exact'),
    'jtitle': ('index.title.exact', 'bibjson.journal.title.exact'),    # Note we use index.title.exact for journals, to support continuations
    'stitle': ('bibjson.alternative_title.exact', None),
    'date': (None, 'bibjson.year.exact'),
    'volume': (None, 'bibjson.journal.volume.exact'),
    'issue': (None, 'bibjson.journal.number.exact'),
    'spage': (None, 'bibjson.start_page.exact'),
    'epage': (None, 'bibjson.end_page.exact'),
    'issn': ('index.issn.exact', 'index.issn.exact'),   # bibjson.identifier.id.exact
    'eissn': ('index.issn.exact', 'index.issn.exact'),
    'isbn': ('index.issn.exact', 'index.issn.exact')
}

# Terms search template. Ensure all queries from OpenURL return publicly visible results with in_doaj : true
IN_DOAJ_TERM = {"term": {"admin.in_doaj": True}}
TERMS_SEARCH = {"query": {"bool": {"must": [IN_DOAJ_TERM]}}}


class OpenURLRequest(object):
    """
    Based on the fields from ofi/fmt:kev:mtx:journal schema for Journals in OpenURL 1.0
    This is the only schema the DOAJ supports.
    """

    def __init__(self, **kwargs):

        # Initialise the OpenURLRequest object with empty attributes
        for key in JOURNAL_SCHEMA_KEYS:
            setattr(self, key, None)

        # Save any attributes specified at creation time
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)

    def __str__(self):
        return "OpenURLRequest{" + ", ".join(["%s : %s" % (x, getattr(self, x)) for x in JOURNAL_SCHEMA_KEYS if getattr(self, x)]) + "}"

    def query_es(self):
        """
        Query Elasticsearch for a set of matches for this request.
        :return: The results of a query through the dao, a JSON object.
        """
        # Copy to the template, which will be populated with terms
        populated_query = deepcopy(TERMS_SEARCH)

        # Get all of the attributes with values set.
        set_attributes = [(x, getattr(self, x)) for x in JOURNAL_SCHEMA_KEYS[:-1] if getattr(self, x)]

        # If we don't have a genre, guess journal FIXME: is it correct to assume journal?
        if not self.genre:
            self.genre = SUPPORTED_GENRES[0]    # TODO: we may want to handle 404 instead

        # Set i to use either our mapping for journals or articles
        i = SUPPORTED_GENRES.index(getattr(self, 'genre').lower())

        # Add the attributes to the query
        for (k, v) in set_attributes:
            es_term = OPENURL_TO_ES[k][i]
            if es_term is None:
                continue
            else:
                term = {"term": {es_term: v}}
            populated_query["query"]["bool"]["must"].append(term)

        # avoid doing an empty query
        if len(populated_query["query"]["bool"]["must"]) == 0:
            app.logger.debug("No valid search terms in OpenURL object")
            return None

        # Return the results of the query
        if i == 0:
            app.logger.debug("OpenURL query to journal: " + json.dumps(populated_query))
            return Journal.query(q=populated_query)
        elif i == 1:
            app.logger.debug("OpenURL query to article: " + json.dumps(populated_query))
            return Article.query(q=populated_query)

    def get_result_url(self):
        """
        Get the URL for this OpenURLRequest's referent.
        :return: The url as a string, or None if not found.
        """
        results = self.query_es()

        if results is None:
            return None

        if results.get('hits', {}).get('total', 0) == 0:
            # No results found for query, retry
            results = self.fallthrough_retry()
            if results is None or results.get('hits', {}).get('total', 0) == 0:
                # This time we've definitely failed
                return None

        if results.get('hits', {}).get('hits', [{}])[0].get('_type') == 'journal':

            # construct a journal object around the result
            journal = Journal(**results['hits']['hits'][0])

            # the continuation is a first-class journal object, so if we have a journal we have the right continuation
            # (assuming that the user gave us specific enough information
            ident = journal.id

            # If there request has a volume parameter, query for presence of an article with that volume
            if self.volume:
                vol_iss_results = self.query_for_vol(journal)

                if vol_iss_results == None:
                    # we were asked for a vol/issue, but weren't given the correct information to get it.
                    return None
                elif vol_iss_results['hits']['total'] > 0:
                    # construct the toc url using the ident, plus volume and issue
                    jtoc_url = url_for("doaj.toc", identifier=ident, volume=self.volume, issue=self.issue)
                else:
                    # If no results, the DOAJ does not contain the vol/issue being searched. (Show openurl 404)
                    jtoc_url = None
            else:
                # if no volume parameter, construct the toc url using the ident only
                jtoc_url = url_for("doaj.toc", identifier=ident)
            return jtoc_url

        elif results.get('hits', {}).get('hits',[{}])[0].get('_type') == 'article':
            return url_for("doaj.article_page", identifier=results['hits']['hits'][0]['_id'])

    def query_for_vol(self, journalobj):

        # The journal object will already be the correct continuation, if the user provided sufficient detail.
        issns = journalobj.bibjson().issns()

        # If there's no way to get the wanted issns, give up, else run the query
        if issns is None:
            return None
        else:
            volume_query = deepcopy(TERMS_SEARCH)
            volume_query["size"] = 0

            issn_term = {"terms": {"index.issn.exact": issns}}
            volume_query["query"]["bool"]["must"].append(issn_term)

            vol_term = {"term": {"bibjson.journal.volume.exact": self.volume}}
            volume_query["query"]["bool"]["must"].append(vol_term)

            # And if there's an issue, query that too. Note, issue does not make sense on its own.
            if self.issue:
                iss_term = {"term": {"bibjson.journal.number.exact": self.issue}}
                volume_query["query"]["bool"]["must"].append(iss_term)

            app.logger.debug("OpenURL subsequent volume query to article: " + json.dumps(volume_query))
            return Article.query(q=volume_query)

    def fallthrough_retry(self):
        """
        Some things to try differently if we get no results on first attempt
        :return: a new result set, or None
        """
        results = None

        # Search again for the title against alternative_title (may catch translations of titles)
        if self.jtitle and not self.stitle:
            self.stitle = self.jtitle
            self.jtitle = None
            results = self.query_es()

        return results

    def validate_issn(self, issn_str):
        """
        If the ISSN is missing a dash, add it so it matches that in the index.
        :param issn_str: The ISSN, or if None, this will skip.
        :return: The ISSN with the dash added
        """
        if issn_str:
            match_dash = re.compile('[-]')
            if not match_dash.search(issn_str):
                issn_str = issn_str[:4] + '-' + issn_str[4:]
        return issn_str

    @property
    def doi(self):
        """Digital Object Identifier"""
        return self._doi

    @doi.setter
    def doi(self, val):
        self._doi = val

    @property
    def aulast(self):
        """First author's family name, may be more than one word"""
        return self._aulast

    @aulast.setter
    def aulast(self, val):
        self._aulast = val

    @property
    def aufirst(self):
        """First author's given name or names or initials"""
        return self._aufirst

    @aufirst.setter
    def aufirst(self, val):
        self._aufirst = val

    @property
    def auinit(self):
        """First author's first and middle initials"""
        return self._auinit

    @auinit.setter
    def auinit(self, val):
        self._auinit = val

    @property
    def auinit1(self):
        """First author's first initial"""
        return self._auinit1

    @auinit1.setter
    def auinit1(self, val):
        self._auinit1 = val

    @property
    def auinitm(self):
        """First author's middle initial"""
        return self._auinitm

    @auinitm.setter
    def auinitm(self, val):
        self._auinitm = val

    @property
    def ausuffix(self):
        """First author's name suffix. e.g. 'Jr.', 'III'"""
        return self._ausuffix

    @ausuffix.setter
    def ausuffix(self, val):
        self._ausuffix = val

    @property
    def au(self):
        """full name of a single author"""
        return self._au

    @au.setter
    def au(self, val):
        self._au = val

    @property
    def aucorp(self):
        """Organisation or corporation that is the author or creator of the document"""
        return self._aucorp

    @aucorp.setter
    def aucorp(self, val):
        self._aucorp = val

    @property
    def atitle(self):
        """Article title"""
        return self._atitle

    @atitle.setter
    def atitle(self, val):
        self._atitle = val

    @property
    def jtitle(self):
        """Journal title"""
        return self._jtitle

    @jtitle.setter
    def jtitle(self, val):
        self._jtitle = val

    @property
    def stitle(self):
        """Abbreviated or short journal title"""
        return self._stitle

    @stitle.setter
    def stitle(self, val):
        self._stitle = val

    @property
    def date(self):
        """Date of publication"""
        return self._date

    @date.setter
    def date(self, val):
        if val:
            try:
                parsed_date = parse_date(val)
                val = parsed_date.year
            except ValueError:
                val = None
        self._date = val

    @property
    def chron(self):
        """Non-normalised enumeration / chronology, e.g. '1st quarter'"""
        return self._chron

    @chron.setter
    def chron(self, val):
        self._chron = val

    @property
    def ssn(self):
        """Season (chronology). spring|summer|fall|autumn|winter"""
        return self._ssn

    @ssn.setter
    def ssn(self, val):
        self._ssn = val

    @property
    def quarter(self):
        """Quarter (chronology). 1|2|3|4"""
        return self._quarter

    @quarter.setter
    def quarter(self, val):
        self._quarter = val

    @property
    def volume(self):
        """Volume designation. e.g. '124', or 'VI'"""
        return self._volume

    @volume.setter
    def volume(self, val):
        self._volume = val

    @property
    def part(self):
        """Subdivision of a volume or highest level division of the journal. e.g. 'B', 'Supplement'"""
        return self._part

    @part.setter
    def part(self, val):
        self._part = val

    @property
    def issue(self):
        """Journal issue"""
        return self._issue

    @issue.setter
    def issue(self, val):
        self._issue = val

    @property
    def spage(self):
        """Starting page"""
        return self._spage

    @spage.setter
    def spage(self, val):
        self._spage = val

    @property
    def epage(self):
        """Ending page"""
        return self._epage

    @epage.setter
    def epage(self, val):
        self._epage = val

    @property
    def pages(self):
        """Page range e.g. '53-58', 'C4-9'"""
        return self._pages

    @pages.setter
    def pages(self, val):
        self._pages = val

    @property
    def artnum(self):
        """Article number"""
        return self._artnum

    @artnum.setter
    def artnum(self, val):
        self._artnum = val

    @property
    def issn(self):
        """Journal ISSN"""
        return self._issn

    @issn.setter
    def issn(self, val):
        self._issn = self.validate_issn(val)

    @property
    def eissn(self):
        """ISSN for electronic version of the journal"""
        return self._eissn

    @eissn.setter
    def eissn(self, val):
        self._eissn = self.validate_issn(val)

    @property
    def isbn(self):
        """Journal ISBN"""
        return self._isbn

    @isbn.setter
    def isbn(self, val):
        self._isbn = val

    @property
    def coden(self):
        """CODEN"""
        return self._coden

    @coden.setter
    def coden(self, val):
        self._coden = val

    @property
    def sici(self):
        """Serial Item and Contribution Identifier (SICI)"""
        return self._sici

    @sici.setter
    def sici(self, val):
        self._sici = val

    @property
    def genre(self):
        """journal|issue|article|proceeding|conference|preprint|unknown"""
        return self._genre

    @genre.setter
    def genre(self, val):
        self._genre = val
