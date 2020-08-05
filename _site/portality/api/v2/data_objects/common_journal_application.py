from copy import deepcopy

from portality.lib import swagger
from portality.lib.seamless import SeamlessMixin

_SHARED_STRUCT = {
    "objects": [
        "bibjson"
    ],
    "structs": {
        "bibjson": {
            "fields": {
                "alternative_title": {"coerce": "unicode"},
                "boai": {"coerce": "bool"},
                "eissn": {"coerce": "issn"},
                "pissn": {"coerce": "issn"},
                "discontinued_date": {"coerce": "bigenddate"},
                "publication_time_weeks": {"coerce": "integer"},
                "title": {"coerce": "unicode"}
            },
            "lists": {
                "is_replaced_by": {"coerce": "issn", "contains": "field"},
                "keywords": {"coerce": "unicode", "contains": "field"},
                "language": {"coerce": "isolang_2letter", "contains": "field"},
                "license": {"coerce": "unicode", "contains": "object"},
                "replaces": {"coerce": "issn", "contains": "field"},
                "subject": {"coerce": "unicode", "contains": "object"},

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
                        "url": {"coerce": "url"}
                    },
                    "lists": {
                        "max": {"contains": "object"}
                    },
                    "structs": {
                        "max": {
                            "fields": {
                                "currency": {"coerce": "currency_code"},
                                "price": {"coerce": "integer"}
                            }
                        }
                    }
                },
                "article": {
                    "fields": {
                        "license_display_example_url": {"coerce": "url"},
                        "orcid": {"coerce": "bool"},
                        "i4oc_open_citations": {"coerce": "bool"}
                    },
                    "lists": {
                        "license_display": {"contains": "field", "coerce": "unicode",
                                            "allowed_values": ["embed", "display", "no"]},
                    }
                },
                "copyright": {
                    "fields": {
                        "author_retains": {"coerce": "bool"},
                        "url": {"coerce": "url"},
                    }
                },
                "deposit_policy": {
                    "fields": {
                        "is_registered": {"coerce": "bool"},
                        "url": {"coerce": "url"}
                    },
                    "lists": {
                        "service": {"coerce": "unicode", "contains": "field"}
                    }
                },
                "editorial": {
                    "fields": {
                        "review_url": {"coerce": "url"},
                        "board_url": {"coerce": "url"}
                    },
                    "lists": {
                        "review_process": {"contains": "field", "coerce": "unicode", "allowed_values": ["Editorial "
                                                                                                        "review",
                                                                                                        "Peer "
                                                                                                        "review",
                                                                                                        "Blind peer "
                                                                                                        "review",
                                                                                                        "Double "
                                                                                                        "blind peer "
                                                                                                        "review",
                                                                                                        "Open peer "
                                                                                                        "review",
                                                                                                        "None"]},
                    }
                },
                "institution": {
                    "fields": {
                        "name": {"coerce": "unicode"},
                        "country": {"coerce": "country_code"}
                    }
                },
                "license": {
                    "fields": {
                        "type": {"coerce": "unicode"},
                        "url": {"coerce": "url"},
                        "BY": {"coerce": "bool"},
                        "NC": {"coerce": "bool"},
                        "ND": {"coerce": "bool"},
                        "SA": {"coerce": "bool"}
                    }
                },
                "other_charges": {
                    "fields": {
                        "url": {"coerce": "url"}
                    }
                },
                "pid_scheme": {
                    "lists": {
                        "scheme": {"coerce": "unicode", "contains": "field"}
                    }
                },
                "plagiarism": {
                    "fields": {
                        "detection": {"coerce": "bool"},
                        "url": {"coerce": "url"},
                    }
                },
                "preservation": {
                    "fields": {
                        "national_library": {"coerce": "unicode"},
                        "url": {"coerce": "url"}
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
                        "country": {"coerce": "country_code"}
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
                        "url": {"coerce": "url"}
                    }
                }
            }
        }
    }
}

class OutgoingCommonJournalApplication(SeamlessMixin, swagger.SwaggerSupport):

    @classmethod
    def from_model(cls, journal_or_app):
        d = deepcopy(journal_or_app.data)
        return cls(d)
