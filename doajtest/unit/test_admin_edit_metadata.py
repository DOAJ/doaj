from doajtest.fixtures import JournalFixtureFactory, ArticleFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.models import Article, Account, Journal
from flask import url_for
from doajtest.unit.resources.articles_metadata_form import ArticleMetadataFactory


class TestAdminEditMetadata(DoajTestCase):

    def setUp(self):
        super(TestAdminEditMetadata, self).setUp()
        admin_account = Account.make_account(username="admin",
                                             name="Admin",
                                             email="admin@test.com",
                                             roles=["admin"])
        admin_account.set_password('password123')
        admin_account.save()

        publisher_account = Account.make_account(username="publisher",
                                                 name="Publisher",
                                                 email="publisher@test.com",
                                                 roles=["publisher"])
        publisher_account.set_password('password456')
        publisher_account.save(blocking=True)

        self.j = Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        self.j.save(blocking=True)
        self.a = Article(**ArticleFixtureFactory.make_article_source(in_doaj=True))
        self.a.save(blocking=True)

    def tearDown(self):
        super(TestAdminEditMetadata, self).tearDown()
        del self.a
        del self.j

    def admin_post_article_metadata_form(self, formdata):
        """ Post a form tto the article metadata endpoint """
        with self.app_test.test_client() as t_client:
            self.login(t_client, "admin", "password123")
            resp = t_client.post(url_for('admin.article_page', article_id=self.a.id), data=dict(formdata))
            assert resp.status_code == 200, "expected: 200, received: {}".format(resp.status)

    @staticmethod
    def login(app, username, password):
        return app.post('/account/login',
                        data=dict(username=username, password=password),
                        follow_redirects=True)

    @staticmethod
    def logout(app):
        return app.get('/account/logout', follow_redirects=True)

    def test_01_open_article_page(self):
        """ Ensure only Admin can open the article metadata form """

        with self.app_test.test_client() as t_client:
            self.login(t_client, "admin", "password123")
            resp = t_client.get(url_for('admin.article_page', article_id=self.a.id), follow_redirects=False)
            assert resp.status_code == 200, "expected: 200, received: {}".format(resp.status)

        # user not logged in
        with self._make_and_push_test_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('admin.article_page', article_id=self.a.id), follow_redirects=False)
                assert resp.status_code == 302, "expected: 302, received: {}".format(resp.status) #expect redirection to login page

        # login as publisher
        with self.app_test.test_client() as t_client:
            self.login(t_client, "publisher", "password456")
            resp = t_client.get(url_for('admin.article_page', article_id=self.a.id), follow_redirects=False)
            assert resp.status_code == 302, "expected: 302, received: {}".format(resp.status)  # expect redirection to login page

    def test_02_update_article_metadata_no_url_fulltext(self):
        """ Update an article with no change to identifying fields: URL and DOI """

        source = ArticleMetadataFactory(article_source=self.a).update_article_no_change_to_url_and_doi()

        # Submit the form
        self.admin_post_article_metadata_form(source)

        # Retrieve the result
        a = Article.pull(self.a.id)
        b = a.bibjson()
        assert b.title == source['title'], 'expected updated title, received: {}'.format(b.title)

    def test_03_update_fulltext_valid(self):
        """ Update an article's fulltext URL """
        source = ArticleMetadataFactory(article_source=self.a).update_article_fulltext(valid=True)

        # Submit the form
        self.admin_post_article_metadata_form(source)

        a = Article.pull(self.a.id)
        bj = a.bibjson()
        # expect updated fulltext url
        assert bj.get_single_url("fulltext") == 'https://www.newarticleurl.co.uk/fulltext', 'expected updated url, received: {}'.format(bj.get_single_url("fulltext"))

    def test_04_update_fulltext_invalid(self):
        """ The form should ignore an update that has the same fulltext URL as an existing article """
        source = ArticleMetadataFactory(article_source=self.a).update_article_fulltext(valid=False)

        a1source = ArticleFixtureFactory.make_article_source(in_doaj=True)
        a1source["id"] = 'aaaaaaaaa_article'
        a1source["fulltext"] = "https://www.urltorepeat.com"
        a1 = Article(**a1source)
        a1.save(blocking=True)

        # Submit the form
        self.admin_post_article_metadata_form(source)

        # Retrieve the result - it should be unchanged
        a = Article.pull(self.a.id)
        bj = a.bibjson()
        assert bj.title == "Article Title", 'expect old title, received: {}'.format(bj.title)
        assert bj.get_single_url(
            "fulltext") == 'http://www.example.com/article', 'expected old url, received: {}'.format(
            bj.get_single_url("fulltext"))

    def test_05_update_doi_valid(self):
        """ The form should allow an update with a new valid DOI """
        source = ArticleMetadataFactory(article_source=self.a).update_article_doi(valid=True)

        # Submit the form
        self.admin_post_article_metadata_form(source)

        # Retrieve the result
        a = Article.pull(self.a.id)
        bj = a.bibjson()
        # expect new data
        assert bj.title == "New title", 'expect updated title, received: {}'.format(bj.title)
        assert bj.get_one_identifier("doi") == '10.1111/article-0', 'expected new doi, received: {}'.format(bj.get_single_identifier("doi"))

    def test_06_update_doi_invalid(self):
        source = ArticleMetadataFactory(article_source=self.a).update_article_doi(valid=False)

        a1source = ArticleFixtureFactory.make_article_source(in_doaj=True)
        a1source['id'] = 'aaaaaaaaa_article'
        a1source["fulltext"] = "https://www.someurl.com"
        a1source["doi"] = '10.1234/article'
        a1 = Article(**a1source)
        a1.save(blocking=True)

        # Submit the form
        self.admin_post_article_metadata_form(source)

        a = Article.pull(self.a.id)
        bj = a.bibjson()
        # expect old data
        assert bj.title == "Article Title", 'expect old title, received: {}'.format(bj.title)
        assert bj.get_one_identifier("doi") == '10.0000/SOME.IDENTIFIER', 'expected old doi, received: {}'.format(
            bj.get_one_identifier("doi"))
