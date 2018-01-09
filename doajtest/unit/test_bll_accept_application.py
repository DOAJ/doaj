from doajtest.helpers import DoajTestCase
from parameterized import parameterized
from doajtest.fixtures import JournalFixtureFactory, AccountFixtureFactory, ApplicationFixtureFactory

import csv, time

from portality.models import Journal, Account, Suggestion, Provenance

from portality.bll import DOAJ
from portality.bll import exceptions, constants
from portality.lib import paths

RUN_SINGLE = None

def load_test_cases():
    with open(paths.rel2abs(__file__, "..", "matrices", "accept_application.csv")) as f:
        reader = csv.reader(f)
        cases = []
        first = True
        for row in reader:
            if first:
                first = False
                continue
            if RUN_SINGLE is None or (RUN_SINGLE is not None and row[0] == RUN_SINGLE):
                row[0] = "row_id_" + row[0]
                cases.append(tuple(row))
        return cases

EXCEPTIONS = {
    "ArgumentException" : exceptions.ArgumentException,
    "SaveException" : exceptions.SaveException,
    "AuthoriseException" : exceptions.AuthoriseException
}

def mock_save(*args, **kwargs):
    return None

class TestBLLAcceptApplication(DoajTestCase):

    def setUp(self):
        super(TestBLLAcceptApplication, self).setUp()
        self.old_journal_save = Journal.save

    def tearDown(self):
        super(TestBLLAcceptApplication, self).tearDown()
        Journal.save = self.old_journal_save

    @parameterized.expand(load_test_cases)
    def test_01_accept_application(self, name, application_type, account_type, manual_update, provenance, raises, result_provenance, result_manual_update):

        ###############################################
        ## set up

        # create the application
        application = None
        if application_type == "save_fail":
            application = Suggestion(**ApplicationFixtureFactory.make_application_source())
            application.save = mock_save
            Journal.save = mock_save
        elif application_type == "with_current_journal":
            application = Suggestion(**ApplicationFixtureFactory.make_application_source())
            cj = application.current_journal
            journal = Journal(**JournalFixtureFactory.make_journal_source())
            journal.set_id(cj)
            journal.save(blocking=True)
        elif application_type == "no_current_journal":
            application = Suggestion(**ApplicationFixtureFactory.make_application_source())
            application.remove_current_journal()


        acc = None
        if account_type == "not_allowed":
            acc = Account(**AccountFixtureFactory.make_publisher_source())
        elif account_type == "allowed":
            acc = Account(**AccountFixtureFactory.make_managing_editor_source())

        mu = None
        if manual_update in ["true", "false"]:
            mu = manual_update == "true"

        prov = None
        if provenance in ["true", "false"]:
            prov = provenance == "true"


        ###########################################################
        # Execution

        doaj = DOAJ()
        if raises != "":
            with self.assertRaises(EXCEPTIONS[raises]):
                doaj.accept_application(application, acc, mu, prov)
        else:
            journal = doaj.accept_application(application, acc, mu, prov)

            # we need to sleep, so the index catches up
            time.sleep(1)

            # check a few common things
            assert application.application_status == constants.APPLICATION_STATUS_ACCEPTED
            assert application.current_journal is None
            assert journal.current_application is None
            assert application.related_journal == journal.id
            related = journal.related_applications
            assert len(related) == 1
            assert related[0].get("application_id") == application.id
            assert related[0].get("date_accepted") is not None

            if result_manual_update == "yes":
                assert journal.last_manual_update is not None
                assert journal.last_manual_update != "1970-01-01T00:00:00Z"
                assert application.last_manual_update is not None
                assert application.last_manual_update != "1970-01-01T00:00:00Z"
            elif result_manual_update == "no":
                assert journal.last_manual_update is None
                assert application.last_manual_update is None

            app_prov = Provenance.get_latest_by_resource_id(application.id)
            if result_provenance == "yes":
                assert app_prov is not None
            elif result_provenance == "no":
                assert app_prov is None

