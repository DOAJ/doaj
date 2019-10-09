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
                "keywords" : {"contains" : "field", "coerce" : "str"},
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
                        "known" : {"contains" : "field", "coerce" : "str"}
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