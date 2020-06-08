# -*- coding: UTF-8 -*-
from copy import deepcopy
import rstr

from doajtest.fixtures.common import EDITORIAL, SUBJECT, NOTES, OWNER, SEAL

from portality.formcontext import forms


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
            template["bibjson"]["pissn"] = rstr.xeger(forms.ISSN_REGEX)
            template["bibjson"]["eissn"] = rstr.xeger(forms.ISSN_REGEX)
            template['admin']['in_doaj'] = in_doaj
            template['bibjson']['title'] = 'Test Title {}'.format(i)
            journal_sources.append(deepcopy(template))
        return journal_sources

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
    "id": "id",
    "created_date": "2000-01-01T00:00:00Z",
    "last_manual_update": "2001-01-01T00:00:00Z",
    "last_updated": "2002-01-01T00:00:00Z",
    "admin": {
        "bulk_upload": "bulk_1234567890",
        "contact":
            {
                "email": "contact@example.com",
                "name": "Example Contact"
            },
        "current_application": "qwertyuiop",
        "editor_group": "editorgroup",
        "editor": "associate",
        "in_doaj": False,
        "notes": [
            {"note": "Second Note", "date": "2014-05-22T00:00:00Z", "id": "abcd"},
            {"note": "First Note", "date": "2014-05-21T14:02:45Z", "id": "1234"}
        ],
        "owner": "Owner",
        "related_applications": [
            {"application_id": "asdfghjkl", "date_accepted": "2018-01-01T00:00:00Z"},
            {"application_id": "zxcvbnm"}
        ],
        "seal": True,
        "ticked": True
    },
    "bibjson": {
        "alternative_title": "Alternative Title",
        "apc": {
            "max": [
                {"currency": "GBP", "price": 2}
            ],
            "url": "http://apc.com",
            "has_apc": True
        },
        "article": {
            "license_display": ["embed", "display"],
            "license_display_example_url": "http://licence.embedded",
            "orcid": True,
            "i4oc_open_citations": True
        },
        "boai": True,
        "copyright": {
            "author_retains": True,
            "url": "http://copyright.com"
        },
        "deposit_policy": {
            "has_policy" : True,
            "is_registered": True,
            "service": ["Sherpa/Romeo", "Store it"],
            "url": "http://deposit.policy"
        },
        "discontinued_date": "2010-01-01",
        "editorial": {
            "review_process": ["Open peer review"],
            "review_url": "http://review.process",
            "board_url": "http://editorial.board"
        },
        "eissn": "9876-5432",
        "is_replaced_by": ["2222-2222"],
        "institution": {
            "name": "Society Institution",
            "country": "US"
        },
        "keywords": ["word", "key"],
        "language": ["EN", "FR"],
        "license": [
            {
                "type": "CC MY",
                "BY": True,
                "NC": True,
                "ND": False,
                "SA": False,
                "url": "http://licence.url"
            }
        ],
        "other_charges": {
            "has_other_charges" : True,
            "url": "http://other.charges"
        },
        "pid_scheme": {
            "scheme": ["DOI", "ARK", "PURL"],
        },
        "pissn": "1234-5678",
        "plagiarism": {
            "detection": True,
            "url": "http://plagiarism.screening"
        },
        "preservation": {
            "service": ["LOCKSS", "CLOCKSS", "A safe place"],
            "national_library": ["Trinity", "Imperial"],
            "url": "http://digital.archiving.policy"
        },
        "publication_time_weeks": 8,
        "publisher": {
            "name": "The Publisher",
            "country": "US"
        },
        "ref": {
            "oa_statement": "http://oa.statement",
            "journal": "http://journal.url",
            "aims_scope": "http://aims.scope",
            "author_instructions": "http://author.instructions.com",
            "license_terms": "http://license.terms"
        },
        "replaces": ["1111-1111"],
        "subject": [
            {"scheme": "LCC", "term": "Economic theory. Demography",
             "code": "HB1-3840"},
            {"scheme": "LCC", "term": "Social Sciences", "code": "H"}
        ],
        "title": "The Title",
        "waiver": {
            "has_waiver" : True,
            "url": "http://waiver.policy"
        }
    }
}

JOURNAL_INFO = {
    "title": "The Title",
    "url": "http://journal.url",
    "alternative_title": "Alternative Title",
    "pissn": "1234-5678",
    "eissn": "9876-5432",
    "publisher": "The Publisher",
    "institution": "Society Institution",
    "institution_country": "US",
    "platform": "Platform Host Aggregator",
    "contact_name": "Contact Name",
    "contact_email": "contact@email.com",
    "confirm_contact_email": "contact@email.com",
    "country": "US",
    "processing_charges": "True",
    "processing_charges_url": "http://apc.com",
    "processing_charges_amount": 2,
    "processing_charges_currency": "GBP",
    "submission_charges": "True",
    "submission_charges_url": "http://submission.com",
    "submission_charges_amount": 4,
    "submission_charges_currency": "USD",
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
    "replaces": ["1111-1111"],
    "is_replaced_by": ["2222-2222"],
    "discontinued_date": "2001-01-01"
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
        "last_updated": {"coerce": "utcdatetime"},
        'last_manual_update': {'coerce': 'utcdatetime'},
        "es_type": {"coerce": "unicode"}
    },
    "structs": {
        "admin": {
            "fields": {
                "in_doaj": {"coerce": "bool", "get__default": False},
                "ticked": {"coerce": "bool", "get__default": False},
                "seal": {"coerce": "bool", "get__default": False}}
        },
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
                        "url": {"coerce": "url"}
                    },
                    "lists": {
                        "national_library": {"coerce": "unicode"},
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

JOURNAL_BULK_EDIT = {
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
    # these are not in the journal model, only in the suggestion model
    # 'Number of articles published in the last calendar year',
    # 'Number of articles information URL',
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
    # these were the articles_last_year and associated URL which are not in the journal model
    # '',
    # '',
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
