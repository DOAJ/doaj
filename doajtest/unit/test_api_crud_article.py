from doajtest.helpers import DoajTestCase
from portality.lib.dataobj import DataObj, DataStructureException
from portality.api.v1.data_objects import IncomingArticleDO, OutgoingArticleDO
from portality.api.v1 import ArticlesCrudApi, Api401Error, Api400Error, Api404Error, Api403Error
from portality import models
from datetime import datetime
from doajtest.fixtures import ArticleFixtureFactory
import time

'''
class TestCrudArticle(DoajTestCase):

    def setUp(self):
        super(TestCrudArticle, self).setUp()

    def tearDown(self):
        super(TestCrudArticle, self).tearDown()

        def test_01_incoming_article_do(self):
        # make a blank one
        ia = IncomingArticleDO()

        # make one from an incoming article model fixture
        data = ArticleFixtureFactory.incoming_article()
        ia = IncomingArticleDO(data)

        # make another one that's broken
        data = ArticleFixtureFactory.incoming_article()
        del data["bibjson"]["title"]
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # now progressively remove the conditionally required/advanced validation stuff
        #
        # missing identifiers
        data = ArticleFixtureFactory.incoming_article()
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

        # no homepage link
        data = ArticleFixtureFactory.incoming_article()
        data["bibjson"]["link"] = [{"type" : "awaypage", "url": "http://there"}]
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # plagiarism detection but no url
        data = ArticleFixtureFactory.incoming_article()
        data["bibjson"]["plagiarism_detection"] = {"detection" : True}
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # embedded licence but no url
        data = ArticleFixtureFactory.incoming_article()
        data["bibjson"]["license"][0]["embedded"] = True
        del data["bibjson"]["license"][0]["embedded_example_url"]
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # author copyright and no link
        data = ArticleFixtureFactory.incoming_article()
        data["bibjson"]["author_copyright"]["copyright"] = True
        del data["bibjson"]["author_copyright"]["url"]
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # author publishing rights and no ling
        data = ArticleFixtureFactory.incoming_article()
        data["bibjson"]["author_publishing_rights"]["publishing_rights"] = True
        del data["bibjson"]["author_publishing_rights"]["url"]
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # invalid domain in archiving_policy
        data = ArticleFixtureFactory.incoming_article()
        data["bibjson"]["archiving_policy"]["policy"] = [{"domain" : "my house", "name" : "something"}]
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # invalid name in non-domained policy
        data = ArticleFixtureFactory.incoming_article()
        data["bibjson"]["archiving_policy"]["policy"] = [{"name" : "something"}]
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # too many keywords
        data = ArticleFixtureFactory.incoming_article()
        data["bibjson"]["keywords"] = ["one", "two", "three", "four", "five", "six", "seven"]
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

    def test_02_create_article_success(self):
        # set up all the bits we need
        data = ArticleFixtureFactory.incoming_article()
        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")

        # call create on the object (which will save it to the index)
        a = ArticlesCrudApi.create(data, account)

        # check that it got created with the right properties
        assert isinstance(a, models.Suggestion)
        assert a.id != "ignore_me"
        assert a.created_date != "2001-01-01T00:00:00Z"
        assert a.last_updated != "2001-01-01T00:00:00Z"
        assert a.suggester.get("name") == "Tester"
        assert a.suggester.get("email") == "test@test.com"
        assert a.owner == "test"
        assert a.suggested_on is not None

        # also, because it's a special case, check the archiving_policy
        archiving_policy = a.bibjson().archiving_policy
        assert len(archiving_policy.get("policy")) == 4
        lcount = 0
        scount = 0
        for ap in archiving_policy.get("policy"):
            if isinstance(ap, list):
                lcount += 1
                assert ap[0] in ["A national library", "Other"]
                assert ap[1] in ["Trinity", "A safe place"]
            else:
                scount += 1
        assert lcount == 2
        assert scount == 2
        assert "CLOCKSS" in archiving_policy.get("policy")
        assert "LOCKSS" in archiving_policy.get("policy")

        time.sleep(2)

        s = models.Suggestion.pull(a.id)
        assert s is not None

    def test_03_create_article_fail(self):
        # if the account is dud
        with self.assertRaises(Api401Error):
            data = ArticleFixtureFactory.incoming_article()
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
        data = ArticleFixtureFactory.incoming_article()

        # first test a load of successes
        data["bibjson"]["country"] = "Bangladesh"
        data["bibjson"]["apc"]["currency"] = "Taka"
        data["bibjson"]["allows_fulltext_indexing"] = "true"
        data["bibjson"]["publication_time"] = "15"
        data["bibjson"]["language"] = ["French", "English"]
        data["bibjson"]["persistent_identifier_scheme"] = ["doi", "HandleS", "something"]
        data["bibjson"]["format"] = ["pdf", "html", "doc"]
        data["bibjson"]["license"][0]["title"] = "cc by"
        data["bibjson"]["license"][0]["type"] = "CC by"
        data["bibjson"]["deposit_policy"] = ["sherpa/romeo", "other"]

        ia = IncomingArticleDO(data)

        assert ia.bibjson.country == "BD"
        assert ia.bibjson.apc.currency == "BDT"
        assert ia.bibjson.allows_fulltext_indexing is True
        assert isinstance(ia.bibjson.title, unicode)
        assert ia.bibjson.publication_time == 15
        assert "fr" in ia.bibjson.language
        assert "en" in ia.bibjson.language
        assert len(ia.bibjson.language) == 2
        assert ia.bibjson.persistent_identifier_scheme[0] == "DOI"
        assert ia.bibjson.persistent_identifier_scheme[1] == "Handles"
        assert ia.bibjson.persistent_identifier_scheme[2] == "something"
        assert ia.bibjson.format[0] == "PDF"
        assert ia.bibjson.format[1] == "HTML"
        assert ia.bibjson.format[2] == "doc"
        assert ia.bibjson.license[0].title == "CC BY"
        assert ia.bibjson.license[0].type == "CC BY"
        assert ia.bibjson.deposit_policy[0] == "Sherpa/Romeo"
        assert ia.bibjson.deposit_policy[1] == "other"

        # now test some failures
        # invalid country name
        data = ArticleFixtureFactory.incoming_article()
        data["bibjson"]["country"] = "LandLand"
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # invalid currency name
        data = ArticleFixtureFactory.incoming_article()
        data["bibjson"]["apc"]["currency"] = "Wonga"
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # an invalid url
        data = ArticleFixtureFactory.incoming_article()
        data["bibjson"]["apc_url"] = "Two streets down on the left"
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # invalid bool
        data = ArticleFixtureFactory.incoming_article()
        data["bibjson"]["allows_fulltext_indexing"] = "Yes"
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # invalid int
        data = ArticleFixtureFactory.incoming_article()
        data["bibjson"]["publication_time"] = "Fifteen"
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

        # invalid language code
        data = ArticleFixtureFactory.incoming_article()
        data["bibjson"]["language"] = ["Hagey Pagey"]
        with self.assertRaises(DataStructureException):
            ia = IncomingArticleDO(data)

    def test_05_outgoing_article_do(self):
        # make a blank one
        oa = OutgoingArticleDO()

        # make one from an incoming article model fixture
        data = ArticleFixtureFactory.make_article_source()
        ap = models.Suggestion(**data)
        oa = OutgoingArticleDO.from_model(ap)

        # check that it does not contain information that it shouldn't
        assert oa.data.get("index") is None
        assert oa.data.get("history") is None
        assert oa.data.get("admin", {}).get("notes") is None
        assert oa.data.get("admin", {}).get("editor_group") is None
        assert oa.data.get("admin", {}).get("editor") is None
        assert oa.data.get("admin", {}).get("seal") is None

    def test_06_retrieve_article_success(self):
        # set up all the bits we need
        data = ArticleFixtureFactory.make_article_source()
        ap = models.Suggestion(**data)
        ap.save()
        time.sleep(2)

        account = models.Account()
        account.set_id(ap.owner)
        account.set_name("Tester")
        account.set_email("test@test.com")

        # call retrieve on the object
        a = ArticlesCrudApi.retrieve(ap.id, account)

        # check that we got back the object we expected
        assert isinstance(a, OutgoingArticleDO)
        assert a.id == ap.id

    def test_07_retrieve_article_fail(self):
        # set up all the bits we need
        data = ArticleFixtureFactory.make_article_source()
        ap = models.Suggestion(**data)
        ap.save()
        time.sleep(2)

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
        data = ArticleFixtureFactory.incoming_article()
        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")

        # call create on the object (which will save it to the index)
        a = ArticlesCrudApi.create(data, account)

        # let the index catch up
        time.sleep(2)

        # get a copy of the newly created version for use in assertions later
        created = models.Suggestion.pull(a.id)

        # now make an updated version of the object
        data = ArticleFixtureFactory.incoming_article()
        data["bibjson"]["title"] = "An updated title"

        # call update on the object
        ArticlesCrudApi.update(a.id, data, account)

        # let the index catch up
        time.sleep(2)

        # get a copy of the updated version
        updated = models.Suggestion.pull(a.id)

        # now check the properties to make sure the update tool
        assert updated.bibjson().title == "An updated title"
        assert updated.created_date == created.created_date

    def test_09_update_article_fail(self):
        # set up all the bits we need
        data = ArticleFixtureFactory.incoming_article()
        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")

        # call create on the object (which will save it to the index)
        a = ArticlesCrudApi.create(data, account)

        # let the index catch up
        time.sleep(2)

        # get a copy of the newly created version for use in assertions later
        created = models.Suggestion.pull(a.id)

        # now make an updated version of the object
        data = ArticleFixtureFactory.incoming_article()
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

        # on one with a disallowed workflow status
        created.set_article_status("accepted")
        created.save()
        time.sleep(2)

        with self.assertRaises(Api403Error):
            ArticlesCrudApi.update(a.id, data, account)

    def test_10_delete_article_success(self):
        # set up all the bits we need
        data = ArticleFixtureFactory.incoming_article()
        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")

        # call create on the object (which will save it to the index)
        a = ArticlesCrudApi.create(data, account)

        # let the index catch up
        time.sleep(2)

        # now delete it
        ArticlesCrudApi.delete(a.id, account)

        # let the index catch up
        time.sleep(2)

        ap = models.Suggestion.pull(a.id)
        assert ap is None

    def test_11_delete_article_fail(self):
        # set up all the bits we need
        data = ArticleFixtureFactory.incoming_article()
        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")

        # call create on the object (which will save it to the index)
        a = ArticlesCrudApi.create(data, account)

        # let the index catch up
        time.sleep(2)

        # get a copy of the newly created version for use in test later
        created = models.Suggestion.pull(a.id)

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

        # on one with a disallowed workflow status
        created.set_article_status("accepted")
        created.save()
        time.sleep(2)

        with self.assertRaises(Api403Error):
            ArticlesCrudApi.delete(a.id, account)
'''
