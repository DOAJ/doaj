class GenericBibJSONOld(object):
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
    def __init__(self, bibjson=None):
        self.bibjson = bibjson if bibjson is not None else {}

    # generic property getter and setter for ad-hoc extensions
    def get_property(self, prop):
        return self.bibjson.get(prop)

    def set_property(self, prop, value):
        self.bibjson[prop] = value

    # shared simple property getter and setters

    @property
    def title(self): return self.bibjson.get("title")
    @title.setter
    def title(self, val) : self.bibjson["title"] = val

    # complex getters and setters

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

    def add_identifier(self, idtype, value):
        if "identifier" not in self.bibjson:
            self.bibjson["identifier"] = []
        idobj = {"type" : idtype, "id" : self._normalise_identifier(idtype, value)}
        self.bibjson["identifier"].append(idobj)

    def get_identifiers(self, idtype=None):
        if idtype is None:
            return self.bibjson.get("identifier", [])

        ids = []
        for identifier in self.bibjson.get("identifier", []):
            if identifier.get("type") == idtype and identifier.get("id") not in ids:
                ids.append(identifier.get("id"))
        return ids

    def get_one_identifier(self, idtype=None):
        results = self.get_identifiers(idtype=idtype)
        if results:
            return results[0]
        else:
            return None

    def update_identifier(self, idtype, new_value):
        if not new_value:
            self.remove_identifiers(idtype=idtype)
            return

        if 'identifier' not in self.bibjson:
            return

        if not self.get_one_identifier(idtype):
            self.add_identifier(idtype, new_value)
            return

        # so an old identifier does actually exist, and we actually want
        # to update it
        for id_ in self.bibjson['identifier']:
            if id_['type'] == idtype:
                id_['id'] = new_value

    def remove_identifiers(self, idtype=None, id=None):
        # if we are to remove all identifiers, this is easy
        if idtype is None and id is None:
            self.bibjson["identifier"] = []
            return

        # else, find all the identifiers positions that we need to remove
        idx = 0
        remove = []
        for identifier in self.bibjson.get("identifier", []):
            if idtype is not None and id is None:
                if identifier.get("type") == idtype:
                    remove.append(idx)
            elif idtype is None and id is not None:
                if identifier.get("id") == id:
                    remove.append(idx)
            else:
                if identifier.get("type") == idtype and identifier.get("id") == id:
                    remove.append(idx)
            idx += 1

        # sort the positions of the ids to remove, largest first
        remove.sort(reverse=True)

        # now remove them one by one (having the largest first means the lower indices
        # are not affected
        for i in remove:
            del self.bibjson["identifier"][i]

    @property
    def keywords(self):
        return self.bibjson.get("keywords", [])

    def add_keyword(self, keyword):
        if "keywords" not in self.bibjson:
            self.bibjson["keywords"] = []
        self.bibjson["keywords"].append(keyword)

    def set_keywords(self, keywords):
        self.bibjson["keywords"] = keywords

    def add_url(self, url, urltype=None, content_type=None):
        if not url:
            # do not add empty URL-s
            return

        if "link" not in self.bibjson:
            self.bibjson["link"] = []
        urlobj = {"url" : url}
        if urltype is not None:
            urlobj["type"] = urltype
        if content_type is not None:
            urlobj["content_type"] = content_type
        self.bibjson["link"].append(urlobj)

    def get_urls(self, urltype=None, unpack_urlobj=True):
        if urltype is None:
            return self.bibjson.get("link", [])

        urls = []
        for link in self.bibjson.get("link", []):
            if link.get("type") == urltype:
                if unpack_urlobj:
                    urls.append(link.get("url"))
                else:
                    urls.append(link)
        return urls

    def get_single_url(self, urltype, unpack_urlobj=True):
        urls = self.get_urls(urltype=urltype, unpack_urlobj=unpack_urlobj)
        if urls:
            return urls[0]
        return None

    def update_url(self, url, urltype=None):
        if "link" not in self.bibjson:
            self.bibjson['link'] = []

        urls = self.bibjson['link']

        if urls:
            for u in urls: # do not reuse "url" as it's a parameter!
                if u['type'] == urltype:
                    u['url'] = url
        else:
            self.add_url(url, urltype)

    def add_subject(self, scheme, term, code=None):
        if "subject" not in self.bibjson:
            self.bibjson["subject"] = []
        sobj = {"scheme" : scheme, "term" : term}
        if code is not None:
            sobj["code"] = code

        # append if the subject isn't already present
        if sobj not in self.bibjson["subject"]:
            self.bibjson["subject"].append(sobj)

    def subjects(self):
        return self.bibjson.get("subject", [])

    def set_subjects(self, subjects):
        self.bibjson["subject"] = subjects

    def remove_subjects(self):
        if "subject" in self.bibjson:
            del self.bibjson["subject"]

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
    def __init__(self, bibjson=None):
        self._add_struct(shared_structs.SHARED_BIBJSON.get("structs", {}).get("bibjson"))
        super(GenericBibJSON, self).__init__(raw=bibjson, construct_maintain_reference=True)

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
        self._add_to_list_with_struct("keywords", keyword)

    def set_keywords(self, keywords):
        self._set_with_struct("keywords", keywords)

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
