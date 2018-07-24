from doajtest.fixtures import ArticleFixtureFactory
from portality.models import Article
from datetime import datetime

class BLLArticleMockFactory(object):

    @classmethod
    def discover_duplicates(cls, doi_duplicates=0, fulltext_duplicates=0, overlap=0):

        if overlap > doi_duplicates or overlap > fulltext_duplicates:
            raise Exception("overlap must be the same as or less than either of doi_duplicates or fulltext_duplicates")

        idents = []
        # first make duplicate records for the total number of desired dois
        for i in range(doi_duplicates):
            idents.append({"doi_domain" : True, "doi" : "10.1234/abc/1", "fulltext" : "http://example.com/unique/" + str(i)})

        for i in range(overlap):
            idents[i]["fulltext"] = "http://example.com/1"
            idents[i]["fulltext_domain"] = True

        remaining_fulltexts = fulltext_duplicates - overlap
        for i in range(remaining_fulltexts):
            idents.append({"fulltext_domain" : True, "doi" : "10.1234/unique/" + str(i), "fulltext" : "http://example.com/1"})

        possible_duplicates = {"doi" : [], "fulltext" : []}
        for i, ident in enumerate(idents):
            source = ArticleFixtureFactory.make_article_source(eissn="1234-5678", pissn="9876-5432", doi=ident["doi"], fulltext=["fulltext"])
            article = Article(**source)
            article.set_id()
            article.data["last_updated"] = datetime.fromtimestamp(i * 100000).strftime("%Y-%m-%dT%H:%M:%SZ")
            if "doi_domain" in ident:
                possible_duplicates["doi"].append(article)
            if "fulltext_domain" in ident:
                possible_duplicates["fulltext"].append(article)

        if len(possible_duplicates["doi"]) == 0:
            del possible_duplicates["doi"]
        if len(possible_duplicates["fulltext"]) == 0:
            del possible_duplicates["fulltext"]


        def mock(article, owner=None):
            return possible_duplicates

        return mock

    @classmethod
    def is_legitimate_owner(cls, legit):
        def mock(*arg, **kwarg):
            return legit
        return mock

    @classmethod
    def issn_ownership_status(cls, owned, shared, unowned, unmatched):

        def mock(*arg, **kwarg):
            return owned, shared, unowned, unmatched

        return mock

    @classmethod
    def get_duplicate(cls, eissn, pissn, doi, fulltext):
        source = ArticleFixtureFactory.make_article_source(eissn=eissn, pissn=pissn, doi=doi, fulltext=fulltext)
        article = Article(**source)
        article.set_id()

        def mock(*args, **kwargs):
            return article

        return mock
