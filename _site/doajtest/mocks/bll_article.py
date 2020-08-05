from doajtest.fixtures import ArticleFixtureFactory
from portality.models import Article
from portality.bll.exceptions import ArticleMergeConflict
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


        def mock(article, owner=None, results_per_match_type=10):
            return possible_duplicates

        return mock

    @classmethod
    def is_legitimate_owner(cls, legit=None, legit_on_issn=None):
        def mock(*arg, **kwarg):
            if legit is not None:
                return legit

            if legit_on_issn is not None:
                article = arg[0]
                issns = article.bibjson().issns()
                for issn in issns:
                    if issn in legit_on_issn:
                        return True
                return False

            return False
        return mock

    @classmethod
    def issn_ownership_status(cls, owned, shared, unowned, unmatched):

        def mock(*arg, **kwarg):
            return owned, shared, unowned, unmatched

        return mock

    @classmethod
    def get_duplicate(cls, return_none=False, given_article_id=None, eissn=None, pissn=None, doi=None, fulltext=None, merge_conflict=False):
        article = None
        if not return_none and not merge_conflict:
            source = ArticleFixtureFactory.make_article_source(eissn=eissn, pissn=pissn, doi=doi, fulltext=fulltext)
            article = Article(**source)
            article.set_id()

        def mock(*args, **kwargs):
            if merge_conflict:
                raise ArticleMergeConflict()

            supplied_article = args[0]
            if given_article_id is not None:
                if given_article_id == supplied_article.id:
                    return article
            else:
                return article

        return mock

