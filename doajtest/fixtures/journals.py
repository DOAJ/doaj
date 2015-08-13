from copy import deepcopy

from doajtest.fixtures.common import EDITORIAL, SUBJECT, NOTES, OWNER, SEAL

class JournalFixtureFactory(object):
    @staticmethod
    def make_journal_source(in_doaj=False):
        template = deepcopy(JOURNAL_SOURCE)
        template['admin']['in_doaj'] = in_doaj
        return template

    @staticmethod
    def make_many_journal_sources(count=2, in_doaj=False):
        journal_sources = []
        for i in range(0, count):
            template = deepcopy(JOURNAL_SOURCE)
            template['id'] = 'journalid{0}'.format(i)
            # now some very quick and very dirty date generation
            fakemonth = i
            if fakemonth < 1:
                fakemonth = 1
            if fakemonth > 9:
                fakemonth = 9
            template['created_date'] = "2000-0{fakemonth}-01T00:00:00Z".format(fakemonth=fakemonth)
            template['identifier'] = [
                # not really proper ISSN format, but then 1234-5678 is not
                # a correct checksummed ISSN either. Need to write a nicer
                # faker module and just ask it for fake ISSNs, IDs, names, publishers, etc.
                {"type": "pissn", "id": "1234-{0}".format(i)},
                {"type": "eissn", "id": "{0}-5432".format(i)},
            ]
            template['admin']['in_doaj'] = in_doaj
            template['bibjson']['active'] = in_doaj  # legacy field?
            journal_sources.append(deepcopy(template))
        return journal_sources

    @staticmethod
    def make_journal_source_with_legacy_info():
        return deepcopy(JOURNAL_SOURCE_WITH_LEGACY_INFO)

    @staticmethod
    def make_journal_form():
        return deepcopy(JOURNAL_FORM)

    @staticmethod
    def make_journal_form_info():
        return deepcopy(JOURNAL_FORMINFO)

    @staticmethod
    def make_journal_apido_struct():
        return deepcopy(JOURNAL_APIDO_STRUCT)

JOURNAL_SOURCE = {
    "id": "abcdefghijk_journal",
    "created_date": "2000-01-01T00:00:00Z",
    "bibjson": {
        # "active" : true|false,
        "title": "The Title",
        "alternative_title": "Alternative Title",
        "identifier": [
            {"type": "pissn", "id": "1234-5678"},
            {"type": "eissn", "id": "9876-5432"},
        ],
        "keywords": ["word", "key"],
        "language": ["EN", "FR"],
        "country": "US",
        "publisher": "The Publisher",
        "provider": "Platform Host Aggregator",
        "institution": "Society Institution",
        "link": [
            {"type": "homepage", "url": "http://journal.url"},
            {"type": "waiver_policy", "url": "http://waiver.policy"},
            {"type": "editorial_board",
             "url": "http://editorial.board"},
            {"type": "aims_scope", "url": "http://aims.scope"},
            {"type": "author_instructions",
             "url": "http://author.instructions.com"},
            {"type": "oa_statement", "url": "http://oa.statement"}
        ],
        "subject": [
            {"scheme": "LCC", "term": "Economic theory. Demography",
             "code": "HB1-3840"},
            {"scheme": "LCC", "term": "Social Sciences", "code": "H"}
        ],

        "oa_start": {
            "year": 1980,
        },
        "apc_url" : "http://apc.com",
        "apc": {
            "currency": "GBP",
            "average_price": 2
        },
        "submission_charges_url" : "http://submission.com",
        "submission_charges": {
            "currency": "USD",
            "average_price": 4
        },
        "archiving_policy": {
            "policy": [
                "LOCKSS", "CLOCKSS",
                ["A national library", "Trinity"],
                ["Other", "A safe place"]
            ],
            "url": "http://digital.archiving.policy"
        },
        "editorial_review": {
            "process": "Open peer review",
            "url": "http://review.process"
        },
        "plagiarism_detection": {
            "detection": True,
            "url": "http://plagiarism.screening"
        },
        "article_statistics": {
            "statistics": True,
            "url": "http://download.stats"
        },
        "deposit_policy": ["Sherpa/Romeo", "Store it"],
        "author_copyright": {
            "copyright": "Sometimes",
            "url": "http://copyright.com"
        },
        "author_publishing_rights": {
            "publishing_rights": "Occasionally",
            "url": "http://publishing.rights"
        },
        "allows_fulltext_indexing": True,
        "persistent_identifier_scheme": ["DOI", "ARK", "PURL"],
        "format": ["HTML", "XML", "Wordperfect"],
        "publication_time": 8,
        "license": [
            {
                "title": "CC MY",
                "type": "CC MY",
                "url": "http://licence.url",
                "open_access": True,
                "BY": True,
                "NC": True,
                "ND": False,
                "SA": False,
                "embedded": True,
                "embedded_example_url": "http://licence.embedded"
            }
        ]
    },
    "admin": {
        "notes": [
            {"note": "First Note", "date": "2014-05-21T14:02:45Z"},
            {"note": "Second Note", "date": "2014-05-22T00:00:00Z"}
        ],
        "contact": [
            {
                "email": "contact@email.com",
                "name": "Contact Name"
            }
        ],
        "owner": "Owner",
        "editor_group": "editorgroup",
        "editor": "associate",
        "seal": True
    }
}

