import time

from doajtest.helpers import DoajTestCase
from doajtest.fixtures.accounts import AccountFixtureFactory
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory

from portality import models
from portality.constants import APPLICATION_STATUSES_ALL
from portality.scripts.accounts_delete_pub_no_journal_or_application import accounts_with_no_journals_or_applications


class TestScriptsAccountsDeletePubNoJournal(DoajTestCase):

    def setUp(self):
        super(TestScriptsAccountsDeletePubNoJournal, self).setUp()

    def test_01_dont_delete_if_journal_exists(self):
        """ Ensure the script doesn't delete accounts that own a journal """

        account_blocklist = []
        journal_blocklist = []

        # Create accounts without journals attached
        expected_deletes = []
        for i in range(10):
            pubsource = AccountFixtureFactory.make_publisher_source()
            pubaccount = models.Account(**pubsource)
            pubaccount.set_id()
            expected_deletes.append(pubaccount.id)
            pubaccount.save()
            account_blocklist.append((pubaccount.id, pubaccount.last_updated))

        # Create accounts with journals
        for i in range(5):
            pubsource = AccountFixtureFactory.make_publisher_source()
            pubaccount = models.Account(**pubsource)
            pubaccount.set_id()
            pubaccount.save()
            account_blocklist.append((pubaccount.id, pubaccount.last_updated))

            # Attach a journal, some in doaj and some not
            jsource = JournalFixtureFactory.make_journal_source(in_doaj=bool(i % 2))
            j = models.Journal(**jsource)
            j.set_id()
            j.set_owner(pubaccount.id)
            j.save()
            journal_blocklist.append((j.id, j.last_updated))

        models.Account.blockall(account_blocklist)
        models.Journal.blockall(journal_blocklist)

        # time.sleep(1)

        # Check we get the expected accounts to delete
        ids_to_delete = accounts_with_no_journals_or_applications()
        assert sorted(ids_to_delete) == sorted(expected_deletes)

        # Run the deletes
        models.Account.bulk_delete(ids_to_delete, refresh=True)
        models.Account.blockalldeleted(ids_to_delete)

        # Check we only have the accounts with journals remaining in the index
        assert len(models.Account.all()) == 5
        assert models.Account.pull(expected_deletes.pop()) is None

    def test_02_dont_delete_if_application_exists(self):
        """ After the application form redesign project accounts are created before the journal, so keep accounts with
        applications in the system """

        # Create accounts without applications attached
        expected_deletes = []
        for i in range(10):
            pubsource = AccountFixtureFactory.make_publisher_source()
            pubaccount = models.Account(**pubsource)
            pubaccount.set_id()
            expected_deletes.append(pubaccount.id)
            pubaccount.save()

        # Create accounts with applications
        for i in range(len(APPLICATION_STATUSES_ALL)):
            pubsource = AccountFixtureFactory.make_publisher_source()
            pubaccount = models.Account(**pubsource)
            pubaccount.set_id()
            pubaccount.save()

            # Attach an application, various statuses
            asource = ApplicationFixtureFactory.make_application_source()
            a = models.Suggestion(**asource)
            a.set_id()
            a.set_owner(pubaccount.id)
            a.set_application_status(APPLICATION_STATUSES_ALL[i])
            a.save()

        time.sleep(1)

        # Check we get the expected accounts to delete
        ids_to_delete = accounts_with_no_journals_or_applications()
        assert sorted(ids_to_delete) == sorted(expected_deletes)

        # Run the deletes
        models.Account.bulk_delete(ids_to_delete, refresh=True)
        models.Account.blockalldeleted(ids_to_delete)

        # Check we only have the accounts with applications remaining in the index
        assert len(models.Account.all()) == len(APPLICATION_STATUSES_ALL)
        assert models.Account.pull(expected_deletes.pop()) is None

    def test_03_excluded_roles(self):
        """ Check accounts with roles we exclude from delete are retained despite no journals or applications """
        EXCLUDED_LIST = ['associate_editor', 'editor', 'admin', 'ultra_bulk_delete', 'jct_inprogress']

        sources = [
            AccountFixtureFactory.make_managing_editor_source(),
            AccountFixtureFactory.make_assed1_source(),
            AccountFixtureFactory.make_assed2_source(),
            AccountFixtureFactory.make_assed3_source(),
            AccountFixtureFactory.make_editor_source(),
        ]

        for s in sources:
            account = models.Account(**s)
            account.set_id()
            account.save()

        # Add a few publishers we expect to be deleted
        publishers = []
        for s2 in range(len(EXCLUDED_LIST)):
            pub_source = AccountFixtureFactory.make_publisher_source()
            pub = models.Account(**pub_source)
            pub.set_id()
            publishers.append(pub)
            pub.save()

        time.sleep(1)

        # Check we get the publishers back when we run the script
        ids_to_delete = accounts_with_no_journals_or_applications()
        assert sorted(ids_to_delete) == sorted([p.id for p in publishers])

        # Add a reserved role to each publisher so they won't be returned next time
        for i in range(0, len(publishers)):
            publisher = publishers[i]
            publisher.add_role(EXCLUDED_LIST[i])
            publisher.save(blocking=True)

        ids_to_delete = accounts_with_no_journals_or_applications()
        assert len(ids_to_delete) == 0
