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