JOURNAL_SOURCE_WITH_LEGACY_INFO = deepcopy(JOURNAL_SOURCE)
JOURNAL_SOURCE_WITH_LEGACY_INFO['bibjson']["author_pays"] = "Y"
JOURNAL_SOURCE_WITH_LEGACY_INFO['bibjson']["author_pays_url"] = "http://author.pays"
JOURNAL_SOURCE_WITH_LEGACY_INFO['bibjson']["oa_end"] = {}
JOURNAL_SOURCE_WITH_LEGACY_INFO['bibjson']["oa_end"]["year"] = 1991

JOURNAL_INFO = {
    "title": "The Title",
    "url": "http://journal.url",
    "alternative_title": "Alternative Title",
    "pissn": "1234-5678",
    "eissn": "9876-5432",
    "publisher": "The Publisher",
    "society_institution": "Society Institution",
    "platform": "Platform Host Aggregator",
    "contact_name": "Contact Name",
    "contact_email": "contact@email.com",
    "confirm_contact_email": "contact@email.com",
    "country": "US",
    "processing_charges": "True",
    "processing_charges_url" : "http://apc.com",
    "processing_charges_amount": 2,
    "processing_charges_currency": "GBP",
    "submission_charges": "True",
    "submission_charges_url" : "http://submission.com",
    "submission_charges_amount": 4,
    "submission_charges_currency": "USD",
    "waiver_policy": "True",
    "waiver_policy_url": "http://waiver.policy",
    "digital_archiving_policy": ["LOCKSS", "CLOCKSS",
                                 "A national library", "Other"],
    "digital_archiving_policy_other": "A safe place",
    "digital_archiving_policy_library": "Trinity",
    "digital_archiving_policy_url": "http://digital.archiving.policy",
    "crawl_permission": "True",
    "article_identifiers": ["DOI", "ARK", "Other"],
    "article_identifiers_other": "PURL",
    "download_statistics": "True",
    "download_statistics_url": "http://download.stats",
    "first_fulltext_oa_year": 1980,
    "fulltext_format": ["HTML", "XML", "Other"],
    "fulltext_format_other": "Wordperfect",
    "keywords": ["word", "key"],
    "languages": ["EN", "FR"],
    "editorial_board_url": "http://editorial.board",
    "review_process": "Open peer review",
    "review_process_url": "http://review.process",
    "aims_scope_url": "http://aims.scope",
    "instructions_authors_url": "http://author.instructions.com",
    "plagiarism_screening": "True",
    "plagiarism_screening_url": "http://plagiarism.screening",
    "publication_time": 8,
    "oa_statement_url": "http://oa.statement",
    "license_embedded": "True",
    "license_embedded_url": "http://licence.embedded",
    "license": "Other",
    "license_other": "CC MY",
    "license_checkbox": ["BY", "NC"],
    "license_url": "http://licence.url",
    "open_access": "True",
    "deposit_policy": ["Sherpa/Romeo", "Other"],
    "deposit_policy_other": "Store it",
    "copyright": "Other",
    "copyright_other": "Sometimes",
    "copyright_url": "http://copyright.com",
    "publishing_rights": "Other",
    "publishing_rights_other": "Occasionally",
    "publishing_rights_url": "http://publishing.rights"
}

