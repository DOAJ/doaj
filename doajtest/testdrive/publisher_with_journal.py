from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.v2.journals import JournalFixtureFactory
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
        j.set_owner(acc.id)
        j.bibjson().eissn = "1111-1111"
        j.bibjson().pissn = "2222-2222"
        j.save()

        return {
            "account": {
                "username": acc.id,
                "password": pw,
                "api_key": acc.api_key
            },
            "journals": [j.id]
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["account"]["username"])
        for jid in params["journals"]:
            models.Journal.remove_by_id(jid)
        return {"status": "success"}