from doajtest.helpers import DoajTestCase
from parameterized import parameterized
from doajtest.fixtures import JournalFixtureFactory, AccountFixtureFactory, ApplicationFixtureFactory

import csv, uuid, time

from portality.models import Journal, Account, Suggestion

from portality.bll import DOAJ
from portality.bll import exceptions
from portality.lib import paths
from portality import lock

RUN_SINGLE = None

def load_test_cases():
    with open(paths.rel2abs(__file__, "..", "matrices", "update_request_for_journal.csv")) as f:
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
    "Locked" : lock.Locked,
    "AuthoriseException" : exceptions.AuthoriseException
}

class TestBLLUpdateRequest(DoajTestCase):

    @parameterized.expand(load_test_cases)
    def test_01_update_request(self, name, journal_id, journal_lock,
                               account, account_role, account_is_owner,
                               applications, application_lock, application_status,
                               raises,
                               return_app, return_jlock, return_alock,
                               db_jlock, db_alock, db_app):

        ###############################################
        ## set up

        # create the journal
        journal = None
        jid = None
        if journal_id == "valid":
            journal = Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
            jid = journal.id
        elif journal_id == "missing":
            jid = uuid.uuid4().hex

        acc = None
        if account == "yes":
            acc = Account(**AccountFixtureFactory.make_publisher_source())
            if account_role == "none":
                acc.remove_role("publisher")
            elif account_role == "admin":
                acc.remove_role("publisher")
                acc.add_role("admin")
            acc.set_id(acc.makeid())
            if account_is_owner == "yes":
                acc.set_id(journal.owner)

        if journal_lock == "yes":
            lock.lock("journal", jid, "someoneelse", blocking=True)

        latest_app = None
        app_count = int(applications)
        for i in range(app_count):
            app = Suggestion(**ApplicationFixtureFactory.make_application_source())
            app.set_id(app.makeid())
            app.set_created("197" + str(i) + "-01-01T00:00:00Z")
            app.set_current_journal(jid)
            app.save()
            latest_app = app

        if app_count == 0:
            # save at least one record to initialise the index mapping, otherwise tests fail
            app = Suggestion(**ApplicationFixtureFactory.make_application_source())
            app.set_id(app.makeid())
            app.save()

        if application_lock == "yes":
            lock.lock("suggestion", latest_app.id, "someoneelse", blocking=True)

        if application_status != "n/a":
            latest_app.set_application_status(application_status)
            latest_app.save()

        # finally save the journal record, ensuring we get a blocking save, so everything
        # above here should be synchronised with the repo
        if journal is not None:
            journal.save(blocking=True)

        ###########################################################
        # Execution

        doaj = DOAJ()
        if raises != "":
            with self.assertRaises(EXCEPTIONS[raises]):
                doaj.update_request_for_journal(jid, acc)
        else:
            application, jlock, alock = doaj.update_request_for_journal(jid, acc)

            # we need to sleep, so the index catches up
            time.sleep(1)

            if return_app == "none":
                assert application is None
            elif return_app == "yes":
                assert application is not None

            if return_jlock == "none":
                assert jlock is None
            elif return_jlock == "yes":
                assert jlock is not None

            if return_alock == "none":
                assert alock is None
            elif return_alock == "yes":
                assert alock is not None

            if db_jlock == "no" and acc is not None:
                assert not lock.has_lock("journal", jid, acc.id)
            elif db_jlock == "yes" and acc is not None:
                assert lock.has_lock("journal", jid, acc.id)

            if db_alock == "no" and application.id is not None and acc is not None:
                assert not lock.has_lock("suggestion", application.id, acc.id)
            elif db_alock == "yes" and application.id is not None and acc is not None:
                assert lock.has_lock("suggestion", application.id, acc.id)

            if db_app == "no" and application.id is not None:
                indb = Suggestion.q2obj(q="id.exact:" + application.id)
                assert indb is None
            elif db_app == "yes" and application.id is not None:
                indb = Suggestion.q2obj(q="id.exact:" + application.id)
                assert indb is not None