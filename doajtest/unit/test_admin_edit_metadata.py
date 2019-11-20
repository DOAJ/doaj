from time import sleep

from flask_login import current_user

from doajtest.fixtures import JournalFixtureFactory, ArticleFixtureFactory
from doajtest.helpers import DoajTestCase
from doajtest.unit.test_formcontext import TestForm
from portality.models import Article, Account, Journal
from flask import url_for
from doajtest.unit.resources.articles_metadata_form import ArticleMetadataFactory
from portality.view.forms import ArticleForm
from werkzeug.datastructures import MultiDict


class TestAdminEditMetadata(DoajTestCase):

    def setUp(self):
        super(TestAdminEditMetadata,self).setUp()
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

        self.j = Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        self.j.save(blocking=True)
        self.a = Article(**ArticleFixtureFactory.make_article_source(in_doaj=True))
        self.a.save(blocking=True)


    @staticmethod
    def login(app, username, password):
        return app.post('/account/login',
                        data=dict(username=username, password=password),
                        follow_redirects=True)

    @staticmethod
    def logout(app):
        return app.get('/account/logout', follow_redirects=True)

    def test_open_article_page(self):
        #ensure only admin can reach it
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                #login admin
                self.login(t_client, "admin", "password123")
                resp = t_client.get(url_for('admin.article_page', article_id=self.a.id))
                assert resp.status_code == 200, "expected: 200, received: {}".format(resp.status)
                #user not logged in
                self.logout(t_client)
                resp = t_client.get(url_for('admin.article_page', article_id=self.a.id))
                assert resp.status_code == 302, "expected: 200, received: {}".format(resp.status) #expect redirection to login page
                #login publisher
                self.login(t_client, "publisher", "password456")
                resp = t_client.get(url_for('admin.article_page', article_id=self.a.id))
                assert resp.status_code == 302, "expected: 200, received: {}".format(
                    resp.status)  # expect redirection to login page

    def test_update_article_metadata_no_url_fulltext(self):
        source = ArticleMetadataFactory(article_source=self.a).update_article_no_change_to_url_and_doi()
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                self.login(t_client, "admin", "password123")
                resp = t_client.post('/admin/article/'+self.a.id, data=dict(source))
                assert resp.status_code == 200, "expected: 200, received: {}".format(resp.status)

        a = Article.pull(self.a.id)
        b = a.bibjson()
        assert b.title == 'New title', 'expected updated title, received: {}'.format(b.title)

    def test_update_fulltext_valid(self):
        source = ArticleMetadataFactory(article_source=self.a).update_article_fulltext(valid=True)

        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                self.login(t_client, "admin", "password123")
                resp = t_client.post('/admin/article/'+self.a.id, data=dict(source))
                assert resp.status_code == 200, "expected: 200, received: {}".format(resp.status)

        a = Article.pull(self.a.id)
        b = a.bibjson()
        #expect updated fulltext url
        assert b.get_single_url("fulltext") == 'https://www.newarticleurl.co.uk/fulltext', 'expected updated url, received: {}'.format(b.get_single_url("fulltext"))

    def test_update_fulltext_invalid(self):
        source = ArticleMetadataFactory(article_source=self.a).update_article_fulltext(valid=False)

        a1source = ArticleFixtureFactory.make_article_source(in_doaj=True)
        a1source["id"]='aaaaaaaaa_article'
        a1source["fulltext"]="https://www.urltorepeat.com"
        self.a1 = Article(**a1source)
        self.a1.save(blocking=True)


        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                self.login(t_client, "admin", "password123")
                resp = t_client.post('/admin/article/' + self.a.id, data=dict(source))
                assert resp.status_code == 200, "expected: 200, received: {}".format(resp.status)

        a = Article.pull(self.a.id)
        b = a.bibjson()
        # expect old data
        assert b.title == "Article Title", 'expect old title, received: {}'.format(b.title)
        assert b.get_single_url(
            "fulltext") == 'http://www.example.com/article', 'expected old url, received: {}'.format(
            b.get_single_url("fulltext"))
