# -*- coding: UTF-8 -*-
from copy import deepcopy
import rstr

from doajtest.fixtures.v2.common import EDITORIAL_FORM_EXPANDED, SUBJECT_FORM_EXPANDED, NOTES_FORM_EXPANDED, \
    OWNER_FORM_EXPANDED, SEAL_FORM_EXPANDED, JOURNAL_LIKE_BIBJSON, JOURNAL_LIKE_BIBJSON_FORM_EXPANDED

from portality.forms.utils import expanded2compact
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
        return deepcopy(JOURNAL_FORM_EXPANDED)

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
    "bibjson": JOURNAL_LIKE_BIBJSON
}

JOURNAL_FORM_EXPANDED = {}
JOURNAL_FORM_EXPANDED.update(JOURNAL_LIKE_BIBJSON_FORM_EXPANDED)
JOURNAL_FORM_EXPANDED.update(EDITORIAL_FORM_EXPANDED)
JOURNAL_FORM_EXPANDED.update(SEAL_FORM_EXPANDED)
JOURNAL_FORM_EXPANDED.update(SUBJECT_FORM_EXPANDED)
JOURNAL_FORM_EXPANDED.update(NOTES_FORM_EXPANDED)
JOURNAL_FORM_EXPANDED.update(OWNER_FORM_EXPANDED)


JOURNAL_FORM = expanded2compact(JOURNAL_FORM_EXPANDED, {"keywords" : ","})


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
    "Journal title",
    "Journal URL",
    "Alternative title",
    "Journal ISSN (print version)",
    "Journal EISSN (online version)",
    "Publisher",
    "Country of publisher",
    "Society or institution",
    "Country of society or institution",
    "APC",
    "APC information URL",
    "APC amount",
    "Has other submission charges",
    "Other submission charges information URL",
    "Journal waiver policy (for developing country authors etc)",
    "Waiver policy information URL",
    "Preservations Services",
    "Preservation Service: national library",
    "Preservation information URL",
    "Permanent article identifiers",
    "Keywords",
    "Full text language",
    "URL for the Editorial Board page",
    "Review process",
    "Review process information URL",
    "URL for journal's aims & scope",
    "URL for journal's instructions for authors",
    "Journal plagiarism screening policy",
    "Plagiarism information URL",
    "Average number of weeks between submission and publication",
    "URL for journal's Open Access statement",
    "Machine-readable CC licensing information embedded or displayed in articles",
    "URL to an example page with embedded licensing information",
    "Journal license",
    "License attributes",
    "URL for license terms",
    "Does this journal allow unrestricted reuse in compliance with BOAI?",
    "Deposit policy directory",
    "URL for deposit policy",
    "Author holds copyright without restrictions",
    "Copyright information URL",
    "Article metadata includes ORCIDs",
    "Journal complies with I4OC standards for open citations",
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
    "United States",
    'Society Institution',
    "United States",
    'Yes',
    'http://apc.com',
    "2 GBP",
    'Yes',
    'http://other.charges',
    'Yes',
    'http://waiver.policy',
    'LOCKSS, CLOCKSS, A safe place',
    'Trinity; Imperial',
    'http://digital.archiving.policy',
    'DOI, ARK, PURL, PIDMachine',
    'word, key',
    'English, French',
    'http://editorial.board',
    'Open peer review, some bloke checks it out',
    'http://review.process',
    'http://aims.scope',
    'http://author.instructions.com',
    'Yes',
    'http://plagiarism.screening',
    '8',
    'http://oa.statement',
    'Embed, Display',
    'http://licence.embedded',
    "Publisher's own license",
    'Attribution, No Commercial Usage',
    'http://licence.url',
    'Yes',
    'Sherpa/Romeo, Store it',
    "http://deposit.policy",
    'Yes',
    'http://copyright.com',
    'Yes',
    'No'
]
