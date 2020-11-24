from copy import deepcopy
from doajtest.fixtures.v2.journals import JOURNAL_SOURCE

class BibJSONFixtureFactory(object):
    @classmethod
    def generic_bibjson(cls):
        return deepcopy(GENERIC)

    @classmethod
    def journal_bibjson(cls):
        return deepcopy(JOURNAL_SOURCE.get("bibjson"))

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
            "orcid_id" : "https://orcid.org/0000-0001-1234-1234"
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
