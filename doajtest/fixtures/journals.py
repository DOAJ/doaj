# -*- coding: UTF-8 -*-
from copy import deepcopy
import rstr

from doajtest.fixtures.common import EDITORIAL, SUBJECT, NOTES, OWNER, SEAL

from portality.formcontext import forms

class JournalFixtureFactory(object):
    @staticmethod
    def make_journal_source(in_doaj=False, include_obsolete_fields=False):
        template = deepcopy(JOURNAL_SOURCE)
        if include_obsolete_fields:
            template['bibjson']['oa_start'] = JOURNAL_OBSOLETE_OA_START
            template['bibjson']['oa_end'] = JOURNAL_OBSOLETE_OA_END
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
            template["bibjson"]['identifier'] = [
                {"type": "pissn", "id": rstr.xeger(forms.ISSN_REGEX)},
                {"type": "eissn", "id": rstr.xeger(forms.ISSN_REGEX)}
            ]
            template['admin']['in_doaj'] = in_doaj
            template['bibjson']['active'] = in_doaj  # legacy field?
            template['bibjson']['title'] = 'Test Title {}'.format(i)
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

    @staticmethod
    def make_bulk_edit_data():
        return deepcopy(JOURNAL_BULK_EDIT)

    @staticmethod
    def csv_headers():
        return deepcopy(CSV_HEADERS)

    @staticmethod
    def question_answers():
        return deepcopy(JOURNAL_QUESTION_ANSWERS)

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
        "replaces" : ["1111-1111"],
        "is_replaced_by" : ["2222-2222"],
        "discontinued_date" : "2001-01-01",
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
            "known" : ["LOCKSS", "CLOCKSS"],
            "other" : "A safe place",
            "nat_lib" : "Trinity",
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
            "copyright": "True",
            "url": "http://copyright.com"
        },
        "author_publishing_rights": {
            "publishing_rights": "True",
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
            {"note": "Second Note", "date": "2014-05-22T00:00:00Z"},
            {"note": "First Note", "date": "2014-05-21T14:02:45Z"}
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
        "seal": True,
        "current_application" : "qwertyuiop",
        "related_applications" : [
            {"application_id" : "asdfghjkl", "date_accepted" : "2018-01-01T00:00:00Z"},
            {"application_id" : "zxcvbnm"}
        ]
    }
}

JOURNAL_OBSOLETE_OA_START = {
    "volume": "1",
    "number": "1",
    "year": "1980",  # some journals do have those as strings in live
}

JOURNAL_OBSOLETE_OA_END = {  # the entire oa_end is obsolete
    "volume": "10",
    "number": "10",
    "year": "1985",
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
    "copyright": "True",
    "copyright_url": "http://copyright.com",
    "publishing_rights": "True",
    "publishing_rights_url": "http://publishing.rights",
    "replaces" : ["1111-1111"],
    "is_replaced_by" : ["2222-2222"],
    "discontinued_date" : "2001-01-01"
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
                "allows_fulltext_indexing": {"coerce": "bool"},
                "alternative_title": {"coerce": "unicode"},
                "apc_url": {"coerce": "url"},
                "country": {"coerce": "country_code"},
                "institution": {"coerce": "unicode"},
                "provider": {"coerce": "unicode"},
                "publication_time": {"coerce": "integer"},
                "publisher": {"coerce": "unicode"},
                "submission_charges_url": {"coerce": "url"},
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
                        "url": {"coerce": "url"},
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
                        "url": {"coerce": "url"},
                    }
                },

                "author_copyright": {
                    "fields": {
                        "copyright": {"coerce": "unicode"},
                        "url": {"coerce": "url"},
                    }
                },

                "author_publishing_rights": {
                    "fields": {
                        "publishing_rights": {"coerce": "unicode"},
                        "url": {"coerce": "url"},
                    }
                },

                "editorial_review": {
                    "fields": {
                        "process": {"coerce": "unicode", "allowed_values" : ["Editorial review", "Peer review", "Blind peer review", "Double blind peer review", "Open peer review", "None"]},
                        "url": {"coerce": "url"},
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
                        "url": {"coerce": "url"},
                        "version": {"coerce": "unicode"},
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
                        "type": {"coerce": "unicode"},
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
                        "scheme": {"coerce": "unicode"},
                        "term": {"coerce": "unicode"},
                        "code": {"coerce": "unicode"},
                    }
                }
            }
        }
    }
}

JOURNAL_BULK_EDIT =  {
    "publisher": "Test Publisher",
    "doaj_seal": True,
    "country": "DZ",
    "platform": "HighWire",
    "contact_email": "richard@example.com",
    "owner": "testuser",
    "contact_name": "Test User"
}


CSV_HEADERS = [
    'Journal title',
    'Journal URL',
    'Alternative title',
    'Journal ISSN (print version)',
    'Journal EISSN (online version)',
    'Publisher',
    'Society or institution',
    'Platform, host or aggregator',
    'Country of publisher',
    'Journal article processing charges (APCs)',
    'APC information URL',
    'APC amount',
    'Currency',
    'Journal article submission fee',
    'Submission fee URL',
    'Submission fee amount',
    'Submission fee currency',
    'Number of articles published in the last calendar year',
    'Number of articles information URL',
    'Journal waiver policy (for developing country authors etc)',
    'Waiver policy information URL',
    'Digital archiving policy or program(s)',
    'Archiving: national library',
    'Archiving: other',
    'Archiving infomation URL',
    'Journal full-text crawl permission',
    'Permanent article identifiers',
    'Journal provides download statistics',
    'Download statistics information URL',
    'First calendar year journal provided online Open Access content',
    'Full text formats',
    'Keywords',
    'Full text language',
    'URL for the Editorial Board page',
    'Review process',
    'Review process information URL',
    "URL for journal's aims & scope",
    "URL for journal's instructions for authors",
    'Journal plagiarism screening policy',
    'Plagiarism information URL',
    'Average number of weeks between submission and publication',
    "URL for journal's Open Access statement",
    'Machine-readable CC licensing information embedded or displayed in articles',
    'URL to an example page with embedded licensing information',
    'Journal license',
    'License attributes',
    'URL for license terms',
    'Does this journal allow unrestricted reuse in compliance with BOAI?',
    'Deposit policy directory',
    'Author holds copyright without restrictions',
    'Copyright information URL',
    'Author holds publishing rights without restrictions',
    'Publishing rights information URL',
    'DOAJ Seal',
    'Tick: Accepted after March 2014',
    'Added on Date',
    'Subjects',
    "Number of Article Records",
    "Most Recent Article Added"
]

JOURNAL_QUESTION_ANSWERS = [
    'The Title',
    'http://journal.url',
    'Alternative Title',
    '1234-5678',
    '9876-5432',
    'The Publisher',
    'Society Institution',
    'Platform Host Aggregator',
    'United States',
    'Yes',
    'http://apc.com',
    '2',
    'GBP - Pound Sterling',
    'Yes',
    'http://submission.com',
    '4',
    'USD - US Dollar',
    '',
    '',
    'Yes',
    'http://waiver.policy',
    'LOCKSS, CLOCKSS',
    'Trinity',
    'A safe place',
    'http://digital.archiving.policy',
    'Yes',
    'DOI, ARK, PURL',
    'Yes',
    'http://download.stats',
    '1980',
    'HTML, XML, Wordperfect',
    'word, key',
    'English, French',
    'http://editorial.board',
    'Open peer review',
    'http://review.process',
    'http://aims.scope',
    'http://author.instructions.com',
    'Yes',
    'http://plagiarism.screening',
    '8',
    'http://oa.statement',
    'Yes',
    'http://licence.embedded',
    'CC MY',
    'Attribution, No Commercial Usage',
    'http://licence.url',
    'Yes',
    'Sherpa/Romeo, Store it',
    'True',
    'http://copyright.com',
    'True',
    'http://publishing.rights'
]