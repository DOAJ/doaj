from doajtest.helpers import DoajTestCase
from parameterized import parameterized, param
from doajtest.fixtures import JournalFixtureFactory, ApplicationFixtureFactory, AccountFixtureFactory
import uuid, time

from copy import deepcopy

from portality.models import Journal, Suggestion, Account

from portality.bll import DOAJ
from portality.bll import exceptions
from portality import lock


def load_journal_cases():
    account = Account(**AccountFixtureFactory.make_publisher_source())
    account.set_id(account.makeid())

    journal = Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
    journal.set_id(journal.makeid())

    wrong_id = uuid.uuid4()

    return [
        param("j_id_acc_lock", journal, journal.id, account, True, raises=lock.Locked),
        param("j_id_acc_nolock", journal, journal.id, account, False),
        param("j_id_noacc_nolock", journal, journal.id, None, False),
        param("j_noid_noacc_nolock", journal, None, None, False, raises=exceptions.ArgumentException),
        param("j_wid_noacc_nolock", journal, wrong_id, None, False),
        param("noj_id_noacc_nolock", None, journal.id, None, False),
        param("noj_noid_noacc_nolock", None, None, None, False, raises=exceptions.ArgumentException)
    ]


def load_application_cases():
    application = Suggestion(**ApplicationFixtureFactory.make_application_source())
    application.makeid()

    wrong_id = uuid.uuid4()

    return [
        param("no_app_no_id", None, None, raises=exceptions.ArgumentException),
        param("no_app", None, application.id),
        param("app_wrong_id", application, wrong_id),
        param("app_right_id", application, application.id)
    ]

class TestBLLGetters(DoajTestCase):

    @parameterized.expand(load_journal_cases)
    def test_01_get_journal(self, name, journal, journal_id, account, lock_journal, raises=None):

        if lock_journal:
            lock.lock("journal", journal.id, "someoneelse", blocking=True)

        doaj = DOAJ()

        if journal is not None:
            journal.save(blocking=True)

        if raises is not None:
            with self.assertRaises(raises):
                if account is None:
                    retrieved, _ = doaj.journal(journal_id)
                else:
                    retrieved, jlock = doaj.journal(journal_id, lock_journal=True, lock_account=account)
        else:
            if account is None:
                retrieved, _ = doaj.journal(journal_id)
                if retrieved is not None:
                    assert retrieved.data == journal.data
                else:
                    assert retrieved is None
            else:
                retrieved, jlock = doaj.journal(journal_id, lock_journal=True, lock_account=account)
                if retrieved is not None:
                    assert retrieved.data == journal.data
                else:
                    assert retrieved is None

                time.sleep(2)

                assert lock.has_lock("journal", journal_id, account.id)

    @parameterized.expand(load_application_cases)
    def test_02_get_application(self, name, application, application_id, raises=None):
        doaj = DOAJ()

        if application is not None:
            application.save(blocking=True)

        if raises is not None:
            with self.assertRaises(raises):
                retrieved = doaj.application(application_id)
        else:
            retrieved = doaj.application(application_id)
            if retrieved is not None:
                assert retrieved.data == application.data
            else:
                assert retrieved is None
