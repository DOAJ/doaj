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
            "license_display": ["Embed", "Display"],
            "license_display_example_url": "http://licence.embedded",
            "orcid": True,
            "i4oc_open_citations": False
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
            "review_process": ["Open peer review", "some bloke checks it out"],
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
                "type": "Publisher's own license",
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
            "scheme": ["DOI", "ARK", "PURL", "PIDMachine"],
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
            "license_terms": "http://licence.url"
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
    "alternative_title": "Alternative Title",
    "apc" : "y",
    "apc_charges" : [
        {
            "apc_max" : 2,
            "apc_currency" : "GBP"
        }
    ],
    "apc_url" : "http://apc.com",
    "preservation_service" : ["LOCKSS", "CLOCKSS"],
    "preservation_service_other" : "A safe place",
    "preservation_service_library" : ["Trinity", "Imperial"],
    "preservation_service_url" : "http://digital.archiving.policy",
    "copyright_author_retains" : "y",
    "copyright_url" : "http://copyright.com",
    "publisher" : {
        "publisher_country" : "US",
        "publisher_name" : "The Publisher"
    },
    "deposit_policy" : ["Sherpa/Romeo"],
    "deposit_policy_other" : "Store it",
    "review_process" : ["Open peer review"],
    "review_process_other" : "some bloke checks it out",
    "review_url" : "http://review.process",
    "pissn": "1234-5678",
    "eissn": "9876-5432",
    "institution" : {
        "institution_name" : "Society Institution",
        "institution_country" : "US"
    },
    "keywords": ["word", "key"],
    "language": ["EN", "FR"],
    "license_attributes" : ["BY", "NC"],
    "license_display" : ["Embed", "Display"],
    "license_display_example_url": "http://licence.embedded",
    "boai": True,
    "license": "Publisher's own license",
    "license_terms_url" : "http://licence.url",
    "oa_statement_url" : "http://oa.statement",
    "journal_url" : "http://journal.url",
    "aims_scope_url" : "http://aims.scope",
    "editorial_board_url" : "http://editorial.board",
    "author_instructions_url" : "http://author.instructions.com",
    "waiver_url" : "http://waiver.policy",
    "persistent_identifiers" : ["DOI", "ARK", "PURL"],
    "persistent_identifiers_other" : "PIDMachine",
    "plagiarism_detection" : "y",
    "plagiarism_url" : "http://plagiarism.screening",
    "publication_time_weeks" : 8,
    "other_charges_url" : "http://other.charges",
    "title": "The Title",
    "has_other_charges" : "y",
    "has_waiver" : "y",
    "orcid_ids" : "y",
    "open_citations" : "n",
    "deposit_policy_url" : "http://deposit.policy"

    #"contact_name": "Contact Name",
    #"contact_email": "contact@email.com",
    #"confirm_contact_email": "contact@email.com",
    #"replaces": ["1111-1111"],
    #"is_replaced_by": ["2222-2222"],
    #"discontinued_date": "2001-01-01"
}

JOURNAL_LEGACY = {
    "author_pays": "Y",
    "author_pays_url": "http://author.pays",
    "oa_end_year": 1991
}

# assemble the form as a regular object

JOURNAL_FORMINFO = deepcopy(JOURNAL_INFO)
JOURNAL_FORMINFO.update(EDITORIAL)
JOURNAL_FORMINFO.update(SEAL)
JOURNAL_FORMINFO.update(SUBJECT)
JOURNAL_FORMINFO.update(NOTES)
JOURNAL_FORMINFO.update(OWNER)
JOURNAL_FORMINFO.update(JOURNAL_LEGACY)

# restructure the form as the text would be returned from the site

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

inst = JOURNAL_FORM["institution"]
del JOURNAL_FORM["institution"]
JOURNAL_FORM["institution-institution_name"] = inst["institution_name"]
JOURNAL_FORM["institution-institution_country"] = inst["institution_country"]

pub = JOURNAL_FORM["publisher"]
del JOURNAL_FORM["publisher"]
JOURNAL_FORM["publisher-publisher_name"] = pub["publisher_name"]
JOURNAL_FORM["publisher-publisher_country"] = pub["publisher_country"]

apcs = JOURNAL_FORM["apc_charges"]
del JOURNAL_FORM["apc_charges"]
i = 0
for a in apcs:
    currkey = "apc_charges-" + str(i) + "-apc_currency"
    maxkey = "apc_charges-" + str(i) + "-apc_max"
    JOURNAL_FORM[currkey] = a.get("apc_currency")
    JOURNAL_FORM[maxkey] = a.get("apc_max")
    i += 1


JOURNAL_APIDO_STRUCT = {
    "objects": ["bibjson", "admin"],
    "fields": {
        "id": {"coerce": "unicode"},
        "created_date": {"coerce": "utcdatetime"},
        "last_updated": {"coerce": "utcdatetime"},
        'last_manual_update': {'coerce': 'utcdatetime'}
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
