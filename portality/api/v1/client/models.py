from portality.api.v1.data_objects.journal import OutgoingJournal
from portality.api.v1.data_objects.article import IncomingArticleDO


class Journal(OutgoingJournal):

    def all_issns(self):
        issns = []

        # get the issns from the identifiers record
        idents = self.bibjson.identifier
        if idents is not None:
            for ident in idents:
                if ident.type in ["pissn", "eissn"]:
                    issns.append(ident.id)

        return issns


class Article(IncomingArticleDO):

    def add_identifier(self, type, id):
        if type is None or id is None:
            return
        self._add_to_list("bibjson.identifier", {"type" : type, "id" : id})

    def get_identifier(self, type):
        for id in self._get_list("bibjson.identifier"):
            if id.get("type") == type:
                return id.get("id")
        return None

    def add_link(self, type, url):
        if type is None or url is None:
            return
        self._add_to_list("bibjson.link", {"type" : type, "url" : url})

    def get_link(self, type):
        for link in self._get_list("bibjson.link"):
            if link.get("type") == type:
                return link.get("url")
        return None

    def add_author(self, name):
        if name is None:
            return
        self._add_to_list("bibjson.author", {"name" : name})

    def is_api_valid(self):
        self.check_construct()
        self.custom_validate()
