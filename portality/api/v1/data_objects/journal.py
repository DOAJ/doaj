from portality.lib import dataobj
from portality import models

from portality.api.v1.data_objects.common_journal_application import OutgoingCommonJournalApplication

# we only have outgoing journals for the moment
JOURNAL_STRUCT = {
    "objects": ["bibjson", "admin"],
    "fields": {
        "id": {"coerce": "str"},
        "created_date": {"coerce": "utcdatetime"},
        "last_updated": {"coerce": "utcdatetime"}
    },
    "structs": {
        "admin": {
            "fields": {
                "in_doaj": {"coerce": "bool", "get__default": False},
                "ticked": {"coerce": "bool", "get__default": False},
                "seal": {"coerce": "bool", "get__default": False},
                "owner": {"coerce": "str"},
            },
            "lists": {
                "contact": {"contains": "object"}
            },
            "structs": {
                "contact": {
                    "fields": {
                        "email": {"coerce": "str"},
                        "name": {"coerce": "str"},
                    }
                }
            }
        },
        "bibjson": {
            "fields": {
                "allows_fulltext_indexing": {"coerce": "bool"},
                "alternative_title": {"coerce": "str"},
                "apc_url": {"coerce": "url"},
                "country": {"coerce": "country_code"},
                "institution": {"coerce": "str"},
                "provider": {"coerce": "str"},
                "publication_time": {"coerce": "integer"},
                "publisher": {"coerce": "str"},
                "submission_charges_url": {"coerce": "url"},
                "title": {"coerce": "str"},
            },
            "lists": {
                "deposit_policy": {"coerce": "deposit_policy", "contains": "field"},
                "format": {"coerce": "format", "contains": "field"},
                "identifier": {"contains": "object"},
                "keywords": {"coerce": "str", "contains": "field"},
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
                        "url": {"coerce": "url"},
                    },
                    "lists": {
                        "policy": {"coerce": "str", "contains": "object"},
                    },

                    "structs" : {
                        "policy" : {
                            "fields" : {
                                "name" : {"coerce": "str"},
                                "domain" : {"coerce" : "str"}
                            }
                        }
                    }
                },

                "article_statistics": {
                    "fields": {
                        "statistics": {"coerce": "bool"},
                        "url": {"coerce": "url"},
                    }
                },

                "author_copyright": {
                    "fields": {
                        "copyright": {"coerce": "str"},
                        "url": {"coerce": "url"},
                    }
                },

                "author_publishing_rights": {
                    "fields": {
                        "publishing_rights": {"coerce": "str"},
                        "url": {"coerce": "url"},
                    }
                },

                "editorial_review": {
                    "fields": {
                        "process": {"coerce": "str", "allowed_values" : ["Editorial review", "Peer review", "Blind peer review", "Double blind peer review", "Open peer review", "None"]},
                        "url": {"coerce": "url"},
                    }
                },

                "identifier": {
                    "fields": {
                        "type": {"coerce": "str"},
                        "id": {"coerce": "str"},
                    }
                },

                "license": {
                    "fields": {
                        "title": {"coerce": "license"},
                        "type": {"coerce": "license"},
                        "url": {"coerce": "url"},
                        "version": {"coerce": "str"},
                        "open_access": {"coerce": "bool"},
                        "BY": {"coerce": "bool"},
                        "NC": {"coerce": "bool"},
                        "ND": {"coerce": "bool"},
                        "SA": {"coerce": "bool"},
                        "embedded": {"coerce": "bool"},
                        "embedded_example_url": {"coerce": "url"},
                    }
                },

                "link": {
                    "fields": {
                        "type": {"coerce": "str"},
                        "url": {"coerce": "url"},
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
                        "url": {"coerce": "url"},
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
                        "scheme": {"coerce": "str"},
                        "term": {"coerce": "str"},
                        "code": {"coerce": "str"},
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