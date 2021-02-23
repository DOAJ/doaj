from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import ApplicationFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.models import Application, Account, Journal
from portality.lib.paths import rel2abs
from doajtest.mocks.bll_article import BLLArticleMockFactory
from doajtest.mocks.model_Article import ModelArticleMockFactory
from portality.dao import ESMappingMissingError
from portality import constants

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

        raises_arg = kwargs.get("raises")
        outcome_arg = kwargs.get("outcome")

        ###############################################
        ## set up

        journal_id = None
        if related_journal_present_arg == "yes":
            journal = Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
            journal.save(blocking=True)
            journal_id = journal_id
        else:
            journal_id = Journal.makeid()


        application = None
        if application_arg != "none":
            application = Application(**ApplicationFixtureFactory.make_application_source())
            if application_arg == "rejected":
                application.set_application_status(constants.APPLICATION_STATUS_REJECTED)
            elif application_arg == "pending":
                application.set_application_status(constants.APPLICATION_STATUS_PENDING)

            if related_journal_linked_arg == "no":
                application.remove_related_journal()
            else:
                application.set_related_journal(journal_id)

            application.save(blocking=True)

        if duplicate_ur_arg == "yes":
            duplicate = Application(**ApplicationFixtureFactory.make_application_source())
            duplicate.set_id(duplicate.makeid())
            duplicate.set_related_journal(journal_id)
            duplicate.save(blocking=True)

        account = None
        if account_arg != "none":
            account = Account()
            account.set_role(account_arg)

        manual_update = manual_update_arg == "True"
        raises = EXCEPTIONS.get(raises_arg)

        ###########################################################
        # Execution

        if raises is not None:
            with self.assertRaises(raises):
                self.svc.unreject_application(application, account, manual_update)

        else:
            self.svc.unreject_application(application, account, manual_update)

            # make sure all the articles are saved before running the asserts
            aids = [(a.id, a.last_updated) for a in articles]
            for aid, lu in aids:
                Article.block(aid, lu, sleep=0.05)

            assert report["success"] == success
            assert report["fail"] == fail
            assert report["update"] == update
            assert report["new"] == success - update

            if success > 0:
                all_articles = Article.all()
                if len(all_articles) != success:
                    time.sleep(0.5)
                    all_articles = Article.all()
                assert len(all_articles) == success
                for article in all_articles:
                    if add_journal_info:
                        assert article.bibjson().journal_title is not None
                    else:
                        assert article.bibjson().journal_title is None

            else:
                # there's nothing in the article index
                with self.assertRaises(ESMappingMissingError):
                    Article.all()