from portality.lib import dataobj
from portality import models
from portality.util import normalise_issn
from portality.formcontext import choices
from copy import deepcopy


class ArticleDO(dataobj.DataObj):
    def __init__(self, raw=None):
        struct = {
            "fields": {
                "id": {"coerce": "unicode"},                # Note that we'll leave these in for ease of use by the
                "created_date": {"coerce": "utcdatetime"},  # caller, but we'll need to ignore them on the conversion
                "last_updated": {"coerce": "utcdatetime"}   # to the real object
            },
            "objects": ["admin", "bibjson"],
            "required": ["bibjson"],

            "structs": {

                "admin": {
                    "fields": {
                        "in_doaj": {"coerce": "bool", "get__default": False},
                        "publisher_record_id": {"coerce": "unicode"}
                    }
                },

                "bibjson": {
                    "fields": {
                        "title": {"coerce": "unicode"},
                        "year": {"coerce": "unicode"},
                        "month": {"coerce": "unicode"},
                        "start_page": {"coerce": "unicode"},
                        "end_page": {"coerce": "unicode"},
                        "abstract": {"coerce": "unicode"}
                    },
                    "lists": {
                        "identifier": {"contains": "object"},
                        "link": {"contains": "object"},
                        "author": {"contains": "object"},
                        "keywords": {"coerce": "unicode", "contains": "field"},
                        "subject": {"contains": "object"}
                    },
                    "objects": [
                        "journal",
                    ],
                    "required": [
                        "title",
                        "author",
                        "identifier"                # One type of identifier is required
                    ],
                    "structs": {

                        "identifier": {
                            "fields": {
                                "type": {"coerce": "unicode"},
                                "id": {"coerce": "unicode"}
                            },
                            "required": ["type", "id"]
                        },

                        "link": {
                            "fields": {
                                "type": {"coerce": "unicode"},
                                "url": {"coerce": "url"}
                            },
                            "required": ["type", "url"]
                        },

                        "author": {
                            "fields": {
                                "name": {"coerce": "unicode"},
                                "email": {"coerce": "unicode"},
                                "affiliation": {"coerce": "unicode"}
                            },
                            "required": ["name"]
                        },

                        "subject": {
                            "fields": {
                                "scheme": {"coerce": "unicode"},
                                "term": {"coerce": "unicode"},
                                "code": {"coerce": "unicode"}
                            }
                        },

                        "journal": {
                            "fields": {
                                "volume": {"coerce": "unicode"},
                                "number": {"coerce": "unicode"},
                                "publisher": {"coerce": "unicode"},
                                "title": {"coerce": "unicode"},
                                "language": {"coerce": "unicode"},
                                "country": {"coerce": "unicode"}
                            },
                            "lists": {
                                "license": {"contains": "object"}
                            },
                            "structs": {

                                "license": {
                                    "fields": {
                                        "title": {"coerce": "license"},
                                        "type": {"coerce": "license"},
                                        "url": {"coerce": "unicode"},
                                        "version": {"coerce": "unicode"},
                                        "open_access": {"coerce": "bool"},
                                    },
                                    "required": [
                                        "title",
                                        "type",
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }

        mycoerce = deepcopy(self.DEFAULT_COERCE)
        mycoerce["license"] = dataobj.string_canonicalise(["CC BY", "CC BY-NC", "CC BY-NC-ND", "CC BY-NC-SA", "CC BY-ND", "CC BY-SA", "Not CC-like"], allow_fail=True)
        super(ArticleDO, self).__init__(raw, struct=struct, construct_silent_prune=True, expose_data=True, coerce_map=mycoerce)

    def custom_validate(self):
        # only attempt to validate if this is not a blank object
        if len(self.data.keys()) == 0:
            return

        # at least one of print issn / e-issn, and they must be different
        #
        # check that there are identifiers at all
        identifiers = self.bibjson.identifier
        if identifiers is None or len(identifiers) == 0:
            raise dataobj.DataStructureException("You must specify at least one of P-ISSN or E-ISSN in bibjson.identifier")

        # extract the p/e-issn identifier objects
        pissn = None
        eissn = None
        for ident in identifiers:
            if ident.type == "pissn":
                pissn = ident
            elif ident.type == "eissn":
                eissn = ident

        # check that at least one of them appears
        if pissn is None and eissn is None:
            raise dataobj.DataStructureException("You must specify at least one of P-ISSN or E-ISSN in bibjson.identifier")

        # normalise the ids
        pissn.id = normalise_issn(pissn.id)
        eissn.id = normalise_issn(eissn.id)

        # check they are not the same
        if pissn.id == eissn.id:
            raise dataobj.DataStructureException("P-ISSN and E-ISSN should be different")

    def to_article_model(self):
        dat = deepcopy(self.data)
        return models.Article(**dat)

    @classmethod
    def from_model(cls, am):
        assert isinstance(am, models.Article)
        return cls(am.data)

    @classmethod
    def from_model_by_id(cls, id_):
        a = models.Article.pull(id_)
        return cls.from_model(a)
