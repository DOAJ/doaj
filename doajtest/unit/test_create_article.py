from doajtest.fixtures import JournalFixtureFactory, ArticleFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll.exceptions import DuplicateArticleException, ArticleMergeConflict
from portality.models import Account, Article, Journal
from portality.bll.services.article import ArticleService


class TestCreateOrUpdateArticle(DoajTestCase):

    def setUp(self):
        super(TestCreateOrUpdateArticle, self).setUp()

        self.publisher = Account()
        self.publisher.add_role("publisher")
        self.publisher.save(blocking=True)

        self.admin = Account()
        self.admin.add_role("admin")
        self.admin.save(blocking=True)

        sources = JournalFixtureFactory.make_many_journal_sources(2, True)
        self.journal1 = Journal(**sources[0])
        self.journal1.set_owner(self.publisher.id)
        jbib1 = self.journal1.bibjson()
        jbib1.add_identifier(jbib1.P_ISSN, "1111-1111")
        jbib1.add_identifier(jbib1.E_ISSN, "2222-2222")
        self.journal1.save(blocking=True)

        self.publisher.add_journal(self.journal1)

        self.journal2 = Journal(**sources[1])
        jbib2 = self.journal2.bibjson()
        jbib2.add_identifier(jbib2.P_ISSN, "1234-5678")
        jbib2.add_identifier(jbib2.E_ISSN, "9876-5432")
        self.journal2.save(blocking=True)

        self.article10 = Article(
            **ArticleFixtureFactory.make_article_source(pissn="1111-1111", eissn="2222-2222", doi="10.0000/article-10",
                                                        fulltext="https://www.article10.com"))
        self.article10.set_id("articleid10")
        self.article10.save(blocking=True)

        self.article11 = Article(
            **ArticleFixtureFactory.make_article_source(pissn="1111-1111", eissn="2222-2222", doi="10.0000/article-11",
                                                        fulltext="https://www.article11.com"))
        self.article11.set_id("articleid11")
        self.article11.save(blocking=True)

        self.article2 = Article(
            **ArticleFixtureFactory.make_article_source(pissn="1234-5678", eissn="9876-5432", doi="10.0000/article-2",
                                                        fulltext="https://www.article2.com"))
        self.article2.set_id("articleid2")
        self.article2.save(blocking=True)

    def tearDown(self):
        super(TestCreateOrUpdateArticle, self).tearDown()

    def test_00_no_doi_and_url_changed(self):
        ba = self.article10.bibjson()
        ba.title = "Updated Article"

        # try for admin

        resp = ArticleService.create_article(self=ArticleService(), account=self.admin, article=self.article10, update_article_id=self.article10.id)

        assert resp["success"] == 1, "expected 1 updated, received: {}".format(resp)
        assert resp["update"] == 1, "expected 1 updated, received: {}".format(resp)
        assert resp["new"] == 0, "expected 1 updated, received: {}".format(resp)
        assert self.article10.bibjson().title == "Updated Article", "Expected `Updated Article`, received: {}" \
            .format(self.article10.bibjson().title)

        ba.title = "Updated 2nd time"

        # try for publisher

        resp = ArticleService.create_article(self=ArticleService(), account=self.publisher, article=self.article10)

        assert resp["success"] == 1, "expected 1 updated, received: {}".format(resp)
        assert resp["update"] == 1, "expected 1 updated, received: {}".format(resp)
        assert resp["new"] == 0, "expected 1 updated, received: {}".format(resp)
        assert self.article10.bibjson().title == "Updated 2nd time", "Expected `Updated 2nd time`, received: {}" \
            .format(self.article10.bibjson().title)

    def test_01_new_doi_new_url(self):
        ba = self.article10.bibjson()
        ba.remove_identifiers(ba.DOI)
        ba.remove_urls(ba.FULLTEXT)
        ba.add_identifier(ba.DOI, "10.0000/NEW")
        ba.add_url(ba.FULLTEXT, "https://www.UPDATED.com")

        #for publisher
        resp = ArticleService.create_article(self=ArticleService(), account=self.publisher, article=self.article10)
        assert resp["success"] == 1, "expected 1 new, received: {}".format(resp)
        assert resp["update"] == 0, "expected 1 new, received: {}".format(resp)
        assert resp["new"] == 1, "expected 1 new, received: {}".format(resp)

        #for admin
        resp = ArticleService.create_article(self=ArticleService(), account=self.admin, article=self.article10, update_article_id=self.article10.id)

        assert resp["success"] == 1, "expected 1 new, received: {}".format(resp)
        assert resp["update"] == 1, "expected 1 new, received: {}".format(resp)
        assert resp["new"] == 0, "expected 1 new, received: {}".format(resp)

    def test_02_old_doi_existing_url_admin(self):
        ba = self.article10.bibjson()
        ba.remove_urls(ba.FULLTEXT)
        # check for url from other article owned by the same publisher
        ba.add_url(self.article11.bibjson().get_single_url(ba.FULLTEXT), ba.FULLTEXT)

        # try as a publisher
        with self.assertRaises(ArticleMergeConflict):
            ArticleService.create_article(self=ArticleService(), account=self.publisher, article=self.article10)

        # try as an admin
        with self.assertRaises(ArticleMergeConflict):
            ArticleService.create_article(self=ArticleService(), account=self.admin, article=self.article10, update_article_id=self.article10.id)

        # check for url from other article owned by someone else
        ba.remove_urls(ba.FULLTEXT)
        ba.add_url(self.article2.bibjson().get_single_url(ba.FULLTEXT), ba.FULLTEXT)

        # try as a publisher
        with self.assertRaises(ArticleMergeConflict):
            ArticleService.create_article(self=ArticleService(), account=self.publisher, article=self.article10)

        # try as an admin
        with self.assertRaises(ArticleMergeConflict):
            ArticleService.create_article(self=ArticleService(), account=self.admin, article=self.article10, update_article_id=self.article10.id)

    def test_03_existing_doi_old_url_admin(self):
        ba = self.article10.bibjson()
        ba.remove_identifiers(ba.DOI)
        # check for DOI from other article owned by the same publisher
        ba.add_identifier(ba.DOI, "10.0000/article-11")

        # try as a publisher
        with self.assertRaises(ArticleMergeConflict):
            ArticleService.create_article(self=ArticleService(), account=self.publisher, article=self.article10)

        # try as an admin
        with self.assertRaises(ArticleMergeConflict):
            ArticleService.create_article(self=ArticleService(), account=self.admin, article=self.article10, update_article_id=self.article10.id)

        ba.remove_identifiers(ba.DOI)
        # check for DOI from other article owned by someone else
        ba.add_identifier(ba.DOI, "10.0000/article-2")

        # try as a publisher
        with self.assertRaises(ArticleMergeConflict):
            ArticleService.create_article(self=ArticleService(), account=self.publisher, article=self.article10)

        # try as an admin
        with self.assertRaises(ArticleMergeConflict):
            ArticleService.create_article(self=ArticleService(), account=self.admin, article=self.article10, update_article_id=self.article10.id)

    def test_04_old_doi_new_url(self):
        ba = self.article10.bibjson()
        ba.remove_urls(ba.FULLTEXT)
        ba.add_url("https://updated.com", ba.FULLTEXT)

        # try as publisher
        with self.assertRaises(DuplicateArticleException):
            ArticleService.create_article(self=ArticleService(), account=self.publisher, article=self.article10)

        # try as an admin
        resp = ArticleService.create_article(self=ArticleService(), account=self.admin, article=self.article10, update_article_id=self.article10.id)

        assert resp["success"] == 1, "expected 1 updated, received: {}".format(resp)
        assert resp["update"] == 1, "expected 1 updated, received: {}".format(resp)
        assert resp["new"] == 0, "expected 1 new, received: {}".format(resp)
        assert self.article10.get_normalised_fulltext() == "//updated.com", "expected //updated.com, received: {}".format(
            self.article10.get_normalised_fulltext())

    def test_05_new_doi_old_url(self):
        ba = self.article10.bibjson()
        ba.remove_identifiers(ba.DOI)
        ba.add_identifier(ba.DOI, "10.0000/article-UPDATED")

        # try as publisher
        with self.assertRaises(DuplicateArticleException):
            ArticleService.create_article(self=ArticleService(), account=self.publisher, article=self.article10)

        # try as an admin
        resp = ArticleService.create_article(self=ArticleService(), account=self.admin, article=self.article10, update_article_id=self.article10.id)

        assert resp["success"] == 1, "expected 1 updated, received: {}".format(resp)
        assert resp["update"] == 1, "expected 1 updated, received: {}".format(resp)
        assert resp["new"] == 0, "expected 1 updated, received: {}".format(resp)
        assert self.article10.get_normalised_doi() == "10.0000/article-UPDATED", \
            "expected 10.0000/article-UPDATED, received: {}".format(
                self.article10.get_normalised_fulltext())

    def test_06_existing_doi_new_url(self):
        ba = self.article10.bibjson()
        ba.remove_urls(ba.FULLTEXT)
        ba.add_url("https://updated.com", ba.FULLTEXT)
        # check for doi from other article of the same publisher
        ba.remove_identifiers(ba.DOI)
        ba.add_identifier(ba.DOI, self.article11.bibjson().get_one_identifier(ba.DOI))

        # try as publisher
        with self.assertRaises(DuplicateArticleException):
            ArticleService.create_article(self=ArticleService(), account=self.publisher, article=self.article10)

        with self.assertRaises(DuplicateArticleException):
            ArticleService.create_article(self=ArticleService(), account=self.admin, article=self.article10, update_article_id=self.article10.id)

    def test_07_new_doi_existing_url(self):
        ba = self.article10.bibjson()
        ba.remove_urls(ba.FULLTEXT)
        ba.add_url(self.article11.bibjson().get_single_url(ba.FULLTEXT), ba.FULLTEXT)
        # check for doi from other article of the same publisher
        ba.remove_identifiers(ba.DOI)
        ba.add_identifier(ba.DOI, "10.0000/article-UPDATED")

        # try as publisher
        with self.assertRaises(DuplicateArticleException):
            ArticleService.create_article(self=ArticleService(), account=self.publisher, article=self.article10)

        # try as an admin
        with self.assertRaises(DuplicateArticleException):
            ArticleService.create_article(self=ArticleService(), account=self.admin, article=self.article10, update_article_id=self.article10.id)
