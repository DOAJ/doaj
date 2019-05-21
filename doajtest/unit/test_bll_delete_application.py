import time

from parameterized import parameterized

from portality import constants
from doajtest.fixtures import JournalFixtureFactory, AccountFixtureFactory, ApplicationFixtureFactory
from doajtest.helpers import DoajTestCase, load_from_matrix
from portality import lock
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.models import Journal, Account, Suggestion


def load_parameter_sets():
    return load_from_matrix("delete_application.csv", test_ids=[])

EXCEPTIONS = {
    "ArgumentException" : exceptions.ArgumentException,
    "Locked" : lock.Locked,
    "AuthoriseException" : exceptions.AuthoriseException,
    "NoSuchObjectException" : exceptions.NoSuchObjectException
}

def check_locks(application, cj, rj, account):
    if account is None:
        return
    account_id = account.id
    application_id = None
    cj_id = None
    rj_id = None
    if application is not None: application_id = application.id
    if cj is not None: cj_id = cj.id
    if rj is not None: rj_id = rj.id

    if application_id is not None:
        assert not lock.has_lock(constants.LOCK_APPLICATION, application_id, account_id)
    if cj_id is not None:
        assert not lock.has_lock(constants.LOCK_JOURNAL, cj_id, account_id)
    if rj_id is not None:
        assert not lock.has_lock(constants.LOCK_JOURNAL, rj_id, account_id)

class TestBLLDeleteApplication(DoajTestCase):

    def setUp(self):
        super(TestBLLDeleteApplication, self).setUp()
        self.old_journal_save = Journal.save

    def tearDown(self):
        super(TestBLLDeleteApplication, self).tearDown()
        Journal.save = self.old_journal_save

    @parameterized.expand(load_parameter_sets)
    def test_01_delete_application(self, name, application_type, account_type, current_journal, related_journal, raises):

        ###############################################
        ## set up

        # create the test application (if needed), and the associated current_journal and related_journal in suitable states
        application = None
        cj = None
        rj = None
        if application_type == "found" or application_type == "locked":
            application = Suggestion(**ApplicationFixtureFactory.make_application_source())

            if current_journal == "none":
                application.remove_current_journal()
            elif current_journal == "not_found":
                application.set_current_journal("123456789987654321")
            elif current_journal == "found":
                cj = Journal(**JournalFixtureFactory.make_journal_source())
                cj.set_id(cj.makeid())
                cj.save(blocking=True)
                application.set_current_journal(cj.id)
            elif current_journal == "locked":
                cj = Journal(**JournalFixtureFactory.make_journal_source())
                cj.set_id(cj.makeid())
                cj.save(blocking=True)
                application.set_current_journal(cj.id)
                lock.lock(constants.LOCK_JOURNAL, cj.id, "otheruser")

            if related_journal == "none":
                application.remove_related_journal()
            elif related_journal == "not_found":
                application.set_related_journal("123456789987654321")
            elif related_journal == "found":
                rj = Journal(**JournalFixtureFactory.make_journal_source())
                rj.set_id(rj.makeid())
                rj.save(blocking=True)
                application.set_related_journal(rj.id)
            elif related_journal == "locked":
                rj = Journal(**JournalFixtureFactory.make_journal_source())
                rj.set_id(rj.makeid())
                rj.save(blocking=True)
                application.set_related_journal(rj.id)
                lock.lock(constants.LOCK_JOURNAL, rj.id, "otheruser")


        acc = None
        if account_type != "none":
            acc = Account(**AccountFixtureFactory.make_publisher_source())
            if account_type == "not_permitted":
                acc.remove_role("publisher")
            if application_type == "locked":
                thelock = lock.lock(constants.LOCK_APPLICATION, application.id, "otheruser")
                # we can't explicitly block on the lock, but we can halt until we confirm it is saved
                thelock.blockall([(thelock.id, thelock.last_updated)])

        application_id = None
        if application is not None:
            if acc is not None:
                application.set_owner(acc.id)
            application.save(blocking=True)
            application_id = application.id
        elif application_type == "not_found":
            application_id = u"sdjfasofwefkwflkajdfasjd"

        ###########################################################
        # Execution

        svc = DOAJ.applicationService()
        if raises != "":
            with self.assertRaises(EXCEPTIONS[raises]):
                svc.delete_application(application_id, acc)
            time.sleep(1)
            check_locks(application, cj, rj, acc)
        else:
            svc.delete_application(application_id, acc)

            # we need to sleep, so the index catches up
            time.sleep(1)

            # check that no locks remain set for this user
            check_locks(application, cj, rj, acc)

            # check that the application actually is gone
            if application is not None:
                assert Suggestion.pull(application.id) is None

            # check that the current journal no longer has a reference to the application
            if cj is not None:
                cj = Journal.pull(cj.id)
                assert cj.current_application is None

            # check that the related journal has a record that the application was deleted
            if rj is not None:
                rj = Journal.pull(rj.id)
                record = rj.related_application_record(application.id)
                assert "status" in record
                assert record["status"] == "deleted"


