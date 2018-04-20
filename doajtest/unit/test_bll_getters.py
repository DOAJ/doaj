import time
import uuid

from parameterized import parameterized, param

from portality import constants
from doajtest.fixtures import JournalFixtureFactory, ApplicationFixtureFactory, AccountFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import lock
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.models import Journal, Suggestion, Account


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
    account = Account(**AccountFixtureFactory.make_publisher_source())
    account.set_id(account.makeid())

    application = Suggestion(**ApplicationFixtureFactory.make_application_source())
    application.makeid()

    wrong_id = uuid.uuid4()

    return [
        param("a_id_acc_lock", application, application.id, account, True, raises=lock.Locked),
        param("a_id_acc_nolock", application, application.id, account, False),
        param("a_id_noacc_nolock", application, application.id, None, False),
        param("a_noid_noacc_nolock", application, None, None, False, raises=exceptions.ArgumentException),
        param("a_wid_noacc_nolock", application, wrong_id, None, False),
        param("noa_id_noacc_nolock", None, application.id, None, False),
        param("noa_noid_noacc_nolock", None, None, None, False, raises=exceptions.ArgumentException)
    ]


class TestBLLGetters(DoajTestCase):

    @parameterized.expand(load_journal_cases)
    def test_01_get_journal(self, name, journal, journal_id, account, lock_journal, raises=None):

        if lock_journal:
            lock.lock("journal", journal.id, "someoneelse", blocking=True)

        svc = DOAJ.journalService()

        if journal is not None:
            journal.save(blocking=True)

        if raises is not None:
            with self.assertRaises(raises):
                if account is None:
                    retrieved, _ = svc.journal(journal_id)
                else:
                    retrieved, jlock = svc.journal(journal_id, lock_journal=True, lock_account=account)
        else:
            if account is None:
                retrieved, _ = svc.journal(journal_id)
                if retrieved is not None:
                    assert retrieved.data == journal.data
                else:
                    assert retrieved is None
            else:
                retrieved, jlock = svc.journal(journal_id, lock_journal=True, lock_account=account)
                if retrieved is not None:
                    assert retrieved.data == journal.data
                else:
                    assert retrieved is None

                time.sleep(2)

                assert lock.has_lock("journal", journal_id, account.id)

    @parameterized.expand(load_application_cases)
    def test_02_get_application(self, name, application, application_id, account, lock_application, raises=None):
        if lock_application:
            lock.lock(constants.LOCK_APPLICATION, application.id, "someoneelse", blocking=True)

        svc = DOAJ.applicationService()

        if application is not None:
            application.save(blocking=True)

        if raises is not None:
            with self.assertRaises(raises):
                if account is None:
                    retrieved, _ = svc.application(application_id)
                else:
                    retrieved, jlock = svc.application(application_id, lock_application=True, lock_account=account)
        else:
            if account is None:
                retrieved, _ = svc.application(application_id)
                if retrieved is not None:
                    assert retrieved.data == application.data
                else:
                    assert retrieved is None
            else:
                retrieved, jlock = svc.application(application_id, lock_application=True, lock_account=account)
                if retrieved is not None:
                    assert retrieved.data == application.data
                else:
                    assert retrieved is None

                time.sleep(2)

                assert lock.has_lock(constants.LOCK_APPLICATION, application_id, account.id)
