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
                "in_doaj": {"coerce": "bool", "get__default": False},
                "ticked": {"coerce": "bool", "get__default": False},
                "seal": {"coerce": "bool", "get__default": False},
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
                "alternative_title": {"coerce": "unicode"},
                "country": {"coerce": "country_code"},
                "publication_time_weeks": {"coerce": "integer"},
                "title": {"coerce": "unicode"},
                "pissn": {"coerce": "unicode"},
                "eissn":{"coerce": "unicode"},
                "boai": {"coerce": "bool"}

            },
            "lists": {
                "format": {"coerce": "format", "contains": "field"},
                "keywords": {"coerce": "unicode", "contains": "field"},
                "language": {"coerce": "isolang_2letter", "contains": "field"},
                "license": {"contains": "object"},
                "link": {"contains": "object"},
                "persistent_identifier_scheme": {"coerce": "persistent_identifier_scheme", "contains": "field"},
                "subject": {"contains": "object"}
            },
            "objects": [
                "preservation",
                "plagiarism_detection",
                "submission_charges",
            ],
            "structs": {
                "apc": {
                    "fields": {
                        "url": {"coerce": "unicode"}
                    },
                    "lists": {
                        "max": {
                            "fields":{
                                "price": {"coerce", "unicode"},
                                "currency": {"coerce", "unicode"}
                            }
                        }
                    }
                },
                "article":{
                    "fields": {
                        "embedded": {"coerce": "bool"},
                        "embedded_example_url": {"coerce": "unicode"}
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
                "pid_scheme": {
                    "fields": {
                        "has_pid_scheme" : {"coerce": "bool"},
                        "scheme": {"coerce": "unicode"}
                    }
                },
                "publisher": {
                    "fields": {
                        "name": {"coerce": "unicode"},
                        "country": {"coerce": "unicode"}
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
                        "url": {"coerce": "unicode"}
                    }
                },
                "plagiarism": {
                    "fields": {
                        "detection": {"coerce": "bool"},
                        "url": {"coerce": "unicode"},
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
                        "scheme": {"coerce": "unicode"},
                        "term": {"coerce": "unicode"},
                        "code": {"coerce": "unicode"},
                    }
                },
                 "waiver": {
                     "fields": {
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