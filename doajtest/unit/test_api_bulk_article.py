from doajtest.helpers import DoajTestCase
from portality.api.v1 import ArticlesBulkApi, Api401Error, Api400Error
from portality import models
from doajtest.fixtures import DoajXmlArticleFixtureFactory, JournalFixtureFactory
from copy import deepcopy
from portality.dao import ESMappingMissingError
from flask import url_for
import json
import time


class TestCrudArticle(DoajTestCase):

    def setUp(self):
        super(TestCrudArticle, self).setUp()

    def tearDown(self):
        super(TestCrudArticle, self).tearDown()

    def test_01_create_articles_success(self):
        def find_dict_in_list(lst, key, value):
            for i, dic in enumerate(lst):
                if dic[key] == value:
                    return i
            return -1

        # set up all the bits we need - 10 articles
        dataset = []
        for i in range(1, 11):
            data = DoajXmlArticleFixtureFactory.make_incoming_api_article()
            # change the DOI and fulltext URLs to escape duplicate detection
            # and try with multiple articles
            doi_ix = find_dict_in_list(data['bibjson']['identifier'], 'type', 'doi')
            if doi_ix == -1:
                data['bibjson']['identifier'].append({"type": "doi"})
            data['bibjson']['identifier'][doi_ix]['id'] = '10.0000/SOME.IDENTIFIER.{0}'.format(i)
            
            fulltext_url_ix = find_dict_in_list(data['bibjson']['link'], 'type', 'fulltext')
            if fulltext_url_ix == -1:
                data['bibjson']['link'].append({"type": "fulltext"})
            data['bibjson']['link'][fulltext_url_ix]['url'] = 'http://www.example.com/article_{0}'.format(i)

            dataset.append(deepcopy(data))

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

    def test_02_create_duplicate_articles(self):
        # set up all the bits we need - 10 articles
        data = DoajXmlArticleFixtureFactory.make_incoming_api_article()
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

        with self.assertRaises(ESMappingMissingError):
            all_articles = models.Article.all()

    def test_03_create_articles_fail(self):
        # if the account is dud
        with self.assertRaises(Api401Error):
            data = DoajXmlArticleFixtureFactory.make_incoming_api_article()
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

    def test_04_delete_article_success(self):
        # set up all the bits we need
        dataset = []
        for i in range(10):
            data = DoajXmlArticleFixtureFactory.make_incoming_api_article(doi="10.123/test/" + str(i), fulltext="http://example.com/" + str(i))
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

    def test_05_delete_articles_fail(self):
        # set up all the bits we need
        dataset = []
        for i in range(10):
            data = DoajXmlArticleFixtureFactory.make_incoming_api_article(doi="10.123/test/" + str(i), fulltext="http://example.com/" + str(i))
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

    def test_06_test_via_endpoint(self):
        """ Use a request context to test the API via the route """

        # set up all the bits we need
        dataset = []
        for i in range(10):
            data = DoajXmlArticleFixtureFactory.make_incoming_api_article(doi="10.123/test/" + str(i),
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
                assert resp.status_code == 400

                # But the correct owner can create articles
                resp = t_client.post(url_for('api_v1.bulk_article_create', api_key=article_owner.api_key),
                                     data=json.dumps(dataset))
                assert resp.status_code == 201
                reply = json.loads(resp.data)
                assert len(reply) == len(dataset)
                first_art = reply.pop()
                assert first_art['status'] == 'created'
                # Check we actually created new records
                time.sleep(1)
                assert len(models.Article.all()) == len(dataset)

                # Bulk delete
                all_but_one = [new_art['id'] for new_art in reply]
                resp = t_client.delete(url_for('api_v1.bulk_article_delete', api_key=article_owner.api_key),
                                       data=json.dumps(all_but_one))
                assert resp.status_code == 204
                time.sleep(1)
                # we should have deleted all but one of the articles.
                assert len(models.Article.all()) == 1
                # And our other user isn't allowed to delete the remaining one.
                resp = t_client.delete(url_for('api_v1.bulk_article_delete', api_key=somebody_else.api_key),
                                       data=json.dumps([first_art['id']]))
                assert resp.status_code == 400
