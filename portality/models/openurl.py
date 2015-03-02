
JOURNAL_SCHEMA_KEYS = ['doi', 'aulast', 'aufirst', 'auinit', 'auinit1', 'auinitm', 'ausuffix', 'au', 'aucorp', 'atitle',
                       'jtitle', 'stitle', 'date', 'chron', 'ssn', 'quarter', 'volume', 'part', 'issue', 'spage',
                       'epage', 'pages', 'artnum', 'issn', 'eissn', 'isbn', 'coden', 'sici', 'genre']

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
        self._issn = val

    @property
    def eissn(self):
        """ISSN for electronic version of the journal"""
        return self._eissn

    @eissn.setter
    def eissn(self, val):
        self._eissn = val

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
