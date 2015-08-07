from portality.lib import dataobj
from portality import models


class JournalDO(dataobj.DataObj):
    _type = 'journal'

    def __init__(self, __raw=None):
        self._RESERVED_ATTR_NAMES += ['from_model']

        struct = {
            "objects": ["bibjson", "admin"],
            "fields": {
                "id": {"coerce": "unicode"},
                "created_date": {"coerce": "utcdatetime"},
                "last_updated": {"coerce": "utcdatetime"}
            },
            "structs": {
                "admin": {
                    "fields": {
                        "in_doaj": {"coerce": "bool", "default": False},
                        "ticked": {"coerce": "bool", "default": False},
                        "seal": {"coerce": "bool", "default": False},
                        "owner": {"coerce": "unicode"},
                    },
                    "lists": {
                        "contact": {"contains": "object"}
                    },
                    "structs": {
                        "contact": {
                            "fields": {
                                "email": {"coerce": "unicode"},
                                "name": {"coerce": "unicode"},
                            }
                        }
                    }
                },
                "bibjson": {
                    "fields": {
                        "title": {"coerce": "unicode"},
                        "alternative_title": {"coerce": "unicode"},
                        "country": {"coerce": "unicode"},
                        "publisher": {"coerce": "unicode"},
                        "provider": {"coerce": "unicode"},
                        "institution": {"coerce": "unicode"},
                        "apc_url": {"coerce": "unicode"},
                        "submission_charges_url": {"coerce": "unicode"},
                        "allows_fulltext_indexing": {"coerce": "bool"},
                        "publication_time": {"coerce": "integer"},
                    },
                    "objects": [
                        "oa_start",
                        "oa_end",
                        "apc",
                        "submission_charges",
                        "archiving_policy",
                        "editorial_review",
                        "plagiarism_detection",
                        "article_statistics",
                        "author_copyright",
                        "author_publishing_rights",
                    ],
                    "lists": {
                        "identifier": {"contains": "object"},
                        "keywords": {"coerce": "unicode", "contains": "field"},
                        "language": {"coerce": "unicode", "contains": "field"},
                        "link": {"contains": "object"},
                        "subject": {"contains": "object"},
                        "deposit_policy": {"coerce": "unicode", "contains": "field"},
                        "persistent_identifier_scheme": {"coerce": "unicode", "contains": "field"},
                        "format": {"coerce": "unicode", "contains": "field"},
                        "license": {"contains": "object"},
                    },
                    "required": [],
                    "structs": {
                        "oa_start": {
                            "fields": {
                                "year": {"coerce": "integer"},
                                "volume": {"coerce": "integer"},
                                "number": {"coerce": "integer"},
                            }
                        },
                        "oa_end": {
                            "fields": {
                                "year": {"coerce": "integer"},
                                "volume": {"coerce": "integer"},
                                "number": {"coerce": "integer"},
                            }
                        },
                        "apc": {
                            "fields": {
                                "currency": {"coerce": "unicode"},
                                "average_price": {"coerce": "integer"}
                            }
                        },
                        "submission_charges": {
                            "fields": {
                                "currency": {"coerce": "unicode"},
                                "average_price": {"coerce": "integer"}
                            }
                        },
                        "archiving_policy": {
                            "fields": {
                                "url": {"coerce": "unicode"},
                            },
                            "lists": {
                                "policy": {"coerce": "unicode", "contains": "field"},
                            }
                        },
                        "editorial_review": {
                            "fields": {
                                "process": {"coerce": "unicode"},
                                "url": {"coerce": "unicode"},
                            }
                        },
                        "plagiarism_detection": {
                            "fields": {
                                "detection": {"coerce": "bool"},
                                "url": {"coerce": "unicode"},
                            }
                        },
                        "article_statistics": {
                            "fields": {
                                "detection": {"coerce": "bool"},
                                "url": {"coerce": "unicode"},
                            }
                        },
                        "author_copyright": {
                            "fields": {
                                "copyright": {"coerce": "unicode"},
                                "url": {"coerce": "unicode"},
                            }
                        },
                        "author_publishing_rights": {
                            "fields": {
                                "publishing_rights": {"coerce": "unicode"},
                                "url": {"coerce": "unicode"},
                            }
                        },
                        "identifier": {
                            "fields": {
                                "type": {"coerce": "unicode"},
                                "id": {"coerce": "unicode"},
                            }
                        },
                        "link": {
                            "fields": {
                                "type": {"coerce": "unicode"},
                                "url": {"coerce": "unicode"},
                            }
                        },
                        "subject": {
                            "fields": {
                                "scheme": {"coerce": "unicode"},
                                "term": {"coerce": "unicode"},
                                "code": {"coerce": "unicode"},
                            }
                        },
                        "license": {
                            "fields": {
                                "title": {"coerce": "unicode"},
                                "type": {"coerce": "unicode"},
                                "url": {"coerce": "unicode"},
                                "version": {"coerce": "unicode"},
                                "open_access": {"coerce": "bool"},
                                "BY": {"coerce": "bool"},
                                "NC": {"coerce": "bool"},
                                "ND": {"coerce": "bool"},
                                "SA": {"coerce": "bool"},
                                "embedded": {"coerce": "bool"},
                                "embedded_example_url": {"coerce": "unicode"},
                            }
                        },
                    }
                }
            }
        }

        super(JournalDO, self).__init__(__raw, _struct=struct, _silent_drop_extra_fields=True)

    @classmethod
    def from_model(cls, jm):
        assert isinstance(jm, models.Journal)
        return cls(jm.data)

    # @property
    # def title(self):
    #     return self._get_single("metadata.title", coerce=dataobj.to_unicode())
    #
    # @title.setter
    # def title(self, val):
    #     self._set_single("metadata.title", val, coerce=dataobj.to_unicode(), allow_none=False, ignore_none=True)
    #
    # @property
    # def version(self):
    #     return self._get_single("metadata.version", coerce=dataobj.to_unicode())
    #
    # @version.setter
    # def version(self, val):
    #     self._set_single("metadata.version", val, coerce=dataobj.to_unicode())
    #
    # @property
    # def type(self):
    #     return self._get_single("metadata.type", coerce=dataobj.to_unicode())
    #
    # @type.setter
    # def type(self, val):
    #     self._set_single("metadata.type", val, coerce=dataobj.to_unicode(), allow_none=False, ignore_none=True)
    #
    # @property
    # def publisher(self):
    #     return self._get_single("metadata.publisher", coerce=dataobj.to_unicode())
    #
    # @publisher.setter
    # def publisher(self, val):
    #     self._set_single("metadata.publisher", val, coerce=dataobj.to_unicode(), allow_none=False, ignore_none=True)
    #
    # @property
    # def language(self):
    #     # Note that in this case we don't coerce to iso language, as it's a slightly costly operation, and all incoming
    #     # data should already be coerced
    #     return self._get_single("metadata.language", coerce=dataobj.to_unicode())
    #
    # @language.setter
    # def language(self, val):
    #     self._set_single("metadata.language", val, coerce=dataobj.to_isolang(), allow_coerce_failure=True, allow_none=False, ignore_none=True)
    #
    # @property
    # def publication_date(self):
    #     return self._get_single("metadata.publication_date", coerce=dataobj.date_str())
    #
    # @publication_date.setter
    # def publication_date(self, val):
    #     self._set_single("metadata.publication_date", val, coerce=dataobj.date_str(), allow_coerce_failure=True, allow_none=False, ignore_none=True)
    #
    # @property
    # def date_accepted(self):
    #     return self._get_single("metadata.date_accepted", coerce=dataobj.date_str())
    #
    # @date_accepted.setter
    # def date_accepted(self, val):
    #     self._set_single("metadata.date_accepted", val, coerce=dataobj.date_str(), allow_coerce_failure=True, allow_none=False, ignore_none=True)
    #
    # @property
    # def date_submitted(self):
    #     return self._get_single("metadata.date_submitted", coerce=dataobj.date_str())
    #
    # @date_submitted.setter
    # def date_submitted(self, val):
    #     self._set_single("metadata.date_submitted", val, coerce=dataobj.date_str(), allow_coerce_failure=True, allow_none=False, ignore_none=True)
    #
    # @property
    # def identifiers(self):
    #     return self._get_list("metadata.identifier")
    #
    # def get_identifiers(self, type):
    #     ids = self._get_list("metadata.identifier")
    #     res = []
    #     for i in ids:
    #         if i.get("type") == type:
    #             res.append(i.get("id"))
    #     return res
    #
    # def add_identifier(self, id, type):
    #     if id is None or type is None:
    #         return
    #     uc = dataobj.to_unicode()
    #     obj = {"id" : self._coerce(id, uc), "type" : self._coerce(type, uc)}
    #     self._delete_from_list("metadata.identifier", matchsub=obj, prune=False)
    #     self._add_to_list("metadata.identifier", obj)
    #
    # @property
    # def authors(self):
    #     return self._get_list("metadata.author")
    #
    # @authors.setter
    # def authors(self, objlist):
    #     # validate the object structure quickly
    #     allowed = ["name", "affiliation", "identifier"]
    #     for obj in objlist:
    #         for k in obj.keys():
    #             if k not in allowed:
    #                 raise dataobj.DataSchemaException("Author object must only contain the following keys: {x}".format(x=", ".join(allowed)))
    #
    #         # coerce the values of some of the keys
    #         uc = dataobj.to_unicode()
    #         for k in ["name", "affiliation"]:
    #             if k in obj:
    #                 obj[k] = self._coerce(obj[k], uc)
    #
    #     # finally write it
    #     self._set_list("metadata.author", objlist)
    #
    # def add_author(self, author_object):
    #     self._delete_from_list("metadata.author", matchsub=author_object)
    #     self._add_to_list("metadata.author", author_object)
    #
    # @property
    # def projects(self):
    #     return self._get_list("metadata.project")
    #
    # @projects.setter
    # def projects(self, objlist):
    #     # validate the object structure quickly
    #     allowed = ["name", "grant_number", "identifier"]
    #     for obj in objlist:
    #         for k in obj.keys():
    #             if k not in allowed:
    #                 raise dataobj.DataSchemaException("Project object must only contain the following keys: {x}".format(x=", ".join(allowed)))
    #
    #         # coerce the values of some of the keys
    #         uc = dataobj.to_unicode()
    #         for k in ["name", "grant_number"]:
    #             if k in obj:
    #                 obj[k] = self._coerce(obj[k], uc)
    #
    #     # finally write it
    #     self._set_list("metadata.project", objlist)
    #
    # def add_project(self, project_obj):
    #     self._delete_from_list("metadata.project", matchsub=project_obj)
    #     self._add_to_list("metadata.project", project_obj)
    #
    # @property
    # def subjects(self):
    #     return self._get_list("metadata.subject")
    #
    # def add_subject(self, kw):
    #     self._add_to_list("metadata.subject", kw, coerce=dataobj.to_unicode(), unique=True)
    #
    # @property
    # def license(self):
    #     return self._get_single("metadata.license_ref")
    #
    # @license.setter
    # def license(self, obj):
    #     # validate the object structure quickly
    #     allowed = ["title", "type", "url", "version"]
    #     for k in obj.keys():
    #         if k not in allowed:
    #             raise dataobj.DataSchemaException("License object must only contain the following keys: {x}".format(x=", ".join(allowed)))
    #
    #     # coerce the values of the keys
    #     uc = dataobj.to_unicode()
    #     for k in allowed:
    #         if k in obj:
    #             obj[k] = self._coerce(obj[k], uc)
    #
    #     # finally write it
    #     self._set_single("metadata.license_ref", obj)
    #
    # def set_license(self, type, url):
    #     uc = dataobj.to_unicode()
    #     type = self._coerce(type, uc)
    #     url = self._coerce(url, uc)
    #     obj = {"title" : type, "type" : type, "url" : url}
    #     self._set_single("metadata.license_ref", obj)
    #
    # @property
    # def source_name(self):
    #     return self._get_single("metadata.source.name", coerce=dataobj.to_unicode())
    #
    # @source_name.setter
    # def source_name(self, val):
    #     self._set_single("metadata.source.name", val, coerce=dataobj.to_unicode())
    #
    # @property
    # def source_identifiers(self):
    #     return self._get_list("metadata.source.identifier")
    #
    # def add_source_identifier(self, type, id):
    #     if id is None or type is None:
    #         return
    #     uc = dataobj.to_unicode()
    #     obj = {"id" : self._coerce(id, uc), "type" : self._coerce(type, uc)}
    #     self._delete_from_list("metadata.source.identifier", matchsub=obj, prune=False)
    #     self._add_to_list("metadata.source.identifier", obj)


    """
    {
    "id" : "32-digit hexadecimal number so chars are [a-f][0-9]",  # use a library to validate, not homebrew, not all combos of those chars are hex numbers, and case has to be taken into account
    "bibjson": {
        "title" : "The title of the journal",
        "alternative_title" : "An alternative title for the journal",
        "identifier": [
            {"type" : "pissn", "id" : "<print issn>"},
            {"type" : "eissn", "id" : "<electronic issn>"},
        ],
        "keywords" : [<list of free-text keywords>],
        "language" : ["The language of the journal"],
        "country" : "<country of journal publication>",
        "publisher" : "<publisher>",
        "provider" : "<service provider or platform used for journal>",
        "institution" : "<society or institution responsible for journal>",
        "link": [
            {"type" : "homepage", "url" : "<url>"},
            {"type" : "waiver_policy", "url" : "<url>"},
            {"type" : "editorial_board", "url" : "<url>"},
            {"type" : "aims_scope", "url" : "<url>"},
            {"type" : "author_instructions", "url" : "<url>"},
            {"type" : "oa_statement", "url" : "<url>"}
        ],
        "subject" : [
            {
                "scheme" : "<scheme>",
                "term" : "<term>",
                "code" : "<code>"
            }
        ],
        "oa_start": {
            "year" : "<year>",
            "volume" : "<volume>", # Deprecated - may be removed
            "number" : "<issue number>" # Deprecated - may be removed
        },
        "oa_end": {
            "year" : "<year>",
            "volume" : "<volume>", # Deprecated - may be removed
            "number" : "<issue number>" # Deprecated - may be removed
        },
        "apc_url" : "<apc info url>",
        "apc": {
            "currency" : "<currency code>",
            "average_price" : "<average price of APC>"
        },
        "submission_charges_url" : "<submission charges info url>",
        "submission_charges": {
            "currency" : "<currency code>",
            "average_price" : "<average price of submission charge>"
        },
        "archiving_policy": {
            "policy" : [
                "<known policy type (e.g. LOCKSS)>",
                ["<policy category>", "<previously unknown policy type>"]
            ],
            "url" : "<url to policy information page>"
        },
        "editorial_review": {
            "process" : "<type of editorial review process>",
            "url" : "<url to info about editorial review process>"
        },
        "plagiarism_detection": {
            "detection": true|false, # is there plagiarism detection
            "url" : "<url to info about plagiarism detection>"
        },
        "article_statistics": {
            "statistics" : true|false
            "url" : "<url for info about article statistics>"
        },
        "deposit_policy" : ["<policy type (e.g. Sherpa/Romeo)>"],
        "author_copyright": {
            "copyright" : "<copyright status>",
            "url" : "<url for information about copyright position>"
        },
        "author_publishing_rights": {
            "publishing_rights" : "<publishing rights status>",
            "url" : "<url for information about publishing rights>"
        },
        "allows_fulltext_indexing" : true|false,
        "persistent_identifier_scheme" : [<list of names of pid schemes>],
        "format" : [<list of mimetypes of fulltext formats available>],
        "publication_time" : "<average time in weeks to publication>",
        "license" : [
            {
                "title" : "<name of licence>",
                "type" : "<type>",
                "url" : "<url>",
                "version" : "<version>",
                "open_access": true|false, # is the licence BOAI compliant
                "BY": true/false,
                "NC": true/false,
                "ND": true/false,
                "SA": true/false,
                "embedded" : true|false # is the licence metadata embedded in the article pages>,
                "embedded_example_url" :  "<url for example of embedded licence>"
            }
        ]
    },
    "admin": {
        "in_doaj" : true|false,
        "ticked" : true|false,
        "seal" : true|false,
        "contact" : [
            {
                "email" : "<email of journal contact>",
                "name" : "<name of journal contact>"
            }
        ],
        "owner" : "<account id of owner>"
    },
    "created_date" : "<date created>",
    "last_updated" : "<date record last modified>",
    }
    """