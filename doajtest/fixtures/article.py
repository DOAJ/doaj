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
    def upload_author_email_address(cls):
        return cls._response_from_xpath("//record[journalTitle='author email address']")

    @classmethod
    def upload_1_issn_superlong_should_not_clip(cls):
        return cls._response_from_xpath("//record[journalTitle='PISSN Correct Superlong Abstract Expected to Not be Clipped']")

    @classmethod
    def upload_1_issn_superlong_should_clip(cls):
        return cls._response_from_xpath("//record[journalTitle='PISSN Correct Superlong Abstract Expected to be Clipped']")

    @classmethod
    def invalid_schema_xml(cls):
        return StringIO("<this><isnot my='schema'></isnot></this>")

    @classmethod
    def noids(cls):
        return cls._response_from_xpath("//record[journalTitle='NOIDS']")

    @classmethod
    def valid_url_http(cls):
        return cls._response_from_xpath("//record[journalTitle='Url starting with http']")

    @classmethod
    def valid_url_https(cls):
        return cls._response_from_xpath("//record[journalTitle='Url starting with https']")

    @classmethod
    def valid_url_non_ascii_chars(cls):
        return cls._response_from_xpath("//record[journalTitle='Url containing non-ascii characters']")

    @classmethod
    def invalid_url(cls):
        return cls._response_from_xpath("//record[journalTitle='Invalid url']")

    @classmethod
    def invalid_url_http_missing(cls):
        return cls._response_from_xpath("//record[journalTitle='Url with http missing']")

    @staticmethod
    def make_article_source(eissn=None, pissn=None, with_id=True, in_doaj=True, with_journal_info=True, doi=None, fulltext=None):
        source = deepcopy(ARTICLE_SOURCE)
        if not with_id:
            del source["id"]
        if with_journal_info is False:
            del source["bibjson"]["journal"]
        source["admin"]["in_doaj"] = in_doaj
        if eissn is None and pissn is None:
            return source

        delete = []
        for i in range(len(source["bibjson"]["identifier"])):
            ident = source["bibjson"]["identifier"][i]
            if ident.get("type") == "pissn":
                if pissn is not None:
                    ident["id"] = pissn
                else:
                    delete.append(i)
            elif ident.get("type") == "eissn":
                if eissn is not None:
                    ident["id"] = eissn
                else:
                    delete.append(i)

        delete.sort(reverse=True)
        for idx in delete:
            del source["bibjson"]["identifier"][idx]

        if doi is not None:
            if doi is False:
                for i in range(len(source["bibjson"]["identifier"])):
                    ident = source["bibjson"]["identifier"][i]
                    if ident.get("type") == "doi":
                        del source["bibjson"]["identifier"][i]
                        break
            else:
                set_doi = False
                for ident in source["bibjson"]["identifier"]:
                    if ident.get("type") == "doi":
                        ident["id"] = doi
                        set_doi = True
                if not set_doi:
                    source["bibjson"]["identifier"].append({"type" : "doi", "id" : doi})

        if fulltext is not None:
            if fulltext is False:
                for i in range(len(source["bibjson"]["link"])):
                    ident = source["bibjson"]["link"][i]
                    if ident.get("type") == "fulltext":
                        del source["bibjson"]["link"][i]
                        break
            else:
                set_fulltext = False
                for ident in source["bibjson"]["link"]:
                    if ident.get("type") == "fulltext":
                        ident["url"] = fulltext
                        set_fulltext = True
                if not set_fulltext:
                    source["bibjson"]["link"].append({"type" : "fulltext", "url" : fulltext})

        return source
    
    @staticmethod
    def make_incoming_api_article(doi=None, fulltext=None):
        template = deepcopy(ARTICLE_SOURCE)
        template['bibjson']['journal']['start_page'] = template['bibjson']['start_page']
        template['bibjson']['journal']['end_page'] = template['bibjson']['end_page']
        del template['bibjson']['start_page']
        del template['bibjson']['end_page']

        if doi is not None:
            set_doi = False
            for i in range(len(template["bibjson"]["identifier"])):
                ident = template["bibjson"]["identifier"][i]
                if ident.get("type") == "doi":
                    ident["id"] = doi
                    set_doi = True
            if not set_doi:
                template["bibjson"]["identifier"].append({"type" : "doi", "id" : doi})

        if fulltext is not None:
            set_fulltext = False
            for i in range(len(template["bibjson"]["link"])):
                ident = template["bibjson"]["link"][i]
                if ident.get("type") == "fulltext":
                    ident["url"] = fulltext
                    set_fulltext = True
            if not set_fulltext:
                template["bibjson"]["link"].append({"type" : "fulltext", "url" : fulltext})


        return deepcopy(template)

    @staticmethod
    def make_article_apido_struct():
        return deepcopy(ARTICLE_STRUCT)

ARTICLE_SOURCE = {
    "id" : "abcdefghijk_article",
    "admin" : {
        "in_doaj" : True,
        "seal" : False,
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
                "seal": {"coerce": "bool", "get__default": False},
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
