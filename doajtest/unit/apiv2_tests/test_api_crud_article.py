from doajtest.helpers import DoajTestCase
from portality.lib.dataobj import DataStructureException
from portality.api.v2.data_objects.article import IncomingArticleDO, OutgoingArticleDO
from portality.api.v2 import ArticlesCrudApi, Api401Error, Api400Error, Api404Error
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

        # and one with an author email, which we have removed from the allowed fields recently. It should silently prune
        data = ArticleFixtureFactory.make_article_source()
        data["bibjson"]["author"][0]["email"] = "author@example.com"
        ia = IncomingArticleDO(data)
        assert "author@example.com" not in ia.json()

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

        #incorrect orcid format
        data = ArticleFixtureFactory.make_article_source()
        data["bibjson"]["author"] = [
            {
                "name" : "The Author",
                "affiliation" : "University Cottage Labs",
                "orcid_id" : "orcid.org/0000-0001-1234-1234"
            },
        ]
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # incorrect doi format
        data = ArticleFixtureFactory.make_article_source()
        data["bibjson"]["identifier"] = [
            {
                "id": "wrong-doi-format",
                "type": "doi"

            },
        ]
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        #another example
        data = ArticleFixtureFactory.make_article_source()
        data["bibjson"]["author"] = [
            {
                "name": "The Author",
                "affiliation": "University Cottage Labs",
                "orcid_id": "0000-0001-1234-123a"
            },
        ]
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)


    def test_02_create_article_success(self):
        # set up all the bits we need
        data = ArticleFixtureFactory.make_incoming_api_article()
        data['bibjson']['journal']['publisher'] = 'Wrong Publisher'
        data['bibjson']['journal']['title'] = 'Wrong Journal Title'
        data['bibjson']['journal']['license'] = [
            {
                "title" : "BAD LICENSE",
                "type" : "GOOD DOG",
                "url" : "Lala land",
                "version" : "XI",
                "open_access": False
            }
        ]
        data['bibjson']['journal']['language'] = ["ES", "These aren't even", "lang codes"]
        data['bibjson']['journal']['country'] = "This better not work"

        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")

        # add a journal to the account
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(account.id)
        # make sure non-overwritable journal metadata matches the article
        journal.bibjson().title = "The Title"
        journal.bibjson().publisher = "The Publisher"
        journal.bibjson().remove_licenses()
        journal.bibjson().add_license(
            **{
                "license_type" : "CC BY",
                "url" : "http://license.example.com"
            }
        )
        journal.bibjson().country = "US"
        journal.bibjson().set_language(["EN", "FR"])
        journal.save()
        time.sleep(1)

        # call create on the object (which will save it to the index)
        a = ArticlesCrudApi.create(data, account)

        # check that it got created with the right properties
        assert isinstance(a, models.Article)
        assert a.id != "abcdefghijk_article"
        assert a.created_date != "2000-01-01T00:00:00Z"
        assert a.last_updated != "2000-01-01T00:00:00Z"
        # allowed to overwrite these
        assert a.bibjson().start_page == '3'
        assert a.bibjson().end_page == '21'
        assert a.bibjson().volume == '1'
        assert a.bibjson().number == '99'
        # but none of these - these should all be the same as the original article in the index
        assert a.bibjson().publisher == 'The Publisher', a.bibjson().publisher
        assert a.bibjson().journal_title == 'The Title'
        assert a.bibjson().get_journal_license() == {
            "title" : "CC BY",
            "type" : "CC BY",
            "url" : "http://license.example.com"
        }
        assert a.bibjson().journal_language == ["EN", "FR"]
        assert a.bibjson().journal_country == "US"

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

        # TODO add test for when you're trying to create an article for a journal not owned by you

    def test_04_coerce(self):
        data = ArticleFixtureFactory.make_article_source()

        # first some successes
        data["bibjson"]["link"][0]["url"] = "http://www.example.com/this_location/here"     # protocol required
        data["bibjson"]["link"][0]["type"] = "fulltext"
        data["admin"]["in_doaj"] = False
        data["created_date"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        ia = IncomingArticleDO(data)
        assert isinstance(ia.bibjson.title, str)

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

        # call retrieve on the object with a valid user
        a = ArticlesCrudApi.retrieve(ap.id, account)

        # call retrieve with no user (will return if in_doaj is True)
        a = ArticlesCrudApi.retrieve(ap.id, None)

        # check that we got back the object we expected
        assert isinstance(a, OutgoingArticleDO)
        assert a.id == ap.id
        assert a.bibjson.journal.start_page == '3', a.bibjson.journal.start_page
        assert a.bibjson.journal.end_page == '21'
        assert a.bibjson.journal.volume == '1'
        assert a.bibjson.journal.number == '99'
        assert a.bibjson.journal.publisher == 'The Publisher', a.bibjson().publisher
        assert a.bibjson.journal.title == 'The Title'
        assert a.bibjson.journal.license[0].title == "CC BY"
        assert a.bibjson.journal.license[0].type == "CC BY"
        assert a.bibjson.journal.license[0].url == "http://license.example.com"
        assert a.bibjson.journal.license[0].version == "1.0"
        assert a.bibjson.journal.license[0].open_access == True
        assert a.bibjson.journal.language == ["EN", "FR"]
        assert a.bibjson.journal.country == "US"

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
        data['admin']['in_doaj'] = False
        ap = models.Article(**data)
        ap.save()
        time.sleep(1)

        # should fail when no user and in_doaj is False
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
        # make sure non-overwritable journal metadata matches the article
        journal.bibjson().title = "The Title"
        journal.bibjson().publisher = "The Publisher"
        journal.bibjson().remove_licenses()
        journal.bibjson().add_license(
            **{
                "license_type" : "CC BY",
                "url" : "http://license.example.com"
            }
        )
        journal.bibjson().country = "US"
        journal.bibjson().set_language(["EN", "FR"])
        journal.save()
        time.sleep(1)

        data = ArticleFixtureFactory.make_incoming_api_article()

        # call create on the object (which will save it to the index)
        a = ArticlesCrudApi.create(data, account)

        # let the index catch up
        time.sleep(1)

        # get a copy of the newly created version for use in assertions later
        created = models.Article.pull(a.id)

        # now make an updated version of the object
        data = ArticleFixtureFactory.make_incoming_api_article()
        data["bibjson"]["title"] = "An updated title"
        # change things we are allowed to change
        data['bibjson']['journal']['start_page'] = 4
        data['bibjson']['journal']['end_page'] = 22
        data['bibjson']['journal']['volume'] = 2
        data['bibjson']['journal']['number'] = '100'

        # change things we are not allowed to change
        data['bibjson']['journal']['publisher'] = 'Wrong Publisher'
        data['bibjson']['journal']['title'] = 'Wrong Journal Title'
        data['bibjson']['journal']['license'] = [
            {
                "title" : "BAD LICENSE",
                "type" : "GOOD DOG",
                "url" : "Lala land",
            }
        ]
        data['bibjson']['journal']['language'] = ["ES", "These aren't even", "lang codes"]
        data['bibjson']['journal']['country'] = "This better not work"

        # call update on the object
        a2 = ArticlesCrudApi.update(a.id, data, account)
        assert a2 != a

        # let the index catch up
        time.sleep(1)

        # get a copy of the updated version
        updated = models.Article.pull(a.id)

        # now check the properties to make sure the update took
        assert updated.bibjson().title == "An updated title"
        assert updated.created_date == created.created_date
        assert updated.last_updated != created.last_updated

        # allowed to overwrite these
        assert updated.bibjson().start_page == '4'
        assert updated.bibjson().end_page == '22'
        assert updated.bibjson().volume == '2'
        assert updated.bibjson().number == '100'
        # but none of these - these should all be the same as the original article in the index
        assert updated.bibjson().publisher == 'The Publisher', updated.bibjson().publisher
        assert updated.bibjson().journal_title == 'The Title'
        assert updated.bibjson().get_journal_license() == {
            "title" : "CC BY",
            "type" : "CC BY",
            "url" : "http://license.example.com"
        }
        assert updated.bibjson().journal_language == ["EN", "FR"]
        assert updated.bibjson().journal_country == "US"

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

    def test_12_too_many_keywords(self):
        """ Check we get an error when we supply too many keywords to the API. """

        # set up all the bits we need
        account = models.Account()
        account.set_id('test')
        account.set_name("Tester")
        account.set_email("test@test.com")
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(account.id)
        journal.save(blocking=True)

        data = ArticleFixtureFactory.make_article_source()
        data['bibjson']['keywords'] = ['one', 'two', 'three', 'four', 'five', 'six', 'seven']

        with self.assertRaises(Api400Error):
            ArticlesCrudApi.create(data, account)

    def test_13_trim_empty_string_data(self):

        data = ArticleFixtureFactory.make_article_source()
        data["bibjson"]["title"] = ""
        data["bibjson"]["year"] = ""
        data["bibjson"]["month"] = ""
        data["bibjson"]["abstract"] = ""
        authors_nr = len(data["bibjson"]["author"][0])
        data["bibjson"]["author"][0]["name"] = ""
        subject_nr = len(data["bibjson"]["subject"])
        data["bibjson"]["subject"][0]["term"] = ""
        ids_nr = len(data["bibjson"]["identifier"])
        data["bibjson"]["identifier"][0]["id"] = ""
        links_nr = len(data["bibjson"]["link"])
        data["bibjson"]["link"][0]["url"] = ""
        keywords_nr = len(data["bibjson"]["keywords"])
        data["bibjson"]["keywords"][0] = ""

        ia = IncomingArticleDO(data)
        bibjson = ia.data["bibjson"]
        assert not "title" in "bibjson"
        assert not "year" in "bibjson"
        assert not "month" in "bibjson"
        assert not "abstract" in "bibjson"
        assert not "author" in "bibjson"
        assert len(bibjson["subject"]) == subject_nr-1
        assert len(bibjson["identifier"]) == ids_nr-1
        assert len(bibjson["link"]) == links_nr-1
        assert len(bibjson["keywords"]) == keywords_nr-1

