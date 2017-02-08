import os
from lxml import etree
from StringIO import StringIO
from copy import deepcopy

RESOURCES = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "unit", "resources")
ARTICLES = os.path.join(RESOURCES, "article_uploads.xml")


class ArticleFixtureFactory(object):

    @classmethod
    def _response_from_xpath(cls, xpath):
        with open(ARTICLES) as f:
            doc = etree.parse(f)
        records = doc.getroot()
        articles = records.xpath(xpath)
        nr = etree.Element("records")
        for a in articles:
            nr.append(a)
        out = etree.tostring(nr, encoding="UTF-8", xml_declaration=True)
        return StringIO(out)

    @classmethod
    def upload_2_issns_correct(cls):
        return cls._response_from_xpath("//record[journalTitle='2 ISSNs Correct']")

    @classmethod
    def upload_2_issns_ambiguous(cls):
        return cls._response_from_xpath("//record[journalTitle='2 ISSNs Ambiguous']")

    @classmethod
    def upload_1_issn_correct(cls):
        return cls._response_from_xpath("//record[journalTitle='PISSN Correct']")

    @classmethod
    def upload_1_issn_superlong_should_not_clip(cls):
        return cls._response_from_xpath("//record[journalTitle='PISSN Correct Superlong Abstract Expected to Not be Clipped']")

    @classmethod
    def upload_1_issn_superlong_should_clip(cls):
        return cls._response_from_xpath("//record[journalTitle='PISSN Correct Superlong Abstract Expected to be Clipped']")

    @staticmethod
    def make_article_source():
        return deepcopy(ARTICLE_SOURCE)
    
    @staticmethod
    def make_incoming_api_article():
        template = deepcopy(ARTICLE_SOURCE)
        template['bibjson']['journal']['start_page'] = template['bibjson']['start_page']
        template['bibjson']['journal']['end_page'] = template['bibjson']['end_page']
        del template['bibjson']['start_page']
        del template['bibjson']['end_page']
        return deepcopy(template)

    @staticmethod
    def make_article_apido_struct():
        return deepcopy(ARTICLE_STRUCT)

ARTICLE_SOURCE = {
    "id" : "abcdefghijk_article",
    "admin" : {
        "in_doaj" : True,
        "publisher_record_id" : "some_identifier",
        "upload_id" : "zyxwvutsrqpo_upload_id"
    },
    "bibjson" : {
        "title" : "Article Title",
        "identifier": [
            {"type" : "doi", "id" : "10.0000/SOME.IDENTIFIER"},
            {"type": "pissn", "id": "1234-5678"},
            {"type": "eissn", "id": "9876-5432"},
        ],
        "journal" : {
            "volume" : "1",
            "number" : "99",
            "publisher" : "The Publisher",
            "title" : "The Title",
            "license" : [
                {
                    "title" : "CC BY",
                    "type" : "CC BY",
                    "url" : "http://license.example.com",
                    "version" : "1.0",
                    "open_access": True,
                }
            ],
            "language" : ["EN", "FR"],
            "country" : "US"
        },
        "year" : "1991",
        "month" : "January",
        "start_page" : "3",
        "end_page" : "21",
        "link" : [
            {
                "url" : "http://www.example.com/article",
                "type" : "fulltext",
                "content_type" : "HTML"
            }
        ],
        "abstract" : "This is the abstract for the example article. It can be quite a long field so there's a fairly"
                     " sizable chunk of text here. The weather today is grey, because I am writing this from Scotland,"
                     " and the time is early evening. A cup of tea helps work's pleasantness - in particular, a"
                     " rooibos blend with vanilla and spice. It's a tea that goes fairly well with ginger biscuits."
                     " Never dunked, of course. Rooibos is from South Africa; it's a flavoursome caffeine-free tea,"
                     " ideal for the working day. I like mine fairly strong - steeping for 3-4 minutes gives this tea"
                     " enough time to release its distinctive flavour, but without overpowering the delicate vanilla. ",
        "author" : [
            {
                "name" : "The Author",
                "email" : "author@example.com",
                "affiliation" : "University Cottage Labs"
            },
        ],
        "keywords": ["word", "key"],
        "subject" : [
            {
                "scheme": "LCC",
                "term": "Economic theory. Demography",
                "code": "HB1-3840"
            },
            {
                "scheme": "LCC",
                "term": "Social Sciences",
                "code": "H"
            }
        ],
    },
    "created_date": "2000-01-01T00:00:00Z"
}

ARTICLE_STRUCT = {
    "fields": {
        "id": {"coerce": "unicode"},                # Note that we'll leave these in for ease of use by the
        "created_date": {"coerce": "utcdatetime"},  # caller, but we'll need to ignore them on the conversion
        "last_updated": {"coerce": "utcdatetime"}   # to the real object
    },
    "objects": ["admin", "bibjson"],

    "structs": {

        "admin": {
            "fields": {
                "in_doaj": {"coerce": "bool", "get__default": False},
                "publisher_record_id": {"coerce": "unicode"},
                "upload_id": {"coerce": "unicode"}
            }
        },

        "bibjson": {
            "fields": {
                "title": {"coerce": "unicode"},
                "year": {"coerce": "unicode"},
                "month": {"coerce": "unicode"},
                "start_page": {"coerce": "unicode"},
                "end_page": {"coerce": "unicode"},
                "abstract": {"coerce": "unicode"}
            },
            "lists": {
                "identifier": {"contains": "object"},
                "link": {"contains": "object"},
                "author": {"contains": "object"},
                "keywords": {"coerce": "unicode", "contains": "field"},
            },
            "objects": [
                "journal",
            ],
            "structs": {

                "identifier": {
                    "fields": {
                        "type": {"coerce": "unicode"},
                        "id": {"coerce": "unicode"}
                    }
                },

                "link": {
                    "fields": {
                        "type": {"coerce": "link_type"},
                        "url": {"coerce": "url"},
                        "content_type": {"coerce": "link_content_type"}
                    }
                },

                "author": {
                    "fields": {
                        "name": {"coerce": "unicode"},
                        "email": {"coerce": "unicode"},
                        "affiliation": {"coerce": "unicode"}
                    }
                },

                "journal": {
                    "fields": {
                        "volume": {"coerce": "unicode"},
                        "number": {"coerce": "unicode"}
                    },
                }
            }
        }
    }
}