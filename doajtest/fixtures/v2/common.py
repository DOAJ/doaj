NOTES_FORM_EXPANDED = {
    'notes': [
        {'date': '2014-05-22T00:00:00Z', 'note': 'Second Note'},
        {'date': '2014-05-21T14:02:45Z', 'note': 'First Note'}
    ]
}

SUBJECT_FORM_EXPANDED = {
    "subject": ['HB1-3840', 'H']
}

OWNER_FORM_EXPANDED = {
    "owner": "publisher"
}

EDITORIAL_FORM_EXPANDED = {
    "editor_group": "editorgroup",
    "editor": "associate"
}

SEAL_FORM_EXPANDED = {
    "doaj_seal": False,
}

JOURNAL_LIKE_BIBJSON = {
    "alternative_title": "Alternative Title",
    "apc": {
        "max": [
            {"currency": "GBP", "price": 2}
        ],
        "url": "http://apc.com",
        "has_apc": True
    },
    "article": {
        "license_display": ["Embed"],
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
    "discontinued_date": "2001-01-01",
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
        "has_pid_scheme" : True,
        "scheme": ["DOI", "ARK", "PURL", "PIDMachine"],
    },
    "pissn": "1234-5678",
    "plagiarism": {
        "detection": True,
        "url": "http://plagiarism.screening"
    },
    "preservation": {
        "has_preservation" : True,
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
JOURNAL_LIKE_BIBJSON_FORM_EXPANDED = {
    "alternative_title": "Alternative Title",
    "apc" : "y",
    "apc_charges" : [
        {
            "apc_max" : 2,
            "apc_currency" : "GBP"
        }
    ],
    "apc_url" : "http://apc.com",
    "preservation_service" : ["LOCKSS", "CLOCKSS", "other", "national_library"],
    "preservation_service_other" : "A safe place",
    "preservation_service_library" : ["Trinity", "Imperial"],
    "preservation_service_url" : "http://digital.archiving.policy",
    "copyright_author_retains" : "y",
    "copyright_url" : "http://copyright.com",
    "publisher_country" : "US",
    "publisher_name" : "The Publisher",
    "deposit_policy" : ["Sherpa/Romeo", "other"],
    "deposit_policy_other" : "Store it",
    "review_process" : ["Open peer review", "other"],
    "review_process_other" : "some bloke checks it out",
    "review_url" : "http://review.process",
    "pissn": "1234-5678",
    "eissn": "9876-5432",
    "institution_name" : "Society Institution",
    "institution_country" : "US",
    "keywords": ["word", "key"],
    "language": ["EN", "FR"],
    "license_attributes" : ["BY", "NC"],
    "license_display" : "y",
    "license_display_example_url": "http://licence.embedded",
    "boai": "y",
    "license": ["Publisher's own license"],
    "license_terms_url" : "http://licence.url",
    "oa_statement_url" : "http://oa.statement",
    "journal_url" : "http://journal.url",
    "aims_scope_url" : "http://aims.scope",
    "editorial_board_url" : "http://editorial.board",
    "author_instructions_url" : "http://author.instructions.com",
    "waiver_url" : "http://waiver.policy",
    "persistent_identifiers" : ["DOI", "ARK", "PURL", "other"],
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
    "deposit_policy_url" : "http://deposit.policy",
    "continues": ["1111-1111"],
    "continued_by": ["2222-2222"],
    "discontinued_date": "2001-01-01"
}