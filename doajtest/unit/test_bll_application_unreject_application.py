from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import ApplicationFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.lib.dates import STD_DATETIME_FMT
from portality.models import Application, Account, Journal
from portality.lib.paths import rel2abs
from portality import constants
from datetime import datetime, timedelta

import time

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "application_unreject_application"),
                               "unreject_application",
                               "test_id",
                               {"test_id" : []}
                               )

EXCEPTIONS = {
    "ArgumentException" : exceptions.ArgumentException,
    "AuthoriseException" : exceptions.AuthoriseException,
    "IllegalStatusException" : exceptions.IllegalStatusException,
    "DuplicateUpdateRequest" : exceptions.DuplicateUpdateRequest,
    "NoSuchObjectException" : exceptions.NoSuchObjectException
}

class TestBLLApplicationUnrejectApplication(DoajTestCase):

    def setUp(self):
        super(TestBLLApplicationUnrejectApplication, self).setUp()
        self.svc = DOAJ.applicationService()


    def tearDown(self):
        super(TestBLLApplicationUnrejectApplication, self).tearDown()

    @parameterized.expand(load_cases)
    def test_application_unreject_application(self, name, kwargs):

        application_arg = kwargs.get("application")
        related_journal_linked_arg = kwargs.get("related_journal_linked")
        related_journal_present_arg = kwargs.get("related_journal_present")
        duplicate_ur_arg = kwargs.get("duplicate_ur")
        account_arg = kwargs.get("account")
        manual_update_arg = kwargs.get("manual_update")
        disallow_statuses_arg = kwargs.get("disallow_statuses")

        raises_arg = kwargs.get("raises")
        outcome_arg = kwargs.get("outcome")

        ###############################################
        ## set up

        journal_id = None
        journal = None
        if related_journal_present_arg == "yes":
            journal = Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
            journal.remove_current_application()
            journal.remove_related_applications()
            journal.set_id(journal.makeid())
            journal_id = journal.id
        else:
            journal_id = Journal.makeid()


        application = None
        if application_arg != "none":
            application = Application(**ApplicationFixtureFactory.make_application_source())
            application.remove_current_journal()
            application.set_last_manual_update("1970-01-01T00:00:00Z")

            if application_arg == "rejected":
                application.set_application_status(constants.APPLICATION_STATUS_REJECTED)
            elif application_arg == "pending":
                application.set_application_status(constants.APPLICATION_STATUS_PENDING)
            elif application_arg == "accepted":
                application.set_application_status(constants.APPLICATION_STATUS_ACCEPTED)

            if related_journal_linked_arg == "no":
                application.remove_related_journal()
            else:
                application.set_related_journal(journal_id)

            application.save(blocking=True)

        if journal is not None:
            if application is not None:
                journal.add_related_application(application.id)
            journal.save(blocking=True)

        if duplicate_ur_arg == "yes":
            duplicate = Application(**ApplicationFixtureFactory.make_application_source())
            duplicate.set_id(duplicate.makeid())
            duplicate.set_current_journal(journal_id)
            duplicate.save(blocking=True)

        account = None
        if account_arg != "none":
            account = Account()
            account.set_role(account_arg)

        manual_update = manual_update_arg == "True"

        disallow_statuses = []
        if disallow_statuses_arg == "accepted":
            disallow_statuses.append(constants.APPLICATION_STATUS_ACCEPTED)

        raises = EXCEPTIONS.get(raises_arg)

        if application is not None:
            last_updated = application.last_updated
            if outcome_arg == "noop":
                time.sleep(1)   # this allows us to differentiate save times, so we can check that there was noop

        ###########################################################
        # Execution and Assertion

        if raises is not None:
            with self.assertRaises(raises):
                self.svc.unreject_application(application, account, manual_update, disallow_statuses)

        else:
            self.svc.unreject_application(application, account, manual_update, disallow_statuses)

            if outcome_arg == "noop":
                assert application.last_updated == last_updated
                assert application.last_manual_update == "1970-01-01T00:00:00Z"

            elif outcome_arg == "unrejected":
                journal = Journal.pull(journal_id)
                assert application.current_journal == journal_id
                assert application.related_journal is None
                assert journal.current_application == application.id
                assert len(journal.related_applications) == 0

                if manual_update:
                    # fixme: millisecond timestamps would help us here, or last_manual_update shouldn't generate its own date
                    lu = datetime.strptime(application.last_updated, STD_DATETIME_FMT)
                    lmu = datetime.strptime(application.last_manual_update, STD_DATETIME_FMT)
                    assert lmu - lu <= timedelta(seconds=1)
                else:
                    assert application.last_manual_update == "1970-01-01T00:00:00Z"