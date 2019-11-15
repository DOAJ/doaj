from doajtest.helpers import DoajTestCase
from portality.api.v1.data_objects import OutgoingJournal
from portality.api.v1 import JournalsCrudApi, Api401Error, Api404Error
from portality import models
from doajtest.fixtures import JournalFixtureFactory
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
        data = JournalFixtureFactory.make_journal_source(include_obsolete_fields=True)
        j = models.Journal(**data)
        oj = OutgoingJournal.from_model(j)

        # check that it does not contain information that it shouldn't
        assert oj.data.get("index") is None
        assert oj.data.get("history") is None
        assert oj.data.get("admin", {}).get("active") is None
        assert oj.data.get("admin", {}).get("notes") is None
        assert oj.data.get("admin", {}).get("editor_group") is None
        assert oj.data.get("admin", {}).get("editor") is None

    def test_02_retrieve_public_journal_success(self):
        # set up all the bits we need
        data = JournalFixtureFactory.make_journal_source(in_doaj=True, include_obsolete_fields=True)
        j = models.Journal(**data)
        j.save()
        time.sleep(2)
        
        a = JournalsCrudApi.retrieve(j.id, account=None)
        # check that we got back the object we expected
        assert isinstance(a, OutgoingJournal)
        assert a.id == j.id
        
        # it should also work if we're logged in with the owner or another user
        # owner first
        account = models.Account()
        account.set_id(j.owner)
        account.set_name("Tester")
        account.set_email("test@test.com")
        
        a = JournalsCrudApi.retrieve(j.id, account)

        assert isinstance(a, OutgoingJournal)
        assert a.id == j.id
        
        # try with another account
        not_owner = models.Account()
        not_owner.set_id("asdklfjaioefwe")
        a = JournalsCrudApi.retrieve(j.id, not_owner)
        assert isinstance(a, OutgoingJournal)
        assert a.id == j.id

    def test_03_retrieve_public_journal_fail(self):
        with self.assertRaises(Api404Error):
            a = JournalsCrudApi.retrieve("ijsidfawefwefw", account=None)

    def test_04_retrieve_withdrawn_journal_fail(self):
        # set up all the bits we need
        data = JournalFixtureFactory.make_journal_source(in_doaj=False, include_obsolete_fields=True)
        j = models.Journal(**data)
        j.save(blocking=True)

        # there are various modes, they should all fail

        # no user
        with self.assertRaises(Api404Error):
            a = JournalsCrudApi.retrieve(j.id, None)

        # wrong user
        account = models.Account()
        account.set_id("asdklfjaioefwe")
        with self.assertRaises(Api404Error):
            a = JournalsCrudApi.retrieve(j.id, account)

        # the owner
        account = models.Account()
        account.set_id(j.owner)
        account.set_name("Tester")
        account.set_email("test@test.com")
        with self.assertRaises(Api404Error):
            a = JournalsCrudApi.retrieve(j.id, account)

        # non-existent journal
        account = models.Account()
        account.set_id(j.id)
        with self.assertRaises(Api404Error):
            a = JournalsCrudApi.retrieve("ijsidfawefwefw", account)

