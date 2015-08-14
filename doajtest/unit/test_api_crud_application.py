from doajtest.helpers import DoajTestCase
from portality.lib.dataobj import DataObj, DataStructureException
from portality.api.v1.data_objects import IncomingApplication
from portality.api.v1 import ApplicationsCrudApi, Api401Error, Api400Error
from portality import models
from datetime import datetime
from doajtest.fixtures import ApplicationFixtureFactory
import time

class TestCrudApplication(DoajTestCase):

    def setUp(self):
        super(TestCrudApplication, self).setUp()

    def tearDown(self):
        super(TestCrudApplication, self).tearDown()

    def test_01_incoming_application_do(self):
        # make a blank one
        ia = IncomingApplication()

        # make one from an incoming application model fixture
        data = ApplicationFixtureFactory.incoming_application()
        ia = IncomingApplication(data)

        # FIXME: this bit doesn't yet work - dataobj refactor required
        # make another one that's broken
        #data = ApplicationFixtureFactory.incoming_application()
        #del data["bibjson"]["title"]
        #with self.assertRaises(DataStructureException):
        #    ia = IncomingApplication(data)

        # now progressively remove the conditionally required/advanced validation stuff
        #
        # missing identifiers
        data = ApplicationFixtureFactory.incoming_application()
        data["bibjson"]["identifier"] = []
        with self.assertRaises(DataStructureException):
            ia = IncomingApplication(data)

        # no issns specified
        data["bibjson"]["identifier"] = [{"type" : "wibble", "id": "alksdjfas"}]
        with self.assertRaises(DataStructureException):
            ia = IncomingApplication(data)

        # issns the same (but not normalised the same)
        data["bibjson"]["identifier"] = [{"type" : "pissn", "id": "12345678"}, {"type" : "eissn", "id": "1234-5678"}]
        with self.assertRaises(DataStructureException):
            ia = IncomingApplication(data)

        # no homepage link
        data = ApplicationFixtureFactory.incoming_application()
        data["bibjson"]["link"] = [{"type" : "awaypage", "url": "http://there"}]
        with self.assertRaises(DataStructureException):
            ia = IncomingApplication(data)

        # plagiarism detection but no url
        data = ApplicationFixtureFactory.incoming_application()
        data["bibjson"]["plagiarism_detection"] = {"detection" : True}
        with self.assertRaises(DataStructureException):
            ia = IncomingApplication(data)

        # embedded licence but no url
        data = ApplicationFixtureFactory.incoming_application()
        data["bibjson"]["license"][0]["embedded"] = True
        del data["bibjson"]["license"][0]["embedded_example_url"]
        with self.assertRaises(DataStructureException):
            ia = IncomingApplication(data)

        # author copyright and no link
        data = ApplicationFixtureFactory.incoming_application()
        data["bibjson"]["author_copyright"]["copyright"] = True
        del data["bibjson"]["author_copyright"]["url"]
        with self.assertRaises(DataStructureException):
            ia = IncomingApplication(data)

        # author publishing rights and no ling
        data = ApplicationFixtureFactory.incoming_application()
        data["bibjson"]["author_publishing_rights"]["publishing_rights"] = True
        del data["bibjson"]["author_publishing_rights"]["url"]
        with self.assertRaises(DataStructureException):
            ia = IncomingApplication(data)

    def test_02_create_application_success(self):
        # set up all the bits we need
        data = ApplicationFixtureFactory.incoming_application()
        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")

        # call create on the object (which will save it to the index)
        a = ApplicationsCrudApi.create(data, account)

        # check that it got created with the right properties
        assert isinstance(a, models.Suggestion)
        assert a.id is not None
        assert a.suggester.get("name") == "Tester"
        assert a.suggester.get("email") == "test@test.com"
        assert a.owner == "test"
        assert a.suggested_on is not None

        time.sleep(2)

        s = models.Suggestion.pull(a.id)
        assert s is not None

    def test_03_create_application_fail(self):
        # if the account is dud
        with self.assertRaises(Api401Error):
            data = ApplicationFixtureFactory.incoming_application()
            a = ApplicationsCrudApi.create(data, None)

        # if the data is bust
        with self.assertRaises(Api400Error):
            account = models.Account()
            account.set_id("test")
            account.set_name("Tester")
            account.set_email("test@test.com")
            data = {"some" : {"junk" : "data"}}
            a = ApplicationsCrudApi.create(data, account)
