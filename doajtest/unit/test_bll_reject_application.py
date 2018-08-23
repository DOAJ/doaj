import time

from parameterized import parameterized

from portality import constants
from doajtest.fixtures import ApplicationFixtureFactory, AccountFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase, load_from_matrix
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.models import Account, Suggestion, Provenance, Journal


def load_test_cases():
    return load_from_matrix("reject_application.csv", test_ids=["77"])


def mock_save_fail(*args, **kwargs):
    return None


EXCEPTIONS = {
    "ArgumentException" : exceptions.ArgumentException,
    "SaveException" : exceptions.SaveException,
    "AuthoriseException" : exceptions.AuthoriseException
}


class TestBLRejectApplication(DoajTestCase):

    def setUp(self):
        super(TestBLRejectApplication, self).setUp()
        self.old_save = Suggestion.save

    def tearDown(self):
        super(TestBLRejectApplication, self).tearDown()
        Suggestion.save = self.old_save

    @parameterized.expand(load_test_cases)
    def test_01_reject_application(self, name, application, application_status, account, prov, current_journal, note, save, raises=None):

        #######################################
        ## set up

        if save == "fail":
            Suggestion.save = mock_save_fail

        ap = None
        journal = None
        if application == "exists":
            ap = Suggestion(**ApplicationFixtureFactory.make_application_source())
            ap.set_application_status(application_status)
            ap.set_id(ap.makeid())
            ap.remove_notes()
            if current_journal == "yes":
                journal = Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
                journal.set_id(journal.makeid())
                journal.set_current_application(ap.id)
                journal.save(blocking=True)
                ap.set_current_journal(journal.id)
            else:
                ap.remove_current_journal()

        acc = None
        if account == "publisher":
            acc = Account(**AccountFixtureFactory.make_publisher_source())
        elif account == "admin":
            acc = Account(**AccountFixtureFactory.make_managing_editor_source())

        provenance = None
        if prov != "none":
            provenance = prov == "true"

        thenote = None
        if note == "yes":
            thenote = "abcdefg"

        ########################################
        ## execute

        svc = DOAJ.applicationService()
        if raises is not None and raises != "":
            with self.assertRaises(EXCEPTIONS[raises]):
                svc.reject_application(ap, acc, provenance, note=thenote)
        else:
            svc.reject_application(ap, acc, provenance, note=thenote)
            time.sleep(1)

            #######################################
            ## Check

            ap2 = Suggestion.pull(ap.id)
            assert ap2 is not None
            assert ap2.application_status == constants.APPLICATION_STATUS_REJECTED
            assert ap2.current_journal is None

            # check the updated and manually updated date are essentially the same (they can theoretically differ
            # by a small amount just based on when they are set)
            updated_spread = abs((ap2.last_updated_timestamp - ap2.last_manual_update_timestamp).total_seconds())
            assert updated_spread <= 1.0

            if current_journal == "yes" and journal is not None:
                j2 = Journal.pull(journal.id)
                assert j2 is not None
                assert j2.current_application is None
                assert ap2.related_journal == j2.id

            if prov == "true":
                pr = Provenance.get_latest_by_resource_id(ap.id)
                assert pr is not None

            if note == "yes":
                assert len(ap2.notes) == 1
                assert ap2.notes[0].get("note") == "abcdefg"
            elif note == "no":
                assert len(ap2.notes) == 0
