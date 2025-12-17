JOURNAL_BIBJSON = {
    "objects" : [
        "bibjson"
    ],
    "structs" : {
        "bibjson" : {
            "fields" : {
                "alternative_title" : {"coerce" : "unicode"},
                "boai" : {"coerce" : "bool"},
                "eissn" : {"coerce" : "issn", "set__allow_coerce_failure" : True},
                "pissn" : {"coerce" : "issn", "set__allow_coerce_failure" : True},
                "discontinued_date" : {"coerce" : "bigenddate"},
                "publication_time_weeks" : {"coerce" : "integer"},
                "title" : {"coerce" : "unicode"},
                "oa_start" : {"coerce" : "integer"}
            },
            "lists" : {
                "is_replaced_by" : {"coerce" : "issn", "contains" : "field", "set__allow_coerce_failure" : True},
                "keywords" : {"contains" : "field", "coerce" : "unicode_lower"},
                "language" : {"contains" : "field", "coerce" : "isolang_2letter_lax"},
                "license" : {"contains" : "object"},
                "replaces" : {"contains" : "field", "coerce" : "issn", "set__allow_coerce_failure" : True},
                "subject" : {"contains" : "object"},
                "labels": {"contains": "field", "coerce": "unicode", "allowed_values": ["s2o"]},
                "language_editions": {"contains": "object"}
            },
            "objects" : [
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
            "structs" : {
                "apc" : {
                    "fields" : {
                        "has_apc" : {"coerce" : "bool"},
                        "url" : {"coerce" : "url", "set__allow_coerce_failure" : True}
                    },
                    "lists" : {
                        "max" : {"contains" : "object"}
                    },
                    "structs" : {
                        "max" : {
                            "fields" : {
                                "currency" : {"coerce" : "currency_code_lax"},
                                "price" : {"coerce" : "integer"}
                            }
                        }
                    }
                },
                "article" : {
                    "fields" : {
                        "license_display_example_url" : {"coerce" : "url", "set__allow_coerce_failure" : True}
                    },
                    "lists" : {
                        "license_display" : {"contains" : "field", "coerce" : "unicode", "allowed_values" : ["Embed", "Display", "No"]},
                    }
                },
                "copyright" : {
                    "fields" : {
                        "author_retains" : {"coerce" : "bool"},
                        "url" : {"coerce" : "url", "set__allow_coerce_failure" : True}
                    }
                },
                "deposit_policy" : {
                    "fields" : {
                        "has_policy" : {"coerce" : "bool"},
                        "is_registered" : {"coerce" : "bool"},  # FIXME: this is no longer used, but remains to aid development where databases already contain this field
                        "url" : {"coerce" : "url", "set__allow_coerce_failure" : True}
                    },
                    "lists" : {
                        "service" : {"contains" : "field", "coerce" : "unicode"}
                    }
                },
                "editorial" : {
                    "fields" : {
                        "review_url" : {"coerce" : "url", "set__allow_coerce_failure" : True},
                        "board_url" : {"coerce" : "url", "set__allow_coerce_failure" : True}
                    },
                    "lists" : {
                        "review_process" : {"contains" : "field", "coerce" : "unicode"}
                    }
                },
                "institution" : {
                    "fields" : {
                        "name" : {"coerce" : "unicode"},
                        "country" : {"coerce" : "country_code", "set__allow_coerce_failure" : True}
                    }
                },
                "license" : {
                    "fields" : {
                        "type" : {"coerce" : "unicode"},
                        "BY" : {"coerce" : "bool"},
                        "NC" : {"coerce" : "bool"},
                        "ND" : {"coerce" : "bool"},
                        "SA" : {"coerce" : "bool"},
                        "url" : {"coerce" : "url", "set__allow_coerce_failure" : True}
                    }
                },
                "other_charges" : {
                    "fields" :{
                        "has_other_charges" : {"coerce" : "bool"},
                        "url" : {"coerce" : "url", "set__allow_coerce_failure" : True}
                    }
                },
                "pid_scheme" : {
                    "fields" : {
                        "has_pid_scheme" : {"coerce" : "bool"},
                    },
                    "lists" : {
                        "scheme" : {"coerce" : "unicode", "contains" : "field"}
                    }
                },
                "plagiarism" : {
                    "fields" : {
                        "detection" : {"coerce" : "bool"},
                        "url" : {"coerce" : "url", "set__allow_coerce_failure" : True}
                    }
                },
                "preservation": {
                    "fields": {
                        "has_preservation": {"coerce": "bool"},
                        "url": {"coerce" : "url", "set__allow_coerce_failure" : True}
                    },
                    "lists": {
                        "national_library": {"contains" : "field", "coerce": "unicode"},
                        "service": {"coerce": "unicode", "contains": "field"},
                    }
                },
                "publisher" : {
                    "fields" : {
                        "name" : {"coerce" : "unicode"},
                        "country" : {"coerce" : "country_code", "set__allow_coerce_failure" : True}
                    }
                },
                "ref" : {
                    "fields" : {
                        "oa_statement" : {"coerce" : "url", "set__allow_coerce_failure" : True},
                        "journal" : {"coerce" : "url", "set__allow_coerce_failure" : True},
                        "aims_scope" : {"coerce" : "url", "set__allow_coerce_failure" : True},
                        "author_instructions" : {"coerce" : "url", "set__allow_coerce_failure" : True},
                        "license_terms" : {"coerce" : "url", "set__allow_coerce_failure" : True},
                    }
                },
                "subject" : {
                    "fields" : {
                        "code" : {"coerce" : "unicode"},
                        "scheme" : {"coerce" : "unicode"},
                        "term" : {"coerce" : "unicode"}
                    }
                },
                "waiver" : {
                    "fields" : {
                        "has_waiver" : {"coerce" : "bool"},
                        "url" : {"coerce" : "url", "set__allow_coerce_failure" : True}
                    }
                },
                "language_editions": {
                    "fields": {
                        "id": {"coerce": "unicode"},
                        "language": {"coerce": "unicode"}
                    }
                }
            }
        }
    }
}

SHARED_JOURNAL_LIKE = {
    "fields" : {
        "id" : {"coerce" : "unicode"},
        "created_date" : {"coerce" : "utcdatetime"},
        "last_updated" : {"coerce" : "utcdatetime"},
        "last_manual_update" : {"coerce" : "utcdatetime"},
        "es_type": {"coerce": "unicode"}
    },
    "objects" : [
        "admin",
        "index"
    ],
    "structs" : {
        "admin" : {
            "fields" : {
                "owner" : {"coerce" : "unicode"},
                "editor_group" : {"coerce" : "unicode"},
                "editor" : {"coerce" : "unicode"},
            },
            "lists" : {
                "notes" : {"contains" : "object"}
            },
            "objects" : [
                "contact"
            ],
            "structs" : {
                "contact" : {
                    "fields" : {
                        "email" : {"coerce" : "unicode"},
                        "name" : {"coerce" : "unicode"}
                    }
                },
                "notes" : {
                    "fields" : {
                        "id" : {"coerce" : "unicode"},
                        "note" : {"coerce" : "unicode"},
                        "date" : {"coerce" : "utcdatetime"},
                        "author_id" : {"coerce" : "unicode"}  # account_id of the note's author
                    },
                    "objects": [
                        "flag"
                    ],
                    "structs": {
                        "flag": {
                            "fields": {
                                "assigned_to": {"coerce" : "unicode"},  # account_id of the note's assignee
                                "deadline": {"coerce" : "bigenddate"}
                            }
                        }
                    }
                },
            }
        },
        "index" : {
            "fields" : {
                "country" : {"coerce" : "unicode"},
                "has_apc" : {"coerce" : "unicode"},
                "is_flagged" : {"coerce" : "bool"},
                "most_urgent_flag_deadline": {"coerce" : "bigenddate"},
                "unpunctitle" : {"coerce" : "unicode"},
                "asciiunpunctitle" : {"coerce" : "unicode"},
                "continued" : {"coerce" : "unicode"},
                "has_editor_group" : {"coerce" : "unicode"},
                "has_editor" : {"coerce" : "unicode"}
            },
            "lists" : {
                "issn" : {"contains" : "field", "coerce" : "unicode"},
                "title" : {"contains" : "field", "coerce" : "unicode"},
                "subject" : {"contains" : "field", "coerce" : "unicode"},
                "schema_subject" : {"contains" : "field", "coerce" : "unicode"},
                "classification" : {"contains" : "field", "coerce" : "unicode"},
                "language" : {"contains" : "field", "coerce" : "unicode"},
                "license" : {"contains" : "field", "coerce" : "unicode"},
                "classification_paths" : {"contains" : "field", "coerce" : "unicode"},
                "schema_code" : {"contains" : "field", "coerce" : "unicode"},
                "schema_codes_tree" : {"contains" : "field", "coerce" : "unicode"},
                "flag_assignees" : {"contains" : "field", "coerce" : "unicode"}
            }
        }
    }
}

ARTICLE_STRUCT = {
    "fields" : {
        "created_date": {"coerce": "utcdatetime"},
        "es_type": {"coerce": "unicode"},
        "id": {"coerce": "unicode"},
        "last_updated": {"coerce": "utcdatetime"},
    },
    "objects": [
        "admin", "index"
    ],
    "structs": {
        "admin": {
            "fields": {
                "in_doaj": {"coerce": "bool"},
                "publisher_record_id": {"coerce": "unicode"},
                "seal": {"coerce": "bool"},
                "upload_id": {"coerce": "unicode"}
            }
        },
        "index": {
            "fields": {
                "asciiunpunctitle" : {"coerce" : "unicode"},
                "classification" : {"coerce" : "unicode"},
                "classification_paths": {"coerce" : "unicode"},
                "country" : {"coerce" : "unicode"},
                "date" : {"coerce" : "utcdatetime"},
                "date_toc_fv_month": {"coerce" : "utcdatetime"},
                "doi": {"coerce" : "unicode"},
                "fulltext": {"coerce" : "unicode"},
                "has_seal" : {"coerce" : "unicode"},
                "issn": {"coerce" : "unicode"},
                "language": {"coerce" : "unicode"},
                "publisher": {"coerce" : "unicode"},
                "schema_code": {"coerce" : "unicode"},
                "schema_codes_tree": {"coerce" : "unicode"},
                "schema_subject": {"coerce" : "unicode"},
                "subject": {"coerce" : "unicode"},
                "unpunctitle": {"coerce" : "unicode"}
            }
        }
    }
}