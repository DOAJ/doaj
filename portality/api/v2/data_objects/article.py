import re

from portality.lib import dataobj, swagger
from portality import models, regex
from portality.util import normalise_issn
from copy import deepcopy

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
                "seal": {"coerce": "bool", "get__default": False},
                "publisher_record_id": {"coerce": "unicode"},
                "upload_id": {"coerce": "unicode"}
            }
        },

        "bibjson": {
            "fields": {
                "title": {"coerce": "unicode"},
                "year": {"coerce": "unicode"},
                "month": {"coerce": "unicode"},
                "abstract": {"coerce": "unicode"}
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
                "author": {
                    "fields": {
                        "name": {"coerce": "unicode"},
                        "affiliation": {"coerce": "unicode"},
                        "orcid_id": {"coerce": "unicode"}
                    }
                },
                "journal": {
                    "fields": {
                        "start_page": {"coerce": "unicode"},
                        "end_page": {"coerce": "unicode"},
                        "volume": {"coerce": "unicode"},
                        "number": {"coerce": "unicode"},
                        "publisher": {"coerce": "unicode"},
                        "title": {"coerce": "unicode"},
                        "country": {"coerce": "unicode"}
                    },
                    "lists": {
                        "license": {"contains": "object"},
                        "language": {"coerce": "unicode", "contains": "field"}
                    },
                    "structs": {

                        "license": {
                            "fields": {
                                "title": {"coerce": "license"},
                                "type": {"coerce": "license"},
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

INCOMING_ARTICLE_REQUIRED = {
    "required": ["bibjson"],

    "structs": {
        "bibjson": {
            "required": [
                "title",
                # "author",                   # author no longer required
                "identifier"                # One type of identifier is required
            ],
            "structs": {

                "identifier": {
                    "required": ["type", "id"]
                },

                "link": {
                    "required": ["type", "url"],
                    "fields": {
                        "type": {"coerce": "link_type"},
                        "url": {"coerce": "url"},
                        "content_type": {"coerce": "link_content_type"}
                    }
                },

                "author": {
                    "required": ["name"]
                }
            }
        }
    }
}

OUTGOING_ARTICLE_PATCH = {
    "structs": {
        "bibjson": {
            "structs": {
                "link": {
                    "required": ["type", "url"],
                    "fields": {
                        "type": {"coerce": "link_type"},
                        "url": {"coerce": "unicode"},
                        "content_type": {"coerce": "link_content_type"}
                    }
                }
            }
        }
    }
}

BASE_ARTICLE_COERCE = deepcopy(dataobj.DataObj.DEFAULT_COERCE)
BASE_ARTICLE_COERCE["link_type"] = dataobj.string_canonicalise(["fulltext"], allow_fail=False)
BASE_ARTICLE_COERCE["link_type_optional"] = dataobj.string_canonicalise(["fulltext"], allow_fail=True)
BASE_ARTICLE_COERCE["link_content_type"] = dataobj.string_canonicalise(["PDF", "HTML", "ePUB", "XML"], allow_fail=True)

BASE_ARTICLE_SWAGGER_TRANS = deepcopy(swagger.SwaggerSupport.DEFAULT_SWAGGER_TRANS)
BASE_ARTICLE_SWAGGER_TRANS["link_type"] = {"type": "string", "format": "link_type"},  # TODO extend swagger-ui with support for this format and let it produce example values etc. on the front-end
BASE_ARTICLE_SWAGGER_TRANS["link_type_optional"] = {"type": "string", "format": "link_type_optional"},  # TODO extend swagger-ui with support for this format and let it produce example values etc. on the front-end
BASE_ARTICLE_SWAGGER_TRANS["link_content_type"] = {"type": "string", "format": "link_content_type"},  # TODO extend swagger-ui with support for this format and let it produce example values etc. on the front-end


class IncomingArticleDO(dataobj.DataObj, swagger.SwaggerSupport):
    def __init__(self, raw=None):
        self._add_struct(BASE_ARTICLE_STRUCT)
        self._add_struct(INCOMING_ARTICLE_REQUIRED)
        super(IncomingArticleDO, self).__init__(raw, construct_silent_prune=True, expose_data=True, coerce_map=BASE_ARTICLE_COERCE, swagger_trans=BASE_ARTICLE_SWAGGER_TRANS)

    def custom_validate(self):
        # only attempt to validate if this is not a blank object
        if len(list(self.data.keys())) == 0:
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
        if pissn is not None:
            pissn.id = normalise_issn(pissn.id)
        if eissn is not None:
            eissn.id = normalise_issn(eissn.id)

        # check they are not the same
        if pissn is not None and eissn is not None:
            if pissn.id == eissn.id:
                raise dataobj.DataStructureException("P-ISSN and E-ISSN should be different")

        # check the number of keywords is no more than 6
        if len(self.bibjson.keywords) > 6:
            raise dataobj.DataStructureException("bibjson.keywords may only contain a maximum of 6 keywords")

        # check if orcid id is valid
        for author in self.bibjson.author:
            if author.orcid_id is not None and regex.ORCID_COMPILED.match(author.orcid_id) is None:
                raise dataobj.DataStructureException("Invalid ORCID iD format. Please use url format, eg: https://orcid.org/0001-1111-1111-1111")


    def to_article_model(self, existing=None):
        dat = deepcopy(self.data)
        if "journal" in dat["bibjson"] and "start_page" in dat["bibjson"].get("journal", {}):
            dat["bibjson"]["start_page"] = dat["bibjson"]["journal"]["start_page"]
            del dat["bibjson"]["journal"]["start_page"]
        if "journal" in dat["bibjson"] and "end_page" in dat["bibjson"].get("journal", {}):
            dat["bibjson"]["end_page"] = dat["bibjson"]["journal"]["end_page"]
            del dat["bibjson"]["journal"]["end_page"]

        # clear out fields that we don't accept via the API
        if "admin" in dat and "in_doaj" in dat["admin"]:
            del dat["admin"]["in_doaj"]
        if "admin" in dat and "seal" in dat["admin"]:
            del dat["admin"]["seal"]
        if "admin" in dat and "upload_id" in dat["admin"]:
            del dat["admin"]["upload_id"]

        if existing is None:
            return models.Article(**dat)
        else:
            merged = dataobj.merge_outside_construct(self._struct, dat, existing.data)
            return models.Article(**merged)


class OutgoingArticleDO(dataobj.DataObj, swagger.SwaggerSupport):
    def __init__(self, raw=None):
        self._add_struct(BASE_ARTICLE_STRUCT)
        self._add_struct(OUTGOING_ARTICLE_PATCH)
        super(OutgoingArticleDO, self).__init__(raw, construct_silent_prune=True, expose_data=True, coerce_map=BASE_ARTICLE_COERCE, swagger_trans=BASE_ARTICLE_SWAGGER_TRANS)

    @classmethod
    def from_model(cls, am):
        assert isinstance(am, models.Article)
        dat = deepcopy(am.data)
        # Fix some inconsistencies with the model - start and end pages should be in bibjson
        if "start_page" in dat["bibjson"]:
            dat["bibjson"].get("journal", {})["start_page"] = dat["bibjson"]["start_page"]
            del dat["bibjson"]["start_page"]
        if "end_page" in dat["bibjson"]:
            dat["bibjson"].get("journal", {})["end_page"] = dat["bibjson"]["end_page"]
            del dat["bibjson"]["end_page"]
        return cls(dat)
    
    @classmethod
    def from_model_by_id(cls, id_):
        a = models.Article.pull(id_)
        return cls.from_model(a)
