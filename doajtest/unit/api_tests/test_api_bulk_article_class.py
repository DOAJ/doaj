"""
test the bulk article API by ArticlesBulkApi layer
"""
import json
import time
from pathlib import Path
from unittest.mock import patch

from flask import url_for
from portality.lib.thread_utils import wait_until

from doajtest.fixtures import ArticleFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase, with_es, wait_unit
from portality import models
from portality.api.current import ArticlesBulkApi, Api401Error, Api400Error


class TestBulkArticle(DoajTestCase):

    def setUp(self):
        super(TestBulkArticle, self).setUp()

    def tearDown(self):
        super(TestBulkArticle, self).tearDown()

    @with_es(indices=[models.Article.__type__, models.Journal.__type__],
             warm_mappings=[models.Article.__type__])
    def test_01_create_articles_success(self):

        dataset = list(ArticleFixtureFactory.make_bulk_incoming_api_article(10))

        # create an account that we'll do the create as
        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")

        # add a journal to the account
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(account.id)
        journal.save(blocking=True)

        # call create on the object (which will save it to the index)
        ids = ArticlesBulkApi.create(dataset, account)

        # check that we got the right number of ids back
        assert len(ids) == 10
        assert len(list(set(ids))) == 10, len(list(set(ids)))  # are they actually 10 unique IDs?

        # let the index catch up
        time.sleep(0.6)

        # check that each id was actually created
        for _id in ids:
            s = models.Article.pull(_id)
            assert s is not None

    @with_es(indices=[models.Article.__type__, models.Journal.__type__])
    def test_02_create_duplicate_articles(self):
        # set up all the bits we need - 10 articles
        data = ArticleFixtureFactory.make_incoming_api_article()
        dataset = [data] * 10

        # create an account that we'll do the create as
        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")

        # add a journal to the account
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(account.id)
        journal.save(blocking=True)

        # call create on the object (which will save it to the index)
        with self.assertRaises(Api400Error):
            ids = ArticlesBulkApi.create(dataset, account)

        time.sleep(0.6)

        # Since the upload was rejected, we should have no articles in the index
        assert len(models.Article.all()) == 0, len(models.Article.all())

    @with_es(indices=[models.Article.__type__, models.Journal.__type__])
    def test_03_create_articles_fail(self):
        # if the account is dud
        with self.assertRaises(Api401Error):
            data = ArticleFixtureFactory.make_incoming_api_article()
            dataset = [data] * 10
            ids = ArticlesBulkApi.create(dataset, None)

        # check that the index is empty, as none of them should have been made
        all = [x for x in models.Article.iterall()]
        assert len(all) == 0

        # if the data is bust
        with self.assertRaises(Api400Error):
            account = models.Account()
            account.set_id("test")
            account.set_name("Tester")
            account.set_email("test@test.com")
            # add a journal to the account
            journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
            journal.set_owner(account.id)
            journal.save(blocking=True)
            dataset = dataset[:5] + [{"some": {"junk": "data"}}] + dataset[5:]
            ids = ArticlesBulkApi.create(dataset, account)

        # check that the index is empty, as none of them should have been made
        _all = [x for x in models.Article.iterall()]
        assert len(_all) == 0

    @with_es(indices=[models.Article.__type__, models.Journal.__type__],
             warm_mappings=[models.Article.__type__])
    def test_04_delete_article_success(self):
        # set up all the bits we need
        dataset = []
        for i in range(10):
            data = ArticleFixtureFactory.make_incoming_api_article(doi="10.123/test/" + str(i),
                                                                   fulltext="http://example.com/" + str(i))
            dataset.append(data)

        # create the account we're going to work as
        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")
        # add a journal to the account
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(account.id)
        journal.save(blocking=True)

        # call create on the objects (which will save it to the index)
        ids = ArticlesBulkApi.create(dataset, account)

        # let the index catch up
        time.sleep(0.6)

        # now delete half of them
        dels = ids[:5]
        ArticlesBulkApi.delete(dels, account)

        # let the index catch up
        time.sleep(0.6)

        for _id in dels:
            ap = models.Article.pull(_id)
            assert ap is None
        for _id in ids[5:]:
            ap = models.Article.pull(_id)
            assert ap is not None

    @with_es(indices=[models.Article.__type__, models.Journal.__type__],
             warm_mappings=[models.Article.__type__])
    def test_05_delete_articles_fail(self):
        # set up all the bits we need
        dataset = []
        for i in range(10):
            data = ArticleFixtureFactory.make_incoming_api_article(doi="10.123/test/" + str(i),
                                                                   fulltext="http://example.com/" + str(i))
            dataset.append(data)

        # create the main account we're going to work as
        article_owner = models.Account()
        article_owner.set_id("test")
        article_owner.set_name("Tester")
        article_owner.set_email("test@test.com")
        # create another account which will own the articles so the one
        # above will be "another user" trying to delete our precious articles.
        somebody_else = models.Account()
        somebody_else.set_id("somebody_else")
        somebody_else.set_name("Somebody Else")
        somebody_else.set_email("somebodyelse@test.com")
        # add a journal to the article owner account to create that link
        # between account and articles
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(article_owner.id)
        journal.save(blocking=True)

        # call create on the objects (which will save it to the index)
        ids = ArticlesBulkApi.create(dataset, article_owner)

        # let the index catch up
        time.sleep(0.6)

        # call delete on the object in various context that will fail

        # without an account
        with self.assertRaises(Api401Error):
            ArticlesBulkApi.delete(ids, None)

        # with the wrong account
        article_owner.set_id("other")
        with self.assertRaises(Api400Error):
            ArticlesBulkApi.delete(ids, somebody_else)

        # on the wrong id
        ids.append("adfasdfhwefwef")
        article_owner.set_id("test")
        with self.assertRaises(Api400Error):
            ArticlesBulkApi.delete(ids, article_owner)

        with self.assertRaises(Api400Error):
            ArticlesBulkApi.delete(ids, article_owner)

    @with_es(indices=[models.Article.__type__, models.Journal.__type__, models.Account.__type__],
             warm_mappings=[models.Article.__type__])
    def test_06_test_via_endpoint(self):
        """ Use a request context to test the API via the route """

        # set up all the bits we need
        dataset = []
        for i in range(10):
            data = ArticleFixtureFactory.make_incoming_api_article(doi="10.123/test/" + str(i),
                                                                   fulltext="http://example.com/" + str(i))
            dataset.append(data)

        # create the main account we're going to work as
        article_owner = models.Account()
        article_owner.set_id("test")
        article_owner.set_name("Tester")
        article_owner.set_email("test@test.com")
        article_owner.generate_api_key()
        article_owner.add_role('publisher')
        article_owner.add_role('api')
        article_owner.save(blocking=True)

        # Add another user who doesn't own these articles
        somebody_else = models.Account()
        somebody_else.set_id("somebody_else")
        somebody_else.set_name("Somebody Else")
        somebody_else.set_email("somebodyelse@test.com")
        somebody_else.generate_api_key()
        somebody_else.add_role('publisher')
        somebody_else.add_role('api')
        somebody_else.save(blocking=True)

        assert article_owner.api_key != somebody_else.api_key

        # add a journal to the article owner account to create that link between account and articles
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(article_owner.id)
        journal.save(blocking=True)

        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                # Bulk create
                # The wrong owner can't create articles
                resp = t_client.post(url_for('api_v3.bulk_article_create', api_key=somebody_else.api_key),
                                     data=json.dumps(dataset))
                assert resp.status_code == 400, resp.status_code

                # Bulk create
                # redirected from v1
                # resp = t_client.post(url_for('api_v1.bulk_article_create', api_key=somebody_else.api_key),
                #                      data=json.dumps(dataset))
                # assert resp.status_code == 301, resp.status_code

                # But the correct owner can create articles
                resp = t_client.post(url_for('api_v3.bulk_article_create', api_key=article_owner.api_key),
                                     data=json.dumps(dataset))
                assert resp.status_code == 201
                reply = json.loads(resp.data.decode("utf-8"))
                assert len(reply) == len(dataset)
                first_art = reply.pop()
                assert first_art['status'] == 'created'
                # Check we actually created new records
                assert wait_until(lambda: len(models.Article.all()) == len(dataset))

                # Bulk delete
                all_but_one = [new_art['id'] for new_art in reply]
                resp = t_client.delete(url_for('api_v3.bulk_article_delete', api_key=article_owner.api_key),
                                       data=json.dumps(all_but_one))
                assert resp.status_code == 204
                # we should have deleted all but one of the articles.
                assert wait_until(lambda: len(models.Article.all()) == 1)
                # And our other user isn't allowed to delete the remaining one.
                resp = t_client.delete(url_for('api_v3.bulk_article_delete', api_key=somebody_else.api_key),
                                       data=json.dumps([first_art['id']]))
                assert resp.status_code == 400

    @with_es(indices=[models.Article.__type__, models.Journal.__type__, models.Account.__type__],
             warm_mappings=[models.Article.__type__])
    def test_07_v1_no_redirects(self):
        """ v1 answers directly without redirect https://github.com/DOAJ/doajPM/issues/2664 """
        # TODO: this is a copy of the test above, with v1 instead of current. If redirects are reinstated, uncomment above

        # set up all the bits we need
        dataset = []
        for i in range(10):
            data = ArticleFixtureFactory.make_incoming_api_article(doi="10.123/test/" + str(i),
                                                                   fulltext="http://example.com/" + str(i))
            dataset.append(data)

        # create the main account we're going to work as
        article_owner = models.Account()
        article_owner.set_id("test")
        article_owner.set_name("Tester")
        article_owner.set_email("test@test.com")
        article_owner.generate_api_key()
        article_owner.add_role('publisher')
        article_owner.add_role('api')
        article_owner.save(blocking=True)

        # Add another user who doesn't own these articles
        somebody_else = models.Account()
        somebody_else.set_id("somebody_else")
        somebody_else.set_name("Somebody Else")
        somebody_else.set_email("somebodyelse@test.com")
        somebody_else.generate_api_key()
        somebody_else.add_role('publisher')
        somebody_else.add_role('api')
        somebody_else.save(blocking=True)

        assert article_owner.api_key != somebody_else.api_key

        # add a journal to the article owner account to create that link between account and articles
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(article_owner.id)
        journal.save(blocking=True)

        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                # Bulk create
                # The wrong owner can't create articles
                resp = t_client.post(url_for('api_v1.bulk_article_create', api_key=somebody_else.api_key),
                                     data=json.dumps(dataset))
                assert resp.status_code == 400, resp.status_code

                # Bulk create
                # But the correct owner can create articles
                resp = t_client.post(url_for('api_v1.bulk_article_create', api_key=article_owner.api_key),
                                     data=json.dumps(dataset))
                assert resp.status_code == 201
                reply = json.loads(resp.data.decode("utf-8"))
                assert len(reply) == len(dataset)
                first_art = reply.pop()
                assert first_art['status'] == 'created'
                # Check we actually created new records
                assert wait_until(lambda: len(models.Article.all()) == len(dataset))

                # Bulk delete
                all_but_one = [new_art['id'] for new_art in reply]
                resp = t_client.delete(url_for('api_v1.bulk_article_delete', api_key=article_owner.api_key),
                                       data=json.dumps(all_but_one))
                assert resp.status_code == 204
                # we should have deleted all but one of the articles.
                assert wait_until(lambda: len(models.Article.all()) == 1)
                # And our other user isn't allowed to delete the remaining one.
                resp = t_client.delete(url_for('api_v1.bulk_article_delete', api_key=somebody_else.api_key),
                                       data=json.dumps([first_art['id']]))
                assert resp.status_code == 400

    @with_es(indices=[models.Article.__type__, models.Journal.__type__, models.Account.__type__],
             warm_mappings=[models.Article.__type__])
    def test_08_v2_no_redirects(self):
        """ v2, like v1 answers directly without redirect https://github.com/DOAJ/doajPM/issues/2664 """
        # TODO: this is a copy of the test above, with v2 instead of current. If redirects are reinstated, uncomment in test 6

        # set up all the bits we need
        dataset = []
        for i in range(10):
            data = ArticleFixtureFactory.make_incoming_api_article(doi="10.123/test/" + str(i),
                                                                   fulltext="http://example.com/" + str(i))
            dataset.append(data)

        # create the main account we're going to work as
        article_owner = models.Account()
        article_owner.set_id("test")
        article_owner.set_name("Tester")
        article_owner.set_email("test@test.com")
        article_owner.generate_api_key()
        article_owner.add_role('publisher')
        article_owner.add_role('api')
        article_owner.save(blocking=True)

        # Add another user who doesn't own these articles
        somebody_else = models.Account()
        somebody_else.set_id("somebody_else")
        somebody_else.set_name("Somebody Else")
        somebody_else.set_email("somebodyelse@test.com")
        somebody_else.generate_api_key()
        somebody_else.add_role('publisher')
        somebody_else.add_role('api')
        somebody_else.save(blocking=True)

        assert article_owner.api_key != somebody_else.api_key

        # add a journal to the article owner account to create that link between account and articles
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(article_owner.id)
        journal.save(blocking=True)

        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                # Bulk create
                # The wrong owner can't create articles
                resp = t_client.post(url_for('api_v2.bulk_article_create', api_key=somebody_else.api_key),
                                     data=json.dumps(dataset))
                assert resp.status_code == 400, resp.status_code

                # Bulk create
                # But the correct owner can create articles
                resp = t_client.post(url_for('api_v2.bulk_article_create', api_key=article_owner.api_key),
                                     data=json.dumps(dataset))
                assert resp.status_code == 201
                reply = json.loads(resp.data.decode("utf-8"))
                assert len(reply) == len(dataset)
                first_art = reply.pop()
                assert first_art['status'] == 'created'
                # Check we actually created new records
                assert wait_until(lambda: len(models.Article.all()) == len(dataset))

                # Bulk delete
                all_but_one = [new_art['id'] for new_art in reply]
                resp = t_client.delete(url_for('api_v2.bulk_article_delete', api_key=article_owner.api_key),
                                       data=json.dumps(all_but_one))
                assert resp.status_code == 204
                # we should have deleted all but one of the articles.
                wait_until(lambda: len(models.Article.all()) == 1)
                # And our other user isn't allowed to delete the remaining one.
                resp = t_client.delete(url_for('api_v2.bulk_article_delete', api_key=somebody_else.api_key),
                                       data=json.dumps([first_art['id']]))
                assert resp.status_code == 400

    def test_09_article_unacceptable(self):
        # set up all the bits we need
        dataset = []
        for i in range(10):
            data = ArticleFixtureFactory.make_incoming_api_article(doi="10.123/test/" + str(i),
                                                                   fulltext="http://example.com/" + str(i))
            dataset.append(data)

        # create the account we're going to work as
        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")
        # add a journal to the account
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=False))
        journal.set_owner(account.id)
        journal.save(blocking=False)

        # check that 400 is raised
        with self.assertRaises(Api400Error):
            ids = ArticlesBulkApi.create(dataset, account)


    def test_create_async__success(self):
        income_articles = list(ArticleFixtureFactory.make_bulk_incoming_api_article(10))
        self.assert_create_async(income_articles, 1, 1)

    def test_create_async__invalid_income_articles_format(self):
        income_articles = [{'invalid_input': 1}]
        self.assert_create_async(income_articles, 1, 1)

    def test_create_async__invalid_json_format(self):
        income_articles = [{'invalid_input': set()}]
        with self.assertRaises(TypeError):
            ArticlesBulkApi.create_async(income_articles, models.Account())

    def assert_create_async(self, income_articles, offset_articles, offset_files):
        def _count_files():
            return len(list(Path(self.app_test.config.get("UPLOAD_ASYNC_DIR", "/tmp")).glob("*.json")))

        n_org_articles = models.BulkArticles.count()
        n_org_files = _count_files()
        with patch_bgtask_submit() as mock_submit:
            ArticlesBulkApi.create_async(income_articles, models.Account())
            mock_submit.assert_called_once()

        assert _count_files() == n_org_files + offset_files
        wait_unit(lambda: models.BulkArticles.count() == n_org_articles + offset_articles, 5, 0.5)


def patch_bgtask_submit():
    return patch('portality.tasks.article_bulk_create.ArticleBulkCreateBackgroundTask.submit')
