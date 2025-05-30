from portality.api.current.data_objects.common import _check_for_script
from portality.lib import dataobj, swagger
from portality import models, regex
from portality.ui.messages import Messages
from portality.util import normalise_issn
from copy import deepcopy
from portality.regex import DOI,DOI_COMPILED

BASE_ARTICLE_STRUCT = {
    "fields": {
        "id": {"coerce": "unicode"},                # Note that we'll leave these in for ease of use by the
        "created_date": {"coerce": "utcdatetime"},  # caller, but we'll need to ignore them on the conversion
        "last_updated": {"coerce": "utcdatetime"},  # to the real object
        "es_type": {"coerce": "unicode"}
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
                # The base struct can't coerce url because we have bad data https://github.com/DOAJ/doajPM/issues/2038
                # Leaving this here in case we want to reinstate in the future
#                "link": {
#                    "fields": {
#                        "type": {"coerce": "link_type"},
#                        "url": {"coerce": "url"},
#                        "content_type": {"coerce": "link_content_type"}
#                    }
#                },
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
                        "language": {"coerce": "unicode", "contains": "field"}
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
BASE_ARTICLE_SWAGGER_TRANS["link_type"] = {"type": "string", "format": "link_type"}  # TODO extend swagger-ui with support for this format and let it produce example values etc. on the front-end
BASE_ARTICLE_SWAGGER_TRANS["link_type_optional"] = {"type": "string", "format": "link_type_optional"}  # TODO extend swagger-ui with support for this format and let it produce example values etc. on the front-end
BASE_ARTICLE_SWAGGER_TRANS["link_content_type"] = {"type": "string", "format": "link_content_type"}  # TODO extend swagger-ui with support for this format and let it produce example values etc. on the front-end


class IncomingArticleDO(dataobj.DataObj, swagger.SwaggerSupport):
    """
    ~~APIIncomingArticle:Model->DataObj:Library~~
    """
    def __init__(self, raw=None):
        self._add_struct(BASE_ARTICLE_STRUCT)
        self._add_struct(INCOMING_ARTICLE_REQUIRED)
        super(IncomingArticleDO, self).__init__(raw, construct_silent_prune=True, expose_data=True,
                                                coerce_map=BASE_ARTICLE_COERCE,
                                                swagger_trans=BASE_ARTICLE_SWAGGER_TRANS)

    def _trim_empty_strings(self):

        def _remove_element_if_empty_data(field):
            if field in bibjson and bibjson[field] == "":
                del bibjson[field]

        def _remove_from_the_list_if_empty_data(bibjson_element, field=None):
            if bibjson_element in bibjson:
                for i in range(len(bibjson[bibjson_element]) - 1, -1, -1):
                    ide = bibjson[bibjson_element][i]
                    if field is not None:
                        if ide.get(field,"") == "":
                            bibjson[bibjson_element].remove(ide)
                    else:
                        if ide == "":
                            bibjson[bibjson_element].remove(ide)

        bibjson = self.data["bibjson"]

        _remove_element_if_empty_data("title")
        _remove_element_if_empty_data("year")
        _remove_element_if_empty_data("month")
        _remove_element_if_empty_data("abstract")
        _remove_from_the_list_if_empty_data("author", "name")
        _remove_from_the_list_if_empty_data("subject", "term")
        _remove_from_the_list_if_empty_data("identifier", "id")
        _remove_from_the_list_if_empty_data("link", "url")
        _remove_from_the_list_if_empty_data("keywords")

    def custom_validate(self):
        # only attempt to validate if this is not a blank object
        if len(list(self.data.keys())) == 0:
            return

        # remove all fields with empty data ""
        self._trim_empty_strings()

        if _check_for_script(self.data):
            raise dataobj.ScriptTagFoundException(Messages.EXCEPTION_SCRIPT_TAG_FOUND)

        # at least one of print issn / e-issn, and they must be different
        #
        # check that there are identifiers at all
        identifiers = self.bibjson.identifier
        if identifiers is None or len(identifiers) == 0:
            raise dataobj.DataStructureException("You must specify at least one Print ISSN or online ISSN in bibjson.identifier")

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
            raise dataobj.DataStructureException("You must specify at least one Print ISSN or online ISSN in bibjson.identifier")

        # normalise the ids
        if pissn is not None:
            pissn.id = normalise_issn(pissn.id)
        if eissn is not None:
            eissn.id = normalise_issn(eissn.id)

        # check they are not the same
        if pissn is not None and eissn is not None:
            if pissn.id == eissn.id:
                raise dataobj.DataStructureException("Print ISSN and online ISSN should be different")


        # check removed: https://github.com/DOAJ/doajPM/issues/2950
        # if len(self.bibjson.keywords) > 6:
        #     raise dataobj.DataStructureException("bibjson.keywords may only contain a maximum of 6 keywords")

        # check if orcid id is valid
        for author in self.bibjson.author:
            if author.orcid_id is not None and regex.ORCID_COMPILED.match(author.orcid_id) is None:
                raise dataobj.DataStructureException("Invalid ORCID iD. Please enter your ORCID iD structured as: https://orcid.org/0000-0000-0000-0000. URLs must start with https.")

        for x in self.bibjson.identifier:
            if x.type == "doi":
                if not DOI_COMPILED.match(x.id):
                    raise dataobj.DataStructureException(
                        "Invalid DOI format.")
                break

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
        if "admin" in dat and "upload_id" in dat["admin"]:
            del dat["admin"]["upload_id"]
        if "es_type" in dat:
            del dat["es_type"]

        # the seal has been removed, but in case external users are still providing it, keeping
        # this data cleanup
        if "admin" in dat and "seal" in dat["admin"]:
            del dat["admin"]["seal"]

        if existing is None:
            return models.Article(**dat)
        else:
            merged = dataobj.merge_outside_construct(self._struct, dat, existing.data)
            return models.Article(**merged) #~~->Article:Model~~


class OutgoingArticleDO(dataobj.DataObj, swagger.SwaggerSupport):
    """
    ~~APIOutgoingArticle:Model->DataObj:Library~~
    """
    def __init__(self, raw=None):
        self._add_struct(BASE_ARTICLE_STRUCT)
        self._add_struct(OUTGOING_ARTICLE_PATCH)
        super(OutgoingArticleDO, self).__init__(raw, construct_silent_prune=True, expose_data=True, coerce_map=BASE_ARTICLE_COERCE, swagger_trans=BASE_ARTICLE_SWAGGER_TRANS)

    @classmethod
    def from_model(cls, am):
        assert isinstance(am, models.Article)   #~~->Article:Model~~
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
