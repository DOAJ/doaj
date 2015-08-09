from portality.lib import dataobj
from portality import models


class JournalDO(dataobj.DataObj):
    _type = 'journal'

    def __init__(self, __raw=None):
        self._RESERVED_ATTR_NAMES += ['from_model', 'from_model_by_id']

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

    @classmethod
    def from_model_by_id(cls, id_):
        j = models.Journal.pull(id_)
        return cls.from_model(j)