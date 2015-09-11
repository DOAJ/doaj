from doajtest.helpers import DoajTestCase
from portality.lib.dataobj import DataStructureException
from portality.api.v1.data_objects import IncomingArticleDO, OutgoingArticleDO
from portality.api.v1 import ArticlesCrudApi, Api401Error, Api400Error, Api404Error, Api403Error
from portality import models
from doajtest.fixtures import ArticleFixtureFactory, JournalFixtureFactory
import time
from datetime import datetime


class TestCrudArticle(DoajTestCase):

    def setUp(self):
        super(TestCrudArticle, self).setUp()

    def tearDown(self):
        super(TestCrudArticle, self).tearDown()

    def test_01_incoming_article_do(self):
        # make a blank one
        ia = IncomingArticleDO()

        # make one from an incoming article model fixture
        data = ArticleFixtureFactory.make_article_source()
        ia = IncomingArticleDO(data)

        # make another one that's broken
        data = ArticleFixtureFactory.make_article_source()
        del data["bibjson"]["title"]
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # now progressively remove the conditionally required/advanced validation stuff
        #
        # missing identifiers
        data = ArticleFixtureFactory.make_article_source()
        data["bibjson"]["identifier"] = []
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # no issns specified
        data["bibjson"]["identifier"] = [{"type" : "wibble", "id": "alksdjfas"}]
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # issns the same (but not normalised the same)
        data["bibjson"]["identifier"] = [{"type" : "pissn", "id": "12345678"}, {"type" : "eissn", "id": "1234-5678"}]
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # too many keywords
        data = ArticleFixtureFactory.make_article_source()
        data["bibjson"]["keywords"] = ["one", "two", "three", "four", "five", "six", "seven"]
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

    def test_02_create_article_success(self):
        # set up all the bits we need
        data = ArticleFixtureFactory.make_article_source()
        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")

        # add a journal to the account
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(account.id)
        journal.save()
        time.sleep(1)

        # call create on the object (which will save it to the index)
        a = ArticlesCrudApi.create(data, account)

        # check that it got created with the right properties
        assert isinstance(a, models.Article)
        assert a.id != "abcdefghijk_article"
        assert a.created_date != "2000-01-01T00:00:00Z"
        assert a.last_updated != "2000-01-01T00:00:00Z"

        time.sleep(1)

        am = models.Article.pull(a.id)
        assert am is not None


    def test_03_create_article_fail(self):
        # if the account is dud
        with self.assertRaises(Api401Error):
            data = ArticleFixtureFactory.make_article_source()
            a = ArticlesCrudApi.create(data, None)

        # if the data is bust
        with self.assertRaises(Api400Error):
            account = models.Account()
            account.set_id("test")
            account.set_name("Tester")
            account.set_email("test@test.com")
            data = {"some" : {"junk" : "data"}}
            a = ArticlesCrudApi.create(data, account)

    def test_04_coerce(self):
        data = ArticleFixtureFactory.make_article_source()

        # first some successes
        data["bibjson"]["link"][0]["url"] = "http://www.example.com/this_location/here"     # protocol required
        data["bibjson"]["link"][0]["type"] = "fulltext"
        data["admin"]["in_doaj"] = False
        data["created_date"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        ia = IncomingArticleDO(data)
        assert isinstance(ia.bibjson.title, unicode)

        # now test some failures

        # an invalid urls
        data = ArticleFixtureFactory.make_article_source()
        data["bibjson"]["link"][0]["url"] = "Two streets down on the left"
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)
        data["bibjson"]["link"][0]["url"] = "www.example.com/this_location/here"
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # an invalid link type
        data = ArticleFixtureFactory.make_article_source()
        data["bibjson"]["link"][0]["type"] = "cheddar"
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # invalid bool
        data = ArticleFixtureFactory.make_article_source()
        data["admin"]["in_doaj"] = "Yes"
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # invalid date
        data = ArticleFixtureFactory.make_article_source()
        data["created_date"] = "Just yesterday"
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

    def test_05_outgoing_article_do(self):
        # make a blank one
        oa = OutgoingArticleDO()

        # make one from an incoming article model fixture
        data = ArticleFixtureFactory.make_article_source()
        ap = models.Article(**data)

        # add some history to the article (it doesn't matter what it looks like since it shouldn't be there at the other end)
        ap.add_history(bibjson={'Lorem': {'ipsum': 'dolor', 'sit': 'amet'}, 'consectetur': 'adipiscing elit.'})

        # Create the DataObject
        oa = OutgoingArticleDO.from_model(ap)

        # check that it does not contain information that it shouldn't
        assert oa.data.get("index") is None
        assert oa.data.get("history") is None

    def test_06_retrieve_article_success(self):
        # set up all the bits we need
        # add a journal to the account
        account = models.Account()
        account.set_id('test')
        account.set_name("Tester")
        account.set_email("test@test.com")
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(account.id)
        journal.save()
        time.sleep(1)

        data = ArticleFixtureFactory.make_article_source()
        ap = models.Article(**data)
        ap.save()
        time.sleep(1)

        # call retrieve on the object
        a = ArticlesCrudApi.retrieve(ap.id, account)

        # check that we got back the object we expected
        assert isinstance(a, OutgoingArticleDO)
        assert a.id == ap.id

    def test_07_retrieve_article_fail(self):
        # set up all the bits we need
        # add a journal to the account
        account = models.Account()
        account.set_id('test')
        account.set_name("Tester")
        account.set_email("test@test.com")
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(account.id)
        journal.save()
        time.sleep(1)

        data = ArticleFixtureFactory.make_article_source()
        ap = models.Article(**data)
        ap.save()
        time.sleep(1)

        # no user
        with self.assertRaises(Api401Error):
            a = ArticlesCrudApi.retrieve(ap.id, None)

        # wrong user
        account = models.Account()
        account.set_id("asdklfjaioefwe")
        with self.assertRaises(Api404Error):
            a = ArticlesCrudApi.retrieve(ap.id, account)

        # non-existant article
        account = models.Account()
        account.set_id(ap.id)
        with self.assertRaises(Api404Error):
            a = ArticlesCrudApi.retrieve("ijsidfawefwefw", account)

    def test_08_update_article_success(self):
        # set up all the bits we need
        account = models.Account()
        account.set_id('test')
        account.set_name("Tester")
        account.set_email("test@test.com")
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(account.id)
        journal.save()
        time.sleep(1)

        data = ArticleFixtureFactory.make_article_source()

        # call create on the object (which will save it to the index)
        a = ArticlesCrudApi.create(data, account)

        # let the index catch up
        time.sleep(1)

        # get a copy of the newly created version for use in assertions later
        created = models.Article.pull(a.id)

        # now make an updated version of the object
        data = ArticleFixtureFactory.make_article_source()
        data["bibjson"]["title"] = "An updated title"

        # call update on the object
        ArticlesCrudApi.update(a.id, data, account)

        # let the index catch up
        time.sleep(1)

        # get a copy of the updated version
        updated = models.Article.pull(a.id)

        # now check the properties to make sure the update tool
        assert updated.bibjson().title == "An updated title"
        assert updated.created_date == created.created_date
        assert updated.last_updated != created.last_updated
        assert updated.data['admin']['upload_id'] == created.data['admin']['upload_id']

    def test_09_update_article_fail(self):
        # set up all the bits we need
        account = models.Account()
        account.set_id('test')
        account.set_name("Tester")
        account.set_email("test@test.com")
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(account.id)
        journal.save()
        time.sleep(1)

        data = ArticleFixtureFactory.make_article_source()

        # call create on the object (which will save it to the index)
        a = ArticlesCrudApi.create(data, account)

        # let the index catch up
        time.sleep(1)

        # get a copy of the newly created version for use in assertions later
        created = models.Article.pull(a.id)

        # now make an updated version of the object
        data = ArticleFixtureFactory.make_article_source()
        data["bibjson"]["title"] = "An updated title"

        # call update on the object in various context that will fail

        # without an account
        with self.assertRaises(Api401Error):
            ArticlesCrudApi.update(a.id, data, None)

        # with the wrong account
        account.set_id("other")
        with self.assertRaises(Api404Error):
            ArticlesCrudApi.update(a.id, data, account)

        # on the wrong id
        account.set_id("test")
        with self.assertRaises(Api404Error):
            ArticlesCrudApi.update("adfasdfhwefwef", data, account)

    def test_10_delete_article_success(self):
        # set up all the bits we need
        account = models.Account()
        account.set_id('test')
        account.set_name("Tester")
        account.set_email("test@test.com")
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(account.id)
        journal.save()
        time.sleep(1)

        data = ArticleFixtureFactory.make_article_source()

        # call create on the object (which will save it to the index)
        a = ArticlesCrudApi.create(data, account)

        # let the index catch up
        time.sleep(1)

        # now delete it
        ArticlesCrudApi.delete(a.id, account)

        # let the index catch up
        time.sleep(1)

        ap = models.Article.pull(a.id)
        assert ap is None

    def test_11_delete_article_fail(self):
        # set up all the bits we need
        account = models.Account()
        account.set_id('test')
        account.set_name("Tester")
        account.set_email("test@test.com")
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(account.id)
        journal.save()
        time.sleep(1)

        data = ArticleFixtureFactory.make_article_source()

        # call create on the object (which will save it to the index)
        a = ArticlesCrudApi.create(data, account)

        # let the index catch up
        time.sleep(1)

        # call delete on the object in various context that will fail

        # without an account
        with self.assertRaises(Api401Error):
            ArticlesCrudApi.delete(a.id, None)

        # with the wrong account
        account.set_id("other")
        with self.assertRaises(Api404Error):
            ArticlesCrudApi.delete(a.id, account)

        # on the wrong id
        account.set_id("test")
        with self.assertRaises(Api404Error):
            ArticlesCrudApi.delete("adfasdfhwefwef", account)
