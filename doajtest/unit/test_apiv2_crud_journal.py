from doajtest.helpers import DoajTestCase
from portality.api.v2.data_objects.journal import OutgoingJournal
from portality.api.v2.crud.journals import JournalsCrudApi, Api401Error, Api404Error
from portality import models
from doajtest.fixtures.v2.journals import JournalFixtureFactory
import time


class TestCrudJournal(DoajTestCase):

    def setUp(self):
        super(TestCrudJournal, self).setUp()

    def tearDown(self):
        super(TestCrudJournal, self).tearDown()

    def test_01_outgoing_journal_do(self):
        # make a blank one successfully
        oj = OutgoingJournal()

        # make one from an incoming journal model fixture
        data = JournalFixtureFactory.make_journal_source()
        j = models.Journal(**data)
        oj = OutgoingJournal.from_model(j)

        # check that it does not contain information that it shouldn't
        assert oj.data.get("index") is None, "index: {}".format(oj.data.get("index"))
        assert oj.data.get("history") is None, "history: {}".format(oj.data.get("history"))
        assert oj.data.get("admin", {}).get("active") is None, "active: {}".format(oj.data.get("admin", {}).get("active"))
        assert oj.data.get("admin", {}).get("notes") is None, "notes: {}".format(oj.data.get("admin", {}).get("notes"))
        assert oj.data.get("admin", {}).get("editor_group") is None, "editor_group: {}".format(oj.data.get("admin", {}).get("editor_group"))
        assert oj.data.get("admin", {}).get("editor") is None, "editor: {}".format(oj.data.get("admin", {}).get("editor"))

    def test_02_outgoing_journal_urls(self):
        """ We've relaxed the URL constraints for outgoing journals - https://github.com/DOAJ/doajPM/issues/2268 """

        data = JournalFixtureFactory.make_journal_source()

        # Even with all of the dodgy URLS above, we should still have a successful OutgoingJournal object.
        j = models.Journal(**data)
        bjson = j.bibjson()
        invalid_url = 'an invalid url $321 >>,'
        bjson.other_charges_url = invalid_url
        bjson.editorial_review_url = invalid_url
        bjson.plagiarism_url = invalid_url
        bjson.copyright_url = invalid_url
        bjson.journal_url = invalid_url
        j.save(blocking=True)

        OutgoingJournal.from_model(j)

    def test_03_retrieve_public_journal_success(self):
        # set up all the bits we need
        data = JournalFixtureFactory.make_journal_source(in_doaj=True)
        j = models.Journal(**data)
        j.save()
        time.sleep(2)
        
        a = JournalsCrudApi.retrieve(j.id, account=None)
        # check that we got back the object we expected
        assert isinstance(a, OutgoingJournal)
        assert a.data["id"] == j.id
        
        # it should also work if we're logged in with the owner or another user
        # owner first
        account = models.Account()
        account.set_id(j.owner)
        account.set_name("Tester")
        account.set_email("test@test.com")
        
        a = JournalsCrudApi.retrieve(j.id, account)

        assert isinstance(a, OutgoingJournal)
        assert a.data["id"] == j.id
        
        # try with another account
        not_owner = models.Account()
        not_owner.set_id("asdklfjaioefwe")
        a = JournalsCrudApi.retrieve(j.id, not_owner)
        assert isinstance(a, OutgoingJournal)
        assert a.data["id"] == j.id

    def test_04_retrieve_public_journal_fail(self):
        with self.assertRaises(Api404Error):
            a = JournalsCrudApi.retrieve("ijsidfawefwefw", account=None)

    def test_05_retrieve_private_journal_success(self):
        # set up all the bits we need
        data = JournalFixtureFactory.make_journal_source()
        j = models.Journal(**data)
        j.save()
        time.sleep(2)

        account = models.Account()
        account.set_id(j.owner)
        account.set_name("Tester")
        account.set_email("test@test.com")

        # call retrieve on the object
        a = JournalsCrudApi.retrieve(j.id, account)

        # check that we got back the object we expected
        assert isinstance(a, OutgoingJournal)
        assert a.data["id"] == j.id

    def test_06_retrieve_private_journal_fail(self):
        # set up all the bits we need
        data = JournalFixtureFactory.make_journal_source(in_doaj=False)
        j = models.Journal(**data)
        j.save()
        time.sleep(2)

        # no user
        with self.assertRaises(Api401Error):
            a = JournalsCrudApi.retrieve(j.id, None)

        # wrong user
        account = models.Account()
        account.set_id("asdklfjaioefwe")
        with self.assertRaises(Api404Error):
            a = JournalsCrudApi.retrieve(j.id, account)

        # non-existant journal
        account = models.Account()
        account.set_id(j.id)
        with self.assertRaises(Api404Error):
            a = JournalsCrudApi.retrieve("ijsidfawefwefw", account)
