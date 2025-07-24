import unittest

from doajtest.fixtures import ArticleFixtureFactory
from portality import models
from portality.crosswalks.article_ris import ArticleRisXWalk


class TestArticleRisXWalk(unittest.TestCase):
    def test_article2ris(self):
        article = ArticleFixtureFactory.make_article_source()
        article = models.Article(**article)
        article.bibjson().abstract = "abstract"
        ris = ArticleRisXWalk.article2ris(article)
        assert ris.type == 'JOUR'
        assert ris['T1'] == [article.data['bibjson']['title']]
        assert ris.to_text().split() == """
TY  - JOUR
T1  - Article Title
AU  - The Author
PY  - 2015
JF  - The Title
PB  - The Publisher
VL  - 1
IS  - 99
SP  - 3
EP  - 21
UR  - http://www.example.com/article
AB  - abstract
KW  - word
KW  - key
DO  - 10.0000/SOME.IDENTIFIER
LA  - EN
LA  - FR
ER  - 
        """.split()

    def test_article2ris__only_title(self):
        ris = ArticleRisXWalk.article2ris({"bibjson": {"title": "Article Title"}})
        assert ris.to_text().split() == """
TY  - JOUR
T1  - Article Title
ER  - 
        """.split()
