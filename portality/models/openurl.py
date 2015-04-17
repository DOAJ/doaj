import re
from flask import url_for
from portality.models import Journal, Article
from portality.core import app
from copy import deepcopy

JOURNAL_SCHEMA_KEYS = ['doi', 'aulast', 'aufirst', 'auinit', 'auinit1', 'auinitm', 'ausuffix', 'au', 'aucorp', 'atitle',
                       'jtitle', 'stitle', 'date', 'chron', 'ssn', 'quarter', 'volume', 'part', 'issue', 'spage',
                       'epage', 'pages', 'artnum', 'issn', 'eissn', 'isbn', 'coden', 'sici', 'genre']

# The genres from the OpenURL schema we support
SUPPORTED_GENRES = ['journal', 'article']

# Mapping from OpenURL schema to both supported models (Journal, Article)
OPENURL_TO_ES = {
    'au' : (None, 'author.name.exact'),
    'aucorp' : (None, 'author.affiliation.exact'),
    'atitle' : (None, 'bibjson.title.exact'),
    'jtitle' : ('index.title.exact', 'bibjson.journal.title.exact'),    # Note we use index.title.exact for journals, to support continuations
    'stitle' : ('bibjson.alternative_title.exact', None),
    'date' : (None, 'index.date'),
    'volume' : (None, 'bibjson.journal.volume'),
    'issue' : (None, 'bibjson.journal.number'),
    'spage' : (None, 'bibjson.start_page'),
    'epage' : (None, 'bibjson.end_page'),
    'issn' : ('index.issn.exact', 'index.issn.exact'), # bibjson.identifier.id.exact
    'eissn' : ('index.issn.exact', 'index.issn.exact'),
    'isbn' : ('index.issn.exact', 'index.issn.exact'),
}

TERMS_SEARCH = { "query" : {"bool" : { "must" : [] } } }

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
            for key, value in kwargs.iteritems():
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

        # FIXME: you can query a journal by volume and issue (which makes sense) but
        # these values are not used to query the index, so you can get a positive match
        # for a volume and issue that aren't held by DOAJ.  Since these input values
        # are then used to point the user to the right endpoint in the journal, this can result
        # in unexpected errors/behaviour down the line

        # Add the attributes to the query
        for (k, v) in set_attributes:
            es_term = OPENURL_TO_ES[k][i]
            if es_term == None:
                continue
            else:
                term = { "term" : { es_term : v} }
            populated_query["query"]["bool"]["must"].append(term)

        # avoid doing an empty query
        if len(populated_query["query"]["bool"]["must"]) == 0:
            app.logger.debug("No valid search terms in OpenURL object")
            return None
        app.logger.debug("Query from OpenURL: " + str(populated_query))

        # Return the results of the query
        if i == 0:
            return Journal.query(q=populated_query)
        elif i == 1:
            return Article.query(q=populated_query)

    def get_result_url(self):
        """
        Get the URL for this OpenURLRequest's referent.
        :return: The url as a string, or None if not found.
        """
        results = self.query_es()

        if results is None:
            return None

        if results.get('hits', {}).get('total', 0) > 0:
            if results.get('hits', {}).get('hits',[{}])[0].get('_type') == 'journal':

                # construct a journal object around the result
                journal = Journal(**results['hits']['hits'][0])

                # since we might be looking for a specific continuation of a journal, do a bit of work
                # to point the user to the correct ToC, which should be by ISSN if possible.  If they have
                # given us the journal title, then we should try to identify the ISSN associated with it
                # Failing all that, just fall back to the current version ToC
                ident = self.issn
                if ident is None:
                    if self.jtitle is not None:
                        issns = journal.issns_for_title(self.jtitle)
                        if len(issns) > 0:
                            ident = issns[0]
                    if ident is None:
                        ident = journal.id

                # FIXME: the volume and issue are not queried on or validated, so we don't know
                # for sure at this point whether the user will hit a valid ToC
                # construct the toc url using the ident, plus volume and issue if they are available
                jtoc_url = url_for("doaj.toc", identifier=ident, volume=self.volume, issue=self.issue if self.volume else None)

                return jtoc_url

            elif results.get('hits', {}).get('hits',[{}])[0].get('_type') == 'article':
                return url_for("doaj.article_page", identifier=results['hits']['hits'][0]['_id'])
        else:
            # No results found for query
            return None

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
