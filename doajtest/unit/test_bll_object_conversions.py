from doajtest.helpers import DoajTestCase
from parameterized import parameterized, param
from doajtest.fixtures import JournalFixtureFactory, AccountFixtureFactory

from copy import deepcopy

from portality.models import Journal, Account, Suggestion

from portality.bll import DOAJ
from portality.bll import exceptions


def load_test_cases():
    journal = Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
    account_source = AccountFixtureFactory.make_publisher_source()

    owner_account = Account(**deepcopy(account_source))
    owner_account.set_id(journal.owner)

    non_owner_publisher = Account(**deepcopy(account_source))

    non_publisher = Account(**deepcopy(account_source))
    non_publisher.remove_role("publisher")

    admin = Account(**deepcopy(account_source))
    admin.add_role("admin")

    return [
        param("no_journal_no_account", None, None, raises=exceptions.ArgumentException),
        param("no_journal_with_account", None, owner_account, raises=exceptions.ArgumentException),
        param("journal_no_account", journal, None, comparator=application_matches),
        param("journal_matching_account", journal, owner_account, comparator=application_matches),
        param("journal_unmatched_account", journal, non_owner_publisher, raises=exceptions.AuthoriseException),
        param("journal_non_publisher_account", journal, non_publisher, raises=exceptions.AuthoriseException),
        param("journal_admin_account", journal, admin, comparator=application_matches)
    ]


def application_matches(journal, application):
    assert isinstance(application, Suggestion)
    assert journal.bibjson().data == application.bibjson().data
    assert application.application_status == "update_request"
    assert journal.contacts() == application.contacts()
    assert application.current_journal == journal.id
    assert application.editor == journal.editor
    assert application.editor_group == journal.editor_group
    assert application.notes == journal.notes
    assert application.owner == journal.owner
    assert application.has_seal() is journal.has_seal()
    assert application.suggester == journal.contacts()[0]


class TestBLLObjectConversions(DoajTestCase):

    @parameterized.expand(load_test_cases)
    def test_01_journal_2_application(self, name, journal, account, raises=None, comparator=None):
        doaj = DOAJ()
        if raises is not None:
            with self.assertRaises(raises):
                doaj.journal_2_application(journal, account)
        elif comparator is not None:
            application = doaj.journal_2_application(journal, account)
            application_matches(journal, application)
        else:
            assert False, "Specify either raises or comparator"
