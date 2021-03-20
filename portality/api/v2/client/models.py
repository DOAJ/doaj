from portality.api.v2.data_objects.journal import OutgoingJournal
from portality.api.v2.data_objects.article import IncomingArticleDO


class Journal(OutgoingJournal):

    def all_issns(self):
        issns = []
        for _ident in ('pissn', 'eissn'):
            if self.data.get('bibjson', {}).get(_ident) is not None:
                issns.append(self.data['bibjson'][_ident])
        return issns


class Article(IncomingArticleDO):

    def add_identifier(self, _type, _id):
        if _type is None or _id is None:
            return
        self._add_to_list("bibjson.identifier", {"type": _type, "id": _id})

    def get_identifier(self, _type):
        for _id in self._get_list("bibjson.identifier"):
            if _id.get("type") == _type:
                return _id.get("id")
        return None

    def add_link(self, _type, url):
        if type is None or url is None:
            return
        self._add_to_list("bibjson.link", {"type": _type, "url": url})

    def get_link(self, _type):
        for link in self._get_list("bibjson.link"):
            if link.get("type") == _type:
                return link.get("url")
        return None

    def add_author(self, name):
        if name is None:
            return
        self._add_to_list("bibjson.author", {"name": name})

    def is_api_valid(self):
        self.check_construct()
        self.custom_validate()
