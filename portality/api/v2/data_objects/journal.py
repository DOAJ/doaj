from portality import models

from portality.api.v1.data_objects.common_journal_application import OutgoingCommonJournalApplication

# we only have outgoing journals for the moment
JOURNAL_STRUCT = {
    "objects": ["bibjson", "admin"],
    "fields": {
        "id": {"coerce": "unicode"},
        "created_date": {"coerce": "utcdatetime"},
        "last_updated": {"coerce": "utcdatetime"}
    },
    "structs": {
        "admin": {
            "fields": {
                "in_doaj": {"coerce": "bool", "get__default": "False"},
                "seal": {"coerce": "bool", "get__default": "False"},
                "ticked": {"coerce": "bool", "get__default": "False"},
                "owner": {"coerce": "unicode"},
            }
        },
        "bibjson": {
            "fields": {
                "alternative_title": {"coerce": "unicode"},
                "boai": {"coerce": "bool"},
                "eissn":{"coerce": "unicode"},
                "pissn": {"coerce": "unicode"},
                "publication_time_weeks": {"coerce": "integer"},
                "title": {"coerce": "unicode"}
            },
            "lists": {
                "keywords": {"coerce": "unicode", "contains": "field"},
                "language": {"coerce": "isolang_2letter", "contains": "field"},
                "license": {"contains" : "object"},
                "subject": {"contains": "object"}
            },
            "objects": [
                "apc",
                "article",
                "copyright",
                "deposit_policy",
                "editorial"
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
                    "lists" : {
                        "max" : {"contains" : "object"}
                    },
                    "structs" : {
                        "max" : {
                            "fields" : {
                                "currency" : {"coerce" : "unicode"},
                                "price" : {"coerce" : "integer"}
                            }
                        }
                    }
                },
                "article":{
                    "fields": {
                        "embedded_licence": {"coerce": "bool"},
                        "embedded_licence_url": {"coerce": "unicode"},
                        "orcid" : {"coerce": "unicode"},
                        "i4oc_open_citations": {"coerce": "unicode"}
                    }
                },
                "copyright": {
                    "fields": {
                        "author_retains": {"coerce": "bool"},
                        "url": {"coerce": "bool"},
                    }
                },
                "deposit_policy": {
                    "fields": {
                        "has_policy" : {"coerce" : "bool"},
                        "is_registered": {"coerce" : "bool"}
                    },
                    "lists" : {
                        "service" : {"coerce": "unicode", "contains": "unicode"}
                    }
                },
                "editorial": {
                    "fields": {
                        "review_url": {"coerce": "unicode"},
                        "board_url": {"coerce":"unicode"}
                    },
                    "lists": {
                        "review_process": {"coerce": "unicode","allowed_values": ["Editorial review", "Peer review", "Blind peer review", "Double blind peer review", "Open peer review", "None"]},
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
                        "type": {"coerce": "license"},
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
                    },
                    "lists": {
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
                        "service": {"coerce": "unicode", "contains": "object"},
                    },
                    "structs" : {
                        "policy" : {
                            "fields" : {
                                "name" : {"coerce": "unicode"},
                                "domain" : {"coerce" : "unicode"}
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
                    "fields":{
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

    def __init__(self, raw=None):
        super(OutgoingJournal, self).__init__(raw, struct=JOURNAL_STRUCT, construct_silent_prune=True, expose_data=True)

    @classmethod
    def from_model(cls, jm):
        assert isinstance(jm, models.Journal)
        return super(OutgoingJournal, cls).from_model(jm)

    @classmethod
    def from_model_by_id(cls, id_):
        j = models.Journal.pull(id_)
        return cls.from_model(j)