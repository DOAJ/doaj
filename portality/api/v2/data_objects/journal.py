from portality import models

from portality.api.v2.data_objects.common_journal_application import OutgoingCommonJournalApplication

# we only have outgoing journals for the moment
from portality.lib.coerce import COERCE_MAP

JOURNAL_STRUCT = {
    "objects": ["bibjson", "admin"],
    "fields": {
        "id": {"coerce": "unicode"},
        "created_date": {"coerce": "utcdatetime"},
        "last_updated": {"coerce": "utcdatetime"},
        "last_manual_update": {"coerce": "utcdatetime"}
    },
    "structs": {
        "admin": {
            "fields": {
                "in_doaj": {"coerce": "bool", "get__default": False},
                "ticked": {"coerce": "bool", "get__default": False},
                "seal": {"coerce": "bool", "get__default": False}
            }
        },
        "bibjson": {
            "fields": {
                "alternative_title": {"coerce": "unicode"},
                "boai": {"coerce": "bool"},
                "eissn": {"coerce": "unicode"},
                "pissn": {"coerce": "unicode"},
                "publication_time_weeks": {"coerce": "integer"},
                "title": {"coerce": "unicode"}
            },
            "lists": {
                "is_replaced_by" : {"contains" : "field", "coerce" : "issn"},
                "keywords": {"coerce": "unicode", "contains": "field"},
                "language": {"coerce": "isolang_2letter", "contains": "field"},
                "license": {"contains": "object"},
                "subject": {"contains": "object"}
            },
            "objects": [
                "apc",
                "article",
                "copyright",
                "deposit_policy",
                "editorial",
                "institution",
                "other_charges",
                "pid_scheme",
                "plagiarism",
                "preservation",
                "publisher",
                "ref",
                "waiver"
            ],
            "structs": {
                "apc": {
                    "fields": {
                        "url": {"coerce": "unicode"},
                        "has_apc": {"coerce": "unicode"}
                    },
                    "lists": {
                        "max": {"contains": "object"}
                    },
                    "structs": {
                        "max": {
                            "fields": {
                                "currency": {"coerce": "unicode"},
                                "price": {"coerce": "integer"}
                            }
                        }
                    }
                },
                "article" : {
                    "fields" : {
                        "license_display_example_url" : {"coerce" : "unicode"},
                        "orcid" : {"coerce" : "bool"},
                        "i4oc_open_citations" : {"coerce" : "bool"}
                    },
                    "lists" : {
                        "license_display" : {"contains" : "field", "coerce" : "unicode", "allowed_values" : ["embed", "display", "no"]},
                    }
                },
                "copyright": {
                    "fields": {
                        "author_retains": {"coerce": "bool"},
                        "url": {"coerce": "unicode"},
                    }
                },
                "deposit_policy": {
                    "fields": {
                        "has_policy": {"coerce": "bool"},
                        "is_registered": {"coerce": "bool"}
                    },
                    "lists": {
                        "service": {"coerce": "unicode", "contains": "field"}
                    }
                },
                "editorial": {
                    "fields": {
                        "review_url": {"coerce": "unicode"},
                        "board_url": {"coerce": "unicode"}
                    },
                    "lists": {
                        "review_process": {"contains": "field", "coerce": "unicode"
                            #,"allowed_values": ["Editorial review", "Peer review", "Blind peer review", "Double blind peer review", "Open peer review", "None"]
                        },
                    }
                },
                "institution": {
                    "fields": {
                        "name": {"coerce": "unicode"},
                        "country": {"coerce": "unicode"}
                    }
                },
                "license": {
                    "fields": {
                        "type": {"coerce": "unicode"},
                        "url": {"coerce": "unicode"},
                        "BY": {"coerce": "bool"},
                        "NC": {"coerce": "bool"},
                        "ND": {"coerce": "bool"},
                        "SA": {"coerce": "bool"}
                    }
                },
                "other_charges": {
                    "fields": {
                        "has_other_charges": {"coerce": "bool"},
                        "url": {"coerce": "unicode"}
                    }
                },
                "pid_scheme": {
                    "fields": {
                        "has_pid_scheme": {"coerce": "bool"},
                        "scheme": {"coerce": "unicode"}
                    }
                },
                "plagiarism": {
                    "fields": {
                        "detection": {"coerce": "bool"},
                        "url": {"coerce": "unicode"},
                    }
                },
                "preservation": {
                    "fields": {
                        "has_preservation": {"coerce": "unicode"},
                        "national_library": {"coerce": "unicode"},
                        "url": {"coerce": "unicode"}
                    },
                    "lists": {
                        "service": {"coerce": "unicode", "contains": "field"},
                    },
                    "structs": {
                        "policy": {
                            "fields": {
                                "name": {"coerce": "unicode"},
                                "domain": {"coerce": "unicode"}
                            }
                        }
                    }
                },
                "publisher": {
                    "fields": {
                        "name": {"coerce": "unicode"},
                        "country": {"coerce": "unicode"}
                    }
                },
                "ref": {
                    "fields": {
                        "license_terms": {"coerce": "unicode"},
                        "oa_statement": {"coerce": "unicode"},
                        "journal": {"coerce": "unicode"},
                        "aims_scope": {"coerce": "unicode"},
                        "author_instructions": {"coerce": "unicode"}

                    }
                },
                "subject": {
                    "fields": {
                        "code": {"coerce": "unicode"},
                        "scheme": {"coerce": "unicode"},
                        "term": {"coerce": "unicode"}
                    }
                },
                "waiver": {
                    "fields": {
                        "has_waiver": {"coerce": "unicode"},
                        "url": {"coerce": "unicode"}
                    }
                }
            }
        }
    }
}


class OutgoingJournal(OutgoingCommonJournalApplication):

    __SEAMLESS_COERCE__ = COERCE_MAP

    def __init__(self, raw=None):
        super(OutgoingJournal, self).__init__(raw, struct=JOURNAL_STRUCT, silent_prune=True)

    @classmethod
    def from_model(cls, jm):
        assert isinstance(jm, models.Journal)
        d = super(OutgoingJournal, cls).from_model(jm)
        return d

    @classmethod
    def from_model_by_id(cls, id_):
        j = models.Journal.pull(id_)
        return cls.from_model(j)

    @property
    def data(self):
        return self.__seamless__.data