JOURNAL_BIBJSON = {
    "objects" : [
        "bibjson"
    ],
    "structs" : {
        "bibjson" : {
            "fields" : {
                "alternative_title" : {"coerce" : "unicode"},
                "boai" : {"coerce" : "bool"},
                "discontinued_date" : {"coerce" : "bigenddate"},
                "eissn" : {"coerce" : "unicode"},
                "pissn" : {"coerce" : "unicode"},
                "publication_time_weeks" : {"coerce" : "integer"},
                "title" : {"coerce" : "unicode"}
            },
            "lists" : {
                "is_replaced_by" : {"contains" : "field", "coerce" : "unicode"},
                "keywords" : {"contains" : "field", "coerce" : "unicode_lower"},
                "language" : {"contains" : "field", "coerce" : "unicode_upper"},
                "license" : {"contains" : "object"},
                "replaces" : {"contains" : "field", "coerce" : "unicode"},
                "subject" : {"contains" : "object"}
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
                        "url" : {"coerce" : "unicode"}
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
                "article" : {
                    "fields" : {
                        "embedded_license" : {"coerce" : "bool"},
                        "embedded_license_example_url" : {"coerce" : "unicode"},
                        "orcid" : {"coerce" : "bool"},
                        "i4oc_open_citations" : {"coerce" : "bool"}
                    }
                },
                "copyright" : {
                    "fields" : {
                        "author_retains" : {"coerce" : "bool"},
                        "url" : {"coerce" : "unicode"}
                    }
                },
                "deposit_policy" : {
                    "fields" : {
                        "has_policy" : {"coerce" : "bool"},
                        "is_registered" : {"coerce" : "bool"}
                    },
                    "lists" : {
                        "service" : {"contains" : "field", "coerce" : "unicode"}
                    }
                },
                "editorial" : {
                    "fields" : {
                        "review_url" : {"coerce" : "unicode"},
                        "board_url" : {"coerce" : "unicode"}
                    },
                    "lists" : {
                        "review_process" : {"contains" : "field", "coerce" : "unicode"}
                    }
                },
                "institution" : {
                    "fields" : {
                        "name" : {"coerce" : "unicode"},
                        "country" : {"coerce" : "unicode"}
                    }
                },
                "license" : {
                    "fields" : {
                        "type" : {"coerce" : "unicode"},
                        "BY" : {"coerce" : "bool"},
                        "NC" : {"coerce" : "bool"},
                        "ND" : {"coerce" : "bool"},
                        "SA" : {"coerce" : "bool"},
                        "url" : {"coerce" : "unicode"}
                    }
                },
                "other_charges" : {
                    "fields" :{
                        "has_other_charges" : {"coerce" : "bool"},
                        "url" : {"coerce" : "unicode"}
                    }
                },
                "pid_scheme" : {
                    "fields" : {
                        "has_pid_scheme" : {"coerce" : "bool"},
                    },
                    "lists" : {
                        "scheme" : {"contains" : "field", "coerce" : "unicode"}
                    }
                },
                "plagiarism" : {
                    "fields" : {
                        "detection" : {"coerce" : "bool"},
                        "url" : {"coerce" : "unicode"}
                    }
                },
                "preservation" : {
                    "fields" : {
                        "has_preservation" : {"coerce" : "bool"},
                        "url" : {"coerce" : "unicode"}
                    },
                    "lists" : {
                        "national_library" : {"contains" : "field", "coerce" : "unicode"},
                        "service" : {"contains" : "field", "coerce" : "unicode"}
                    }
                },
                "publisher" : {
                    "fields" : {
                        "name" : {"coerce" : "unicode"},
                        "country" : {"coerce" : "unicode"}
                    }
                },
                "ref" : {
                    "fields" : {
                        "oa_statement" : {"coerce" : "unicode"},
                        "journal" : {"coerce" : "unicode"},
                        "aims_scope" : {"coerce" : "unicode"},
                        "author_instructions" : {"coerce" : "unicode"},
                        "license_terms" : {"coerce" : "unicode"},
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
                        "url" : {"coerce" : "unicode"}
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
        "last_manual_update" : {"coerce" : "utcdatetime"}
    },
    "objects" : [
        "admin",
        "index"
    ],
    "structs" : {
        "admin" : {
            "fields" : {
                "seal" : {"coerce" : "bool"},
                "bulk_upload" : {"coerce" : "unicode"},
                "owner" : {"coerce" : "unicode"},
                "editor_group" : {"coerce" : "unicode"},
                "editor" : {"coerce" : "unicode"},
            },
            "lists" : {
                "contact" : {"contains" : "object"},
                "notes" : {"contains" : "object"}
            },
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
                        "date" : {"coerce" : "utcdatetime"}
                    }
                },
            }
        },
        "index" : {
            "fields" : {
                "country" : {"coerce" : "unicode"},
                "has_apc" : {"coerce" : "unicode"},
                "has_seal" : {"coerce" : "unicode"},
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
                "schema_code" : {"contains" : "field", "coerce" : "unicode"}
            }
        }
    }
}