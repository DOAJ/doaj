from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from portality import models


class PublisherWithJournal(TestDrive):
    def setup(self) -> dict:
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, "Publisher " + un, [constants.ROLE_PUBLISHER, constants.ROLE_API])
        acc.set_password(pw)
        acc.generate_api_key()
        acc.save()

        source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        j = models.Journal(**source)
        j.remove_current_application()
        j.set_id(j.makeid())
        j.set_owner(acc.id)
        j.bibjson().eissn = "1111-1111"
        j.bibjson().pissn = "2222-2222"
        j.save()

        source = ApplicationFixtureFactory.make_application_source()
        a = models.Application(**source)
        a.remove_current_journal()
        a.remove_related_journal()
        a.application_type = constants.APPLICATION_TYPE_NEW_APPLICATION
        a.set_id(a.makeid())
        a.set_owner(acc.id)
        a.bibjson().eissn = "3333-3333"
        a.bibjson().pissn = "4444-4444"
        a.set_application_status(constants.APPLICATION_STATUS_IN_PROGRESS)
        a.save()

        return {
            "account": {
                "username": acc.id,
                "password": pw,
                "api_key": acc.api_key
            },
            "journals": [j.id],
            "applications": [a.id],
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["account"]["username"])
        for jid in params["journals"]:
            models.Journal.remove_by_id(jid)
        for aid in params["applications"]:
            models.Application.remove_by_id(aid)
        return {"status": "success"}