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
        # same ISSNs, in the same fields, as the article XML upload test files in doajtest/xml_upload_test_package
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
            "article_upload_instructions": [
                "Log in with the username and password above to upload articles as this publisher",
                "The journal is in DOAJ with Print ISSN 1111-1111 and E-ISSN 2222-2222, matching the article XML upload test files",
                "An article's ISSNs must match exactly one journal in DOAJ, owned by the uploader, with the Print and E-ISSN in the same fields",
                "Only one journal may have these ISSNs. If you ran this testdrive before, use the teardown link on that earlier page first, or uploads will fail with the ISSNs reported as shared or not owned",
                "For the 'unmatched ISSN' tests, ISSN 5555-5555 must not be on any journal",
                "Uploads stay 'pending' unless the events queue worker is running: huey_consumer.py portality.tasks.consumer_events_queue.events_queue",
            ],
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["account"]["username"])
        for jid in params["journals"]:
            models.Journal.remove_by_id(jid)
        for aid in params["applications"]:
            models.Application.remove_by_id(aid)
        return {"status": "success"}