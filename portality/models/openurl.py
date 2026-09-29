import re, json
from flask import url_for
from portality.models import Journal, Article
from portality.core import app
from copy import deepcopy
from portality.lib import dates

JOURNAL_SCHEMA_KEYS = ['doi', 'aulast', 'aufirst', 'auinit', 'auinit1', 'auinitm', 'ausuffix', 'au', 'aucorp', 'atitle',
                       'jtitle', 'stitle', 'date', 'chron', 'ssn', 'quarter', 'volume', 'part', 'issue', 'spage',
                       'epage', 'pages', 'artnum', 'issn', 'eissn', 'isbn', 'coden', 'sici', 'genre']

# The genres from the OpenURL schema we support
SUPPORTED_GENRES = ['journal', 'article']

# Mapping from OpenURL schema to both supported models (Journal, Article)
OPENURL_TO_ES = {
    'aulast': (None, 'bibjson.author.name.exact'),
    'aucorp': (None, 'bibjson.author.affiliation.exact'),
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
    'isbn': ('index.issn.exact', 'index.issn.exact'),
    'doi': (None, 'index.doi.exact')
}

# Terms search template. Ensure all queries from OpenURL return publicly visible results with in_doaj : true
IN_DOAJ_TERM = {"term": {"admin.in_doaj": True}}
TERMS_SEARCH = {"query": {"bool": {"must": [IN_DOAJ_TERM]}}}


def reformat_au_as_aulast(au_value):
    """
    Best-effort reformat of an OpenURL ``au`` (free-text full author name) into the
    "Given Surname" order DOAJ's own indexing uses (see
    ``portality.crosswalks.article_crossref_xml.extract_authors``), so it can be
    searched via the same ES field as ``aulast``.

    Real-world requests we've seen in production use ``au`` non-standardly to hold
    *multiple* authors in one value, semicolon-separated, each usually in
    "Surname, Given" order (e.g. ``"Barich, Howard;Kotler, Philip"``) - the
    opposite order to how we index names. Only the first author is used if
    several are supplied: exact-match search on a full name is already fragile
    (a missing middle initial, a diacritic, or different formatting from the
    source citation will still silently fail to match), and OR-ing several
    full-name guesses together would only make that harder to reason about, not
    more accurate.

    :param au_value: the raw au string, e.g. "Barich, Howard;Kotler, Philip"
    :return: a best-effort "Given Surname" string, e.g. "Howard Barich", or the
        first author's value unchanged if it doesn't look like "Surname, Given"
        (no comma present)
    """
    first_author = au_value.split(";")[0].strip()
    if "," in first_author:
        surname, given = first_author.split(",", 1)
        return (given.strip() + " " + surname.strip()).strip()
    return first_author


class UnsupportedOpenURLQuery(Exception):
    """
    Raised when an OpenURL request cannot be turned into a usable search query -
    e.g. every field supplied is one the OpenURL schema allows but that DOAJ does
    not support searching on (such as ``rft.chron``), or the genre supplied isn't
    one DOAJ recognises. Callers (the view) should treat this as a bad request
    (400), as distinct from a well-formed query that simply found no results.
    """
    pass


