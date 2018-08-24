from doajtest.helpers import DoajTestCase
from portality.api.v1 import ArticlesBulkApi, Api401Error, Api400Error
from portality import models
from doajtest.fixtures import ArticleFixtureFactory, JournalFixtureFactory
import time
from copy import deepcopy

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
            data = ArticleFixtureFactory.make_incoming_api_article()
            # change the DOI and fulltext URLs to escape duplicate detection
            # and try with multiple articles
            doi_ix = find_dict_in_list(data['bibjson']['identifier'], 'type', 'doi')
            if doi_ix == -1:
                data['bibjson']['identifier'].append({"type" : "doi"})
            data['bibjson']['identifier'][doi_ix]['id'] = '10.0000/SOME.IDENTIFIER.{0}'.format(i)
            
            fulltext_url_ix = find_dict_in_list(data['bibjson']['link'], 'type', 'fulltext')
            if fulltext_url_ix == -1:
                data['bibjson']['link'].append({"type" : "fulltext"})
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
        journal.save()

        time.sleep(2)

        # call create on the object (which will save it to the index)
        ids = ArticlesBulkApi.create(dataset, account)

        # check that we got the right number of ids back
        assert len(ids) == 10
        assert len(list(set(ids))) == 10, len(list(set(ids)))  # are they actually 10 unique IDs?

        # let the index catch up
        time.sleep(2)

        # check that each id was actually created
        for id in ids:
            s = models.Article.pull(id)
            assert s is not None

    def test_02_create_duplicate_articles_success(self):
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
        journal.save()

        time.sleep(2)

        # call create on the object (which will save it to the index)
        ids = ArticlesBulkApi.create(dataset, account)

        # check that we got the right number of ids back
        assert len(ids) == 1

        # let the index catch up
        time.sleep(2)

        # check that each id was actually created
        for id in ids:
            s = models.Article.pull(id)
            assert s is not None

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
            journal.save()
            time.sleep(1)
            dataset = dataset[:5] + [{"some" : {"junk" : "data"}}] + dataset[5:]
            ids = ArticlesBulkApi.create(dataset, account)

        # check that the index is empty, as none of them should have been made
        all = [x for x in models.Article.iterall()]
        assert len(all) == 0

    def test_04_delete_article_success(self):
        # set up all the bits we need
        data = ArticleFixtureFactory.make_incoming_api_article()
        dataset = [data] * 10

        # create the account we're going to work as
        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")
        # add a journal to the account
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(account.id)
        journal.save()
        time.sleep(1)

        # call create on the objects (which will save it to the index)
        ids = ArticlesBulkApi.create(dataset, account)

        # let the index catch up
        time.sleep(2)

        # now delete half of them
        dels = ids[:5]
        ArticlesBulkApi.delete(dels, account)

        # let the index catch up
        time.sleep(2)

        for id in dels:
            ap = models.Article.pull(id)
            assert ap is None
        for id in ids[5:]:
            ap = models.Article.pull(id)
            assert ap is not None

    def test_05_delete_articles_fail(self):
        # set up all the bits we need
        data = ArticleFixtureFactory.make_incoming_api_article()
        dataset = []
        for i in range(10):
            cdata = deepcopy(data)
            # FIXME: put different dois and fulltexts in the articles
        dataset = [data] * 10

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
        journal.save()
        time.sleep(1)

        # call create on the objects (which will save it to the index)
        ids = ArticlesBulkApi.create(dataset, article_owner)

        # let the index catch up
        time.sleep(2)

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


