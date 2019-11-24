from copy import deepcopy

class BibJSONFixtureFactory(object):
    @classmethod
    def generic_bibjson(cls):
        return deepcopy(GENERIC)

    @classmethod
    def journal_bibjson(cls):
        return deepcopy(JOURNAL)

    @classmethod
    def article_bibjson(cls):
        return deepcopy(ARTICLE)


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
    "replaces" : ["0000-0000"],
    "is_replaced_by" : ["9999-9999"],
    "discontinued_date" : "2001-01-01",

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
}

ARTICLE = {
    "title" : "Article Title",
    "identifier" : [
        {"type": "pissn", "id": "1234-5678"},
        {"type": "eissn", "id": "9876-5432"},
        {"type" : "doi", "id" : "10.1234/article"}
    ],
    "journal" : {
        "volume" : "No 10",
        "number" : "Iss. 4",
        "publisher" : "IEEE",
        "title" : "Journal of Things",
        "license" : [
            {
                "title" : "CC-BY",
                "type" : "CC-BY",
                "url" : "http://creativecommons.org/by/",
                "version" : "3.0",
                "open_access" : True
            }
        ],
        "language" : ["eng"],
        "country" : "GB",
        "issns" : ["1234-5678", "9876-5432"]
    },
    "year" : "1987",
    "month" : "4",
    "start_page" : "14",
    "end_page" : "15",
    "link" : [
        {
            "url" : "http://example.com/file",
            "type" : "fulltext",
            "content_type" : "application/pdf"
        }
    ],
    "abstract" : "Some text here",
    "author" : [
        {
            "name" : "Test",
            "affiliation" : "University of Life",
            "orcid_id" : "0000-0001-1234-1234"
        }
    ],
    "keywords" : ["key", "word"],
    "subject" : [
        {
            "scheme" : "LCC",
            "term" : "Medicine",
            "code" : "M"
        }
    ]
}
