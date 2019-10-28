from portality.lib import dataobj
from portality.api.v1.data_objects.journal import OutgoingJournal
from portality.api.v1.data_objects.article import IncomingArticleDO

"""
BASE_ARTICLE_STRUCT = {
    "fields": {
        "id": {"coerce": "unicode"},                # Note that we'll leave these in for ease of use by the
        "created_date": {"coerce": "utcdatetime"},  # caller, but we'll need to ignore them on the conversion
        "last_updated": {"coerce": "utcdatetime"}   # to the real object
    },
    "objects": ["admin", "bibjson"],

    "structs": {

        "admin": {
            "fields": {
                "in_doaj": {"coerce": "bool", "get__default": False},
                "publisher_record_id": {"coerce": "unicode"},
                "upload_id": {"coerce": "unicode"}
            }
        },

        "bibjson": {
            "fields": {
                "title": {"coerce": "unicode", "set__ignore_none": True},
                "year": {"coerce": "unicode", "set__ignore_none": True},
                "month": {"coerce": "unicode", "set__ignore_none": True},
                "abstract": {"coerce": "unicode", "set__ignore_none": True}
            },
            "lists": {
                "identifier": {"contains": "object"},
                "link": {"contains": "object"},
                "author": {"contains": "object"},
                "keywords": {"coerce": "unicode", "contains": "field"},
                "subject": {"contains": "object"},
            },
            "objects": [
                "journal",
            ],
            "structs": {

                "identifier": {
                    "fields": {
                        "type": {"coerce": "unicode"},
                        "id": {"coerce": "unicode"}
                    }
                },

                "link": {
                    "fields": {
                        "type": {"coerce": "unicode"},
                        "url": {"coerce": "url"},
                        "content_type": {"coerce": "unicde"}
                    }
                },

                "author": {
                    "fields": {
                        "name": {"coerce": "unicode"},
                        "email": {"coerce": "unicode"},
                        "affiliation": {"coerce": "unicode"}
                    }
                },

                "journal": {
                    "fields": {
                        "start_page": {"coerce": "unicode", "set__ignore_none": True},
                        "end_page": {"coerce": "unicode", "set__ignore_none": True},
                        "volume": {"coerce": "unicode", "set__ignore_none": True},
                        "number": {"coerce": "unicode", "set__ignore_none": True},
                        "publisher": {"coerce": "unicode", "set__ignore_none": True},
                        "title": {"coerce": "unicode", "set__ignore_none": True},
                        "country": {"coerce": "unicode", "set__ignore_none": True}
                    },
                    "lists": {
                        "license": {"contains": "object"},
                        "language": {"coerce": "unicode", "contains": "field", "set__ignore_none": True}
                    },
                    "structs": {

                        "license": {
                            "fields": {
                                "title": {"coerce": "unicode"},
                                "type": {"coerce": "unicode"},
                                "url": {"coerce": "unicode"},
                                "version": {"coerce": "unicode"},
                                "open_access": {"coerce": "bool"},
                            }
                        }
                    }
                },

                "subject": {
                    "fields": {
                        "scheme": {"coerce": "unicode"},
                        "term": {"coerce": "unicode"},
                        "code": {"coerce": "unicode"}
                    }
                },
            }
        }
    }
}

ARTICLE_REQUIRED = {
    "required": ["bibjson"],

    "structs": {
        "bibjson": {
            "required": [
                "title",
                "identifier"                # One type of identifier is required
            ],
            "structs": {

                "identifier": {
                    "required": ["type", "id"]
                },

                "link": {
                    "required": ["type", "url"]
                }
            }
        }
    }
}
"""

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



"""
class ArticleValidator(dataobj.DataObj):
    def __init__(self, raw=None):
        self._add_struct(BASE_ARTICLE_STRUCT)
        self._add_struct(ARTICLE_REQUIRED)
        super(ArticleValidator, self).__init__(raw, expose_data=True)
"""