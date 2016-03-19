from copy import deepcopy

class BibJSONFixtureFactory(object):
    @classmethod
    def generic_bibjson(cls):
        return deepcopy(GENERIC)

    @classmethod
    def journal_bibjson(cls):
        return deepcopy(JOURNAL)


GENERIC = {
    "title": "The Title",
    "identifier": [
        {"type": "pissn", "id": "1234-5678"},
        {"type": "eissn", "id": "9876-5432"},
    ],
    "keywords": ["word", "key"],
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
    ]
}

JOURNAL = {
    "active" : True,
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
}