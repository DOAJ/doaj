from doajtest.helpers import DoajTestCase
from portality.migrate.continuations import restructure_archiving_policy
from portality.migrate.continuations import extract_continuations
from portality import models
from copy import deepcopy
import time

class TestMigration(DoajTestCase):

    def test_01_archiving_policy(self):
        njf = restructure_archiving_policy.migrate(OLD_JOURNAL_FORMAT)

        assert isinstance(njf, models.Journal)
        ap = njf.data.get("bibjson").get("archiving_policy")
        assert ap.get("known") == ["LOCKSS", "CLOCKSS"]
        assert ap.get("other") == "A safe place"
        assert ap.get("nat_lib") == "Trinity"

    def test_02_continuations(self):
        result = extract_continuations.migrate(WITH_HISTORY)
        assert result.get("bibjson", {}).get("replaces") == ["9999-9999", "8888-8888"]

        time.sleep(2)
        nine = models.Journal.find_by_issn("9999-9999")
        assert len(nine) == 1
        one = models.Journal.find_by_issn("1111-1111")
        assert len(one) == 1


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

WITH_HISTORY = deepcopy(OLD_JOURNAL_FORMAT)
WITH_HISTORY["history"] = [
    {
        "date" : "2001-01-01T00:00:00Z",
        "replaces" : ["1111-1111", "2222-2222"],
        "isreplacedby" : ["1234-5678", "9876-5432"],
        "bibjson" : {
            "identifier": [
                {"type": "pissn", "id": "9999-9999"},
                {"type": "eissn", "id": "8888-8888"},
            ],
            "title" : "Last One"
        }
    },
    {
        "date" : "2000-01-01T00:00:00Z",
        "isreplacedby" : ["9999-9999", "8888-8888"],
        "bibjson" : {
            "identifier": [
                {"type": "pissn", "id": "1111-1111"},
                {"type": "eissn", "id": "2222-2222"},
            ],
            "title" : "First One"
        }
    }
]