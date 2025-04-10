from doajtest.fixtures import ApplicationFixtureFactory
from portality import constants
from doajtest.testdrive.factory import TestDrive
from portality import models
from portality.lib import dates
from portality.core import app
from flask import url_for

class AutocheckApplicationSubmission(TestDrive):
    """
    setup for the testbook test autocheck/application_submission_workflow
    """

    def setup(self) -> dict:
        # admin
        un = self.create_random_str()
        pw1 = self.create_random_str()
        admin = models.Account.make_account(un + "@example.com", un, "Admin " + un, [constants.ROLE_ADMIN])
        admin.set_password(pw1)
        admin.save()

        # publisher
        un = self.create_random_str()
        pw2 = self.create_random_str()
        pub = models.Account.make_account(un + "@example.com", un, "Publisher " + un, [constants.ROLE_PUBLISHER])
        pub.set_password(pw2)
        pub.save()

        # ensure that the issns that we are going to use in the test are removed from the database
        js = models.Journal.find_by_issn("1848-3380")
        if js is not None:
            for j in js:
                j.delete()

        js = models.Journal.find_by_issn("0005-1144")
        if js is not None:
            for j in js:
                j.delete()

        # create a draft application for submission
        source = ApplicationFixtureFactory.make_application_source()
        draft_application = models.DraftApplication(**source)
        draft_application.set_id(draft_application.makeid())
        draft_application.set_application_status("draft")
        draft_application.set_owner(pub.id)
        draft_application.application_type = constants.APPLICATION_TYPE_NEW_APPLICATION
        draft_application.remove_related_journal()
        draft_application.date_applied = dates.now_str()
        bj = draft_application.bibjson()
        bj.pissn = "1848-3380"
        bj.eissn = "0005-1144"
        bj.set_preservation(["CLOCKSS", "LOCKSS"], "https://example.com/preservation")
        draft_application.save()

        return {
            "admin": {
                "username": admin.id,
                "password": pw1
            },
            "publisher": {
                "username": pub.id,
                "password": pw2
            },
            "draft_application": {
                "id": draft_application.id,
                "url": app.config.get("BASE_URL") + url_for("apply.public_application", draft_id=draft_application.id)
            }
        }

    def teardown(self, params):
        models.Account.remove_by_id(params["admin"]["username"])
        models.Account.remove_by_id(params["publisher"]["username"])
        return {"status": "success"}