class OpenURLRequest(object):
    """
    Based on the fields from ofi/fmt:kev:mtx:journal schema for Journals in OpenURL 1.0
    This is the only schema the DOAJ supports.
    """

    # ~~API:Feature~~

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

        Fields the OpenURL schema allows but that DOAJ has no ES mapping for
        (e.g. ``au``, ``chron``, ``ssn`` ...), and a genre DOAJ doesn't recognise,
        are logged and skipped rather than raising - unless skipping them leaves
        no usable search term at all, in which case :class:`UnsupportedOpenURLQuery`
        is raised so the caller can respond with a 400 rather than treating it as
        a legitimate (if empty) search.

        :return: The results of a query through the dao, a JSON object, or None
            if no attributes were supplied on the request at all.
        :raises UnsupportedOpenURLQuery: if the request had content, but none of
            it could be mapped onto a search DOAJ supports.
        """
        # Copy to the template, which will be populated with terms
        populated_query = deepcopy(TERMS_SEARCH)

        # Get all of the attributes with values set. Guard against a schema key that
        # somehow doesn't have a matching property (shouldn't happen given __init__,
        # but defends against future schema drift rather than crashing on it).
        set_attributes = []
        for x in JOURNAL_SCHEMA_KEYS[:-1]:
            try:
                val = getattr(self, x)
            except AttributeError as e:
                app.logger.warning("OpenURL schema key '{x}' has no matching property, skipping: {e}".format(x=x, e=e))
                continue
            if val:
                set_attributes.append((x, val))

        # If we don't have a genre, guess journal FIXME: is it correct to assume journal?
        if not self.genre:
            self.genre = SUPPORTED_GENRES[0]    # TODO: we may want to handle 404 instead

        # Set i to use either our mapping for journals or articles. An unrecognised
        # genre means we can't tell which half of OPENURL_TO_ES to use at all, so
        # none of the supplied fields (even otherwise-valid ones) can be mapped.
        unsupported_fields = []
        try:
            i = SUPPORTED_GENRES.index(str(self.genre).lower())
        except (ValueError, AttributeError) as e:
            app.logger.warning("OpenURL request supplied an unsupported genre '{x}': {e}".format(x=self.genre, e=e))
            unsupported_fields.append(("genre", self.genre))
            i = None

        # Add the attributes to the query, skipping (and logging) any field that
        # the OpenURL schema allows but DOAJ can't map to a search term, instead
        # of letting one bad field crash the whole request.
        # NOTE: populated_query's "must" list always starts with IN_DOAJ_TERM, so
        # we can't tell "no real search terms added" just from its length - track
        # that separately.
        terms_added = 0
        if i is not None:
            # so 'au' can defer to an explicit 'aulast' if both are given, rather
            # than adding two, possibly conflicting, author terms
            attr_keys = {x for (x, _) in set_attributes}

            for (k, v) in set_attributes:
                lookup_key, term_value = k, v

                # 'au' (free-text full author name) isn't in OPENURL_TO_ES - DOAJ
                # only supports author search via 'aulast' (surname). Real-world
                # requests use 'au' far more often than 'aulast', so rather than
                # just dropping it, make a best-effort translation onto the same
                # search 'aulast' already uses (see reformat_au_as_aulast).
                if k == "au":
                    if "aulast" in attr_keys:
                        app.logger.debug("OpenURL 'au' field ignored in favour of explicit 'aulast'")
                        continue
                    lookup_key = "aulast"
                    term_value = reformat_au_as_aulast(v)

                try:
                    es_term = OPENURL_TO_ES[lookup_key][i]
                except (KeyError, IndexError, TypeError) as e:
                    app.logger.warning("OpenURL field '{x}' is not supported by DOAJ, skipping: {e}".format(x=k, e=e))
                    unsupported_fields.append((k, v))
                    continue

                if es_term is None:
                    continue

                term = {"term": {es_term: term_value}}
                populated_query["query"]["bool"]["must"].append(term)
                terms_added += 1

        # avoid doing an empty (unconstrained beyond in_doaj) query
        if terms_added == 0:
            if unsupported_fields:
                # the request had content, but none of it could be turned into a
                # usable search - this is a bad request, not just "no results"
                msg = "OpenURL request contained no fields DOAJ can search on (unsupported: {x})".format(
                    x=", ".join(f for f, _ in unsupported_fields))
                app.logger.warning(msg)
                raise UnsupportedOpenURLQuery(msg)

            app.logger.debug("No valid search terms in OpenURL object")
            return None

        try:
            query_json = json.dumps(populated_query)
        except TypeError as e:
            query_json = "<unable to serialise query for logging: {e}>".format(e=e)

        # Return the results of the query
        if i == 0:
            app.logger.debug("OpenURL query to journal: " + query_json)
            return Journal.query(q=populated_query)
        elif i == 1:
            app.logger.debug("OpenURL query to article: " + query_json)
            return Article.query(q=populated_query)

    def get_result_url(self):
        """
        Get the URL for this OpenURLRequest's referent.
        :return: The url as a string, or None if not found.
        :raises UnsupportedOpenURLQuery: propagated from query_es() - the caller
            (the view) should turn this into a 400 response.
        """
        results = self.query_es()

        if results is None:
            return None

        if results.get('hits', {}).get('total', {}).get('value', 0) == 0:
            # No results found for query, retry
            results = self.fallthrough_retry()
            if results is None or results.get('hits', {}).get('total', {}).get('value', 0) == 0:
                # This time we've definitely failed
                return None

        if results.get('hits', {}).get('hits', [{}])[0].get('_source', {}).get('es_type') == 'journal':

            # construct a journal object around the result
            journal = Journal(**results['hits']['hits'][0])

            # the continuation is a first-class journal object, so if we have a journal we have the right continuation
            # (assuming that the user gave us specific enough information
            ident = journal.id

            # construct the toc url using the ident only
            jtoc_url = url_for("doaj.toc", identifier=ident)
            return jtoc_url

        #~~->Article:Page~~
        elif results.get('hits', {}).get('hits', [{}])[0].get('_source', {}).get('es_type') == 'article':
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

            try:
                query_json = json.dumps(volume_query)
            except TypeError as e:
                query_json = "<unable to serialise query for logging: {e}>".format(e=e)
            app.logger.debug("OpenURL subsequent volume query to article: " + query_json)
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
                parsed_date = dates.parse(val)
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
