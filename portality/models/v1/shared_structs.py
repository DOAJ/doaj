JOURNAL_LIKE_BIBJSON = {
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
                "pid_schema",
                "plagiarism",
                "preservation",
                "publisher"
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
                        "embedded_license_example" : {"coerce" : "unicode"},
                        "orcid" : {"coerce" : "bool"}
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
                        "national_library" : {"coerce", "unicode"},
                        "other" : {"coerce" : "unicode"},
                        "url" : {"coerce" : "unicode"}
                    },
                    "lists" : {
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

"""
SHARED_BIBJSON = {
    "objects" : [
        "bibjson"
    ],
    "structs" : {
        "bibjson" : {
            "fields" : {
                "title" : {"coerce" : "unicode"},
            },
            "lists" : {
                "identifier" : {"contains" : "object"},
                "keywords" : {"contains" : "field", "coerce" : "unicode"},
                "link" : {"contains" : "object"},
                "subject" : {"contains" : "object"},
            },
            "structs" : {
                "identifier" : {
                    "fields" : {
                        "type" : {"coerce" : "unicode"},
                        "id" : {"coerce" : "unicode"}
                    }
                },
                "link" : {
                    "fields" : {
                        "type" : {"coerce" : "unicode"},
                        "url" : {"coerce" : "unicode"},
                        "content_type" : {"coerce" : "unicode"}
                    }
                },
                "subject" : {
                    "fields" : {
                        "scheme" : {"coerce" : "unicode"},
                        "term" : {"coerce" : "unicode"},
                        "code" : {"coerce" : "unicode"}
                    }
                }
            }
        }
    }
}

JOURNAL_BIBJSON_EXTENSION = {
    "objects" : [
        "bibjson"
    ],
    "structs" : {
        "bibjson" : {
            "fields" : {
                "active" : {"coerce" : "bool"},
                "alternative_title" : {"coerce" : "unicode"},
                "country" : {"coerce" : "unicode"},
                "publisher" : {"coerce" : "unicode"},
                "provider" : {"coerce" : "unicode"},
                "institution" : {"coerce" : "unicode"},
                "apc_url" : {"coerce" : "unicode"},
                "submission_charges_url" : {"coerce" : "unicode"},
                "allows_fulltext_indexing" : {"coerce" : "bool"},
                "publication_time" : {"coerce" : "integer"},
                "author_pays" : {"coerce" : "unicode"},
                "author_pays_url" : {"coerce" : "unicode"},
                "discontinued_date" : {"coerce" : "bigenddate"}
            },
            "lists" : {
                "language" : {"contains" : "field", "coerce" : "unicode_upper"},
                "deposit_policy" : {"contains" : "field", "coerce" : "unicode"},
                "persistent_identifier_scheme" : {"contains" : "field", "coerce" : "unicode"},
                "format" : {"contains" : "field", "coerce" : "unicode"},
                "license" : {"contains" : "object"},
                "is_replaced_by" : {"contains" : "field", "coerce" : "unicode"},
                "replaces" : {"contains" : "field", "coerce" : "unicode"}
            },
            "objects" : [
                "oa_start",
                "oa_end",
                "apc",
                "submission_charges",
                "archiving_policy",
                "editorial_review",
                "plagiarism_detection",
                "article_statistics",
                "author_copyright",
                "author_publishing_rights"
            ],

            "structs" : {
                "oa_start" : {
                    "fields" : {
                        "year" : {"coerce" : "integer"},
                        "volume" : {"coerce" : "unicode"},
                        "number" : {"coerce" : "unicode"}
                    }
                },
                "oa_end" : {
                    "fields" : {
                        "year" : {"coerce" : "integer"},
                        "volume" : {"coerce" : "unicode"},
                        "number" : {"coerce" : "unicode"}
                    }
                },
                "apc" : {
                    "fields" : {
                        "currency" : {"coerce" : "unicode"},
                        "average_price" : {"coerce" : "integer"}
                    }
                },
                "submission_charges" : {
                    "fields" : {
                        "currency" : {"coerce" : "unicode"},
                        "average_price" : {"coerce" : "integer"}
                    }
                },
                "archiving_policy" : {
                    "fields" : {
                        "other" : {"coerce" : "unicode"},
                        "nat_lib" : {"coerce" : "unicode"},
                        "url" : {"coerce" : "unicode"}
                    },
                    "lists" : {
                        "known" : {"contains" : "field", "coerce" : "unicode"}
                    }
                },
                "editorial_review" : {
                    "fields" : {
                        "process" : {"coerce" : "unicode"},
                        "url" : {"coerce" : "unicode"}
                    }
                },
                "plagiarism_detection" : {
                    "fields" : {
                        "detection" : {"coerce" : "bool"},
                        "url" : {"coerce" : "unicode"}
                    }
                },
                "article_statistics" : {
                    "fields" : {
                        "statistics" : {"coerce" : "bool"},
                        "url" : {"coerce" : "unicode"}
                    }
                },
                "author_copyright" : {
                    "fields" : {
                        "copyright" : {"coerce" : "unicode"},
                        "url" : {"coerce" : "unicode"}
                    }
                },
                "author_publishing_rights" : {
                    "fields" : {
                        "publishing_rights" : {"coerce" : "unicode"},
                        "url" : {"coerce" : "unicode"}
                    }
                },
                "license" : {
                    "fields" : {
                        "title" : {"coerce" : "unicode"},
                        "type" : {"coerce" : "unicode"},
                        "url" : {"coerce" : "unicode"},
                        "version" : {"coerce" : "unicode"},
                        "open_access" : {"coerce" : "bool"},
                        "BY" : {"coerce" : "bool"},
                        "NC" : {"coerce" : "bool"},
                        "ND" : {"coerce" : "bool"},
                        "SA" : {"coerce" : "bool"},
                        "embedded" : {"coerce" : "bool"},
                        "embedded_example_url" : {"coerce" : "unicode"}
                    }
                }
            }
        }
    }
}
"""