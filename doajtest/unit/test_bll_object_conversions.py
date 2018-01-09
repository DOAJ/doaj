from doajtest.helpers import DoajTestCase
from parameterized import parameterized, param
from doajtest.fixtures import JournalFixtureFactory, AccountFixtureFactory, ApplicationFixtureFactory

from copy import deepcopy

from portality.models import Journal, Account, Suggestion

from portality.bll import DOAJ
from portality.bll import exceptions


def load_j2a_cases():
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


def load_a2j_cases():
    update_request_reference = Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
    update_request_reference.set_id(update_request_reference.makeid())

    application_source = ApplicationFixtureFactory.make_application_source()

    ncj_source = deepcopy(application_source)
    del ncj_source["admin"]["current_journal"]
    no_current_journal = Suggestion(**ncj_source)

    cj_source = deepcopy(application_source)
    cj_source["admin"]["current_journal"] = update_request_reference.id
    with_current_journal = Suggestion(**cj_source)

    return [
        param("1", None, None, raises=exceptions.ArgumentException),
        param("2", None, True, raises=exceptions.ArgumentException),
        param("3", None, False, raises=exceptions.ArgumentException),
        param("4", no_current_journal, None, raises=exceptions.ArgumentException),
        param("5", no_current_journal, True, comparator=journal_matches),
        param("6", no_current_journal, False, comparator=journal_matches),
        param("7", with_current_journal, None, update_request_reference, raises=exceptions.ArgumentException),
        param("8", with_current_journal, True, update_request_reference, comparator=journal_matches),
        param("9", with_current_journal, False, update_request_reference, comparator=journal_matches)
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

def journal_matches(application, journal, manual_update, update_request_reference):
    assert isinstance(journal, Journal)
    jbj = journal.bibjson().data
    del jbj["active"]
    assert jbj == application.bibjson().data
    assert journal.contacts() == application.contacts()
    assert application.editor == journal.editor
    assert application.editor_group == journal.editor_group
    assert application.notes == journal.notes
    assert application.owner == journal.owner
    assert application.has_seal() is journal.has_seal()

    assert len(journal.related_applications) == 1
    assert journal.related_applications[0].get("application_id") == application.id
    assert journal.related_applications[0].get("date_accepted") is not None

    assert journal.is_in_doaj() is True

    if manual_update:
        assert journal.last_manual_update is not None and journal.last_manual_update != "1970-01-01T00:00:00Z"

    if update_request_reference:
        assert journal.id == update_request_reference.id
        assert journal.created_date == update_request_reference.created_date

class TestBLLObjectConversions(DoajTestCase):

    @parameterized.expand(load_j2a_cases)
    def test_01_journal_2_application(self, name, journal, account, raises=None, comparator=None):
        doaj = DOAJ()
        if raises is not None:
            with self.assertRaises(raises):
                doaj.journal_2_application(journal, account)
        elif comparator is not None:
            application = doaj.journal_2_application(journal, account)
            comparator(journal, application)
        else:
            assert False, "Specify either raises or comparator"

    @parameterized.expand(load_a2j_cases)
    def test_02_application_2_journal(self, name, application, manual_update, update_request_reference=None, raises=None, comparator=None):
        if update_request_reference is not None:
            update_request_reference.save(blocking=True)
        doaj = DOAJ()
        if raises is not None:
            with self.assertRaises(raises):
                doaj.application_2_journal(application, manual_update)
        elif comparator is not None:
            journal = doaj.application_2_journal(application, manual_update)
            comparator(application, journal, manual_update, update_request_reference)
        else:
            assert False, "Specify either raises or comparator"
