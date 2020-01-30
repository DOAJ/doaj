from portality.lib import dataobj
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
                "allows_fulltext_indexing": {"coerce": "bool"},
                "alternative_title": {"coerce": "unicode"},
                "apc_url": {"coerce": "unicode"},
                "country": {"coerce": "country_code"},
                "institution": {"coerce": "unicode"},
                "provider": {"coerce": "unicode"},
                "publication_time": {"coerce": "integer"},
                "publisher": {"coerce": "unicode"},
                "submission_charges_url": {"coerce": "unicode"},
                "title": {"coerce": "unicode"},
            },
            "lists": {
                "deposit_policy": {"coerce": "deposit_policy", "contains": "field"},
                "format": {"coerce": "format", "contains": "field"},
                "identifier": {"contains": "object"},
                "keywords": {"coerce": "unicode", "contains": "field"},
                "language": {"coerce": "isolang_2letter", "contains": "field"},
                "license": {"contains": "object"},
                "link": {"contains": "object"},
                "persistent_identifier_scheme": {"coerce": "persistent_identifier_scheme", "contains": "field"},
                "subject": {"contains": "object"}
            },
            "objects": [
                "apc",
                "archiving_policy",
                "article_statistics",
                "author_copyright",
                "author_publishing_rights",
                "editorial_review",
                "oa_start",
                "oa_end",
                "plagiarism_detection",
                "submission_charges",
            ],

            "structs": {
                "apc": {
                    "fields": {
                        "currency": {"coerce": "currency_code"},
                        "average_price": {"coerce": "integer"}
                    }
                },

                "archiving_policy": {               # NOTE: this is not the same as the storage model, so beware when working with this
                    "fields": {
                        "url": {"coerce": "unicode"},
                    },
                    "lists": {
                        "policy": {"coerce": "unicode", "contains": "object"},
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

                "article_statistics": {
                    "fields": {
                        "statistics": {"coerce": "bool"},
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

                "editorial_review": {
                    "fields": {
                        "process": {"coerce": "unicode", "allowed_values" : ["Editorial review", "Peer review", "Blind peer review", "Double blind peer review", "Open peer review", "None"]},
                        "url": {"coerce": "unicode"},
                    }
                },

                "identifier": {
                    "fields": {
                        "type": {"coerce": "unicode"},
                        "id": {"coerce": "unicode"},
                    }
                },

                "license": {
                    "fields": {
                        "title": {"coerce": "license"},
                        "type": {"coerce": "license"},
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

                "link": {
                    "fields": {
                        "type": {"coerce": "unicode"},
                        "url": {"coerce": "unicode"},
                    }
                },

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

                "plagiarism_detection": {
                    "fields": {
                        "detection": {"coerce": "bool"},
                        "url": {"coerce": "unicode"},
                    }
                },

                "submission_charges": {
                    "fields": {
                        "currency": {"coerce": "currency_code"},
                        "average_price": {"coerce": "integer"}
                    }
                },
                "subject": {
                    "fields": {
                        "scheme": {"coerce": "unicode"},
                        "term": {"coerce": "unicode"},
                        "code": {"coerce": "unicode"},
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