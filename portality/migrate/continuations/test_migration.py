from portality.migrate.continuations.restructure_archiving_policy import migrate
from portality import models

OLD_JOURNAL_FORMAT = {
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


njf = migrate(OLD_JOURNAL_FORMAT)

assert isinstance(njf, models.Journal)
ap = njf.data.get("bibjson").get("archiving_policy")
assert ap.get("known") == ["LOCKSS", "CLOCKSS"]
assert ap.get("other") == "A safe place"
assert ap.get("nat_lib") == "Trinity"