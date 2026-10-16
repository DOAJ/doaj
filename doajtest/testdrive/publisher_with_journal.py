import elasticsearch
from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from portality import models


class PublisherWithJournal(TestDrive):
    def setup(self) -> dict:
        # the XML upload test files use these fixed ISSNs; a second journal holding them makes uploads fail as "shared"
        clashes = models.Journal.find_by_issn(["1111-1111", "2222-2222"])
        if clashes:
            return {"error": "Journal(s) " + ", ".join(j.id for j in clashes) + " already use ISSN 1111-1111 or "
                             "2222-2222; remove them or change their ISSNs before running this testdrive"}

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
        j.bibjson().pissn = "1111-1111"
        j.bibjson().eissn = "2222-2222"
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
        if "error" in params:
            return {"status": "success"}
        # remove articles the tester uploaded into the journal; must run before the journal is removed
        try:
            models.Article.delete_selected(owner=params["account"]["username"], snapshot=False, tombstone=False)
        except elasticsearch.ConflictError:
            # the page's beforeunload beacon runs a second teardown alongside the link click; it deleted them first
            pass
        models.Account.remove_by_id(params["account"]["username"])
        for jid in params["journals"]:
            models.Journal.remove_by_id(jid)
        for aid in params["applications"]:
            models.Application.remove_by_id(aid)
        return {"status": "success"}