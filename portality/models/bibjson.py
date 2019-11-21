from portality.lib import dataobj
from portality.models import shared_structs

class GenericBibJSON(dataobj.DataObj):
    # vocab of known identifier types
    P_ISSN = "pissn"
    E_ISSN = "eissn"
    DOI = "doi"

    # allowable values for the url types
    HOMEPAGE = "homepage"
    WAIVER_POLICY = "waiver_policy"
    EDITORIAL_BOARD = "editorial_board"
    AIMS_SCOPE = "aims_scope"
    AUTHOR_INSTRUCTIONS = "author_instructions"
    OA_STATEMENT = "oa_statement"
    FULLTEXT = "fulltext"

    # constructor
    def __init__(self, bibjson=None, **kwargs):
        self._add_struct(shared_structs.SHARED_BIBJSON.get("structs", {}).get("bibjson"))
        # construct_maintain_reference is enforced here, don't allow override with kwargs
        kwargs.pop('construct_maintain_reference', None)
        super(GenericBibJSON, self).__init__(raw=bibjson, construct_maintain_reference=True, **kwargs)

    ####################################################
    # shared simple property getter and setters

    @property
    def title(self):
        return self._get_single("title")

    @title.setter
    def title(self, val):
        self._set_with_struct("title", val)

    #####################################################
    # complex getters and setters


    ## work with the identifiers

    def add_identifier(self, idtype, value):
        all = self.get_identifiers()
        existing = [x for x in all if x["type"] == idtype]
        if existing:
            for x in existing:
                all.remove(x)
        idobj = {"type" : idtype, "id" : self._normalise_identifier(idtype, value)}
        self._add_to_list_with_struct("identifier", idobj)

    def get_identifiers(self, idtype=None):
        if idtype is None:
            return self._get_list("identifier")

        ids = []
        for identifier in self._get_list("identifier"):
            if identifier.get("type") == idtype and identifier.get("id") not in ids:
                ids.append(identifier.get("id"))
        return ids

    def get_one_identifier(self, idtype=None):
        results = self.get_identifiers(idtype=idtype)
        if len(results) > 0:
            return results[0]
        else:
            return None

    def remove_identifiers(self, idtype=None, id=None):
        # if we are to remove all identifiers, this is easy
        if idtype is None and id is None:
            self._delete("identifier")
            return

        match = {}
        if idtype is not None:
            match["type"] = idtype
        if id is not None:
            match["id"] = id
        self._delete_from_list("identifier", matchsub=match)

    def _normalise_identifier(self, idtype, value):
        if idtype in [self.P_ISSN, self.E_ISSN]:
            return self._normalise_issn(value)
        return value

    def _normalise_issn(self, issn):
        issn = issn.upper()
        if len(issn) > 8: return issn
        if len(issn) == 8:
            if "-" in issn: return "0" + issn
            else: return issn[:4] + "-" + issn[4:]
        if len(issn) < 8:
            if "-" in issn: return ("0" * (9 - len(issn))) + issn
            else:
                issn = ("0" * (8 - len(issn))) + issn
                return issn[:4] + "-" + issn[4:]

    ## work with keywords

    @property
    def keywords(self):
        return self._get_list("keywords")

    def add_keyword(self, keyword):
        if keyword is not None:
            self._add_to_list_with_struct("keywords", keyword.lower())

    def set_keywords(self, keywords):
        if type(keywords) is list:
            keywords = [w.lower() for w in keywords]
            self._set_with_struct("keywords", keywords)
        else:
            if keywords is not None:
                self._set_with_struct("keywords", keywords.lower())

    ## work with urls

    def add_url(self, url, urltype=None, content_type=None):
        if url is None:
            # do not add empty URL-s
            return

        urlobj = {"url" : url}
        if urltype is not None:
            urlobj["type"] = urltype
        if content_type is not None:
            urlobj["content_type"] = content_type

        self._add_to_list_with_struct("link", urlobj)

    def get_urls(self, urltype=None, unpack_urlobj=True):
        if urltype is None:
            return self._get_list("link")

        urls = []
        for link in self._get_list("link"):
            if link.get("type") == urltype:
                if unpack_urlobj:
                    urls.append(link.get("url"))
                else:
                    urls.append(link)
        return urls

    def get_single_url(self, urltype, unpack_urlobj=True):
        urls = self.get_urls(urltype=urltype, unpack_urlobj=unpack_urlobj)
        if len(urls) > 0:
            return urls[0]
        return None

    def remove_urls(self, urltype=None, url=None):
        # if we are to remove all urls, this is easy
        if urltype is None and url is None:
            self._delete("link")
            return

        match = {}
        if urltype is not None:
            match["type"] = urltype
        if url is not None:
            match["url"] = id
        self._delete_from_list("link", matchsub=match)

    ## work with subjects

    def add_subject(self, scheme, term, code=None):
        sobj = {"scheme" : scheme, "term" : term}
        if code is not None:
            sobj["code"] = code
        self._add_to_list_with_struct("subject", sobj)

    def subjects(self):
        return self._get_list("subject")

    def set_subjects(self, subjects):
        self._set_with_struct("subject", subjects)

    def remove_subjects(self):
        self._delete("subject")

    def lcc_paths(self):
        classification_paths = []

        # calculate the classification paths
        from portality.lcc import lcc # inline import since this hits the database
        for subs in self.subjects():
            scheme = subs.get("scheme")
            term = subs.get("term")
            if scheme == "LCC":
                p = lcc.pathify(term)
                if p is not None:
                    classification_paths.append(p)

        # normalise the classification paths, so we only store the longest ones
        classification_paths = lcc.longest(classification_paths)

        return classification_paths

    def issns(self):
        issns = []
        issns += self.get_identifiers(self.P_ISSN)
        issns += self.get_identifiers(self.E_ISSN)
        return issns

    @property
    def first_pissn(self):
        return self.get_identifiers(self.P_ISSN)[0]

    @property
    def first_eissn(self):
        return self.get_identifiers(self.E_ISSN)[0]