JOURNAL_LEGACY = {
    "author_pays": "Y",
    "author_pays_url": "http://author.pays",
    "oa_end_year": 1991
}

JOURNAL_FORMINFO = deepcopy(JOURNAL_INFO)
JOURNAL_FORMINFO.update(EDITORIAL)
JOURNAL_FORMINFO.update(SEAL)
JOURNAL_FORMINFO.update(SUBJECT)
JOURNAL_FORMINFO.update(NOTES)
JOURNAL_FORMINFO.update(OWNER)
JOURNAL_FORMINFO.update(JOURNAL_LEGACY)

JOURNAL_FORM = deepcopy(JOURNAL_FORMINFO)
JOURNAL_FORM["keywords"] = ",".join(JOURNAL_FORM["keywords"])

notes = JOURNAL_FORM["notes"]
del JOURNAL_FORM["notes"]
i = 0
for n in notes:
    notekey = "notes-" + str(i) + "-note"
    datekey = "notes-" + str(i) + "-date"
    JOURNAL_FORM[notekey] = n.get("note")
    JOURNAL_FORM[datekey] = n.get("date")
    i += 1

JOURNAL_APIDO_STRUCT = {
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
                "title": {"coerce": "unicode"},
                "alternative_title": {"coerce": "unicode"},
                "country": {"coerce": "unicode"},
                "publisher": {"coerce": "unicode"},
                "provider": {"coerce": "unicode"},
                "institution": {"coerce": "unicode"},
                "apc_url": {"coerce": "unicode"},
                "submission_charges_url": {"coerce": "unicode"},
                "allows_fulltext_indexing": {"coerce": "bool"},
                "publication_time": {"coerce": "integer"},
            },
            "objects": [
                "oa_start",
                "oa_end",
                "apc",
                "submission_charges",
                "archiving_policy",
                "editorial_review",
                "plagiarism_detection",
                "article_statistics",
                "author_copyright",
                "author_publishing_rights",
            ],
            "lists": {
                "identifier": {"contains": "object"},
                "keywords": {"coerce": "unicode", "contains": "field"},
                "language": {"coerce": "unicode", "contains": "field"},
                "link": {"contains": "object"},
                "subject": {"contains": "object"},
                "deposit_policy": {"coerce": "unicode", "contains": "field"},
                "persistent_identifier_scheme": {"coerce": "unicode", "contains": "field"},
                "format": {"coerce": "unicode", "contains": "field"},
                "license": {"contains": "object"},
            },
            "required": [],
            "structs": {
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
                "apc": {
                    "fields": {
                        "currency": {"coerce": "unicode"},
                        "average_price": {"coerce": "integer"}
                    }
                },
                "submission_charges": {
                    "fields": {
                        "currency": {"coerce": "unicode"},
                        "average_price": {"coerce": "integer"}
                    }
                },
                "archiving_policy": {
                    "fields": {
                        "url": {"coerce": "unicode"},
                    },
                    "lists": {
                        "policy": {"coerce": "unicode", "contains": "field"},
                    }
                },
                "editorial_review": {
                    "fields": {
                        "process": {"coerce": "unicode"},
                        "url": {"coerce": "unicode"},
                    }
                },
                "plagiarism_detection": {
                    "fields": {
                        "detection": {"coerce": "bool"},
                        "url": {"coerce": "unicode"},
                    }
                },
                "article_statistics": {
                    "fields": {
                        "detection": {"coerce": "bool"},
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
                "identifier": {
                    "fields": {
                        "type": {"coerce": "unicode"},
                        "id": {"coerce": "unicode"},
                    }
                },
                "link": {
                    "fields": {
                        "type": {"coerce": "unicode"},
                        "url": {"coerce": "unicode"},
                    }
                },
                "subject": {
                    "fields": {
                        "scheme": {"coerce": "unicode"},
                        "term": {"coerce": "unicode"},
                        "code": {"coerce": "unicode"},
                    }
                },
                "license": {
                    "fields": {
                        "title": {"coerce": "unicode"},
                        "type": {"coerce": "unicode"},
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
            }
        }
    }
}