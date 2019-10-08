SHARED_BIBJSON = {
    "objects" : [
        "bibjson"
    ],
    "structs" : {
        "bibjson" : {
            "fields" : {
                "title" : {"coerce" : "str"},
            },
            "lists" : {
                "identifier" : {"contains" : "object"},
                "keywords" : {"contains" : "field", "coerce" : "str"},
                "link" : {"contains" : "object"},
                "subject" : {"contains" : "object"},
            },
            "structs" : {
                "identifier" : {
                    "fields" : {
                        "type" : {"coerce" : "str"},
                        "id" : {"coerce" : "str"}
                    }
                },
                "link" : {
                    "fields" : {
                        "type" : {"coerce" : "str"},
                        "url" : {"coerce" : "str"},
                        "content_type" : {"coerce" : "str"}
                    }
                },
                "subject" : {
                    "fields" : {
                        "scheme" : {"coerce" : "str"},
                        "term" : {"coerce" : "str"},
                        "code" : {"coerce" : "str"}
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
                "alternative_title" : {"coerce" : "str"},
                "country" : {"coerce" : "str"},
                "publisher" : {"coerce" : "str"},
                "provider" : {"coerce" : "str"},
                "institution" : {"coerce" : "str"},
                "apc_url" : {"coerce" : "str"},
                "submission_charges_url" : {"coerce" : "str"},
                "allows_fulltext_indexing" : {"coerce" : "bool"},
                "publication_time" : {"coerce" : "integer"},
                "author_pays" : {"coerce" : "str"},
                "author_pays_url" : {"coerce" : "str"},
                "discontinued_date" : {"coerce" : "bigenddate"}
            },
            "lists" : {
                "language" : {"contains" : "field", "coerce" : "unicode_upper"},
                "deposit_policy" : {"contains" : "field", "coerce" : "str"},
                "persistent_identifier_scheme" : {"contains" : "field", "coerce" : "str"},
                "format" : {"contains" : "field", "coerce" : "str"},
                "license" : {"contains" : "object"},
                "is_replaced_by" : {"contains" : "field", "coerce" : "str"},
                "replaces" : {"contains" : "field", "coerce" : "str"}
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
                        "volume" : {"coerce" : "str"},
                        "number" : {"coerce" : "str"}
                    }
                },
                "oa_end" : {
                    "fields" : {
                        "year" : {"coerce" : "integer"},
                        "volume" : {"coerce" : "str"},
                        "number" : {"coerce" : "str"}
                    }
                },
                "apc" : {
                    "fields" : {
                        "currency" : {"coerce" : "str"},
                        "average_price" : {"coerce" : "integer"}
                    }
                },
                "submission_charges" : {
                    "fields" : {
                        "currency" : {"coerce" : "str"},
                        "average_price" : {"coerce" : "integer"}
                    }
                },
                "archiving_policy" : {
                    "fields" : {
                        "other" : {"coerce" : "str"},
                        "nat_lib" : {"coerce" : "str"},
                        "url" : {"coerce" : "str"}
                    },
                    "lists" : {
                        "known" : {"contains" : "field", "coerce" : "str"}
                    }
                },
                "editorial_review" : {
                    "fields" : {
                        "process" : {"coerce" : "str"},
                        "url" : {"coerce" : "str"}
                    }
                },
                "plagiarism_detection" : {
                    "fields" : {
                        "detection" : {"coerce" : "bool"},
                        "url" : {"coerce" : "str"}
                    }
                },
                "article_statistics" : {
                    "fields" : {
                        "statistics" : {"coerce" : "bool"},
                        "url" : {"coerce" : "str"}
                    }
                },
                "author_copyright" : {
                    "fields" : {
                        "copyright" : {"coerce" : "str"},
                        "url" : {"coerce" : "str"}
                    }
                },
                "author_publishing_rights" : {
                    "fields" : {
                        "publishing_rights" : {"coerce" : "str"},
                        "url" : {"coerce" : "str"}
                    }
                },
                "license" : {
                    "fields" : {
                        "title" : {"coerce" : "str"},
                        "type" : {"coerce" : "str"},
                        "url" : {"coerce" : "str"},
                        "version" : {"coerce" : "str"},
                        "open_access" : {"coerce" : "bool"},
                        "BY" : {"coerce" : "bool"},
                        "NC" : {"coerce" : "bool"},
                        "ND" : {"coerce" : "bool"},
                        "SA" : {"coerce" : "bool"},
                        "embedded" : {"coerce" : "bool"},
                        "embedded_example_url" : {"coerce" : "str"}
                    }
                }
            }
        }
    }
}