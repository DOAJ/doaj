from portality import constants
from doajtest.testdrive.factory import TestDrive
from portality import models

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

        return {
            "admin": {
                "username": admin.id,
                "password": pw1
            },
            "publisher": {
                "username": pub.id,
                "password": pw2
            }
        }

    def teardown(self, params):
        models.Account.remove_by_id(params["admin"]["username"])
        models.Account.remove_by_id(params["publisher"]["username"])
        return {"status": "success"}
