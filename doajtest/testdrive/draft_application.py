from doajtest.fixtures import ApplicationFixtureFactory
from doajtest.testdrive.factory import TestDrive
from portality import models, constants
from portality.bll import DOAJ
from portality.lib import dates


class DraftApplication(TestDrive):

    def setup(self) -> dict:
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, "Publisher " + un,[constants.ROLE_PUBLISHER, constants.ROLE_API])
        acc.set_password(pw)
        acc.generate_api_key()
        acc.save()


        drafts = []
        for i in range(5):
            source = ApplicationFixtureFactory.make_application_source()
            app = models.DraftApplication(**source)
            app.set_id(app.makeid())
            app.bibjson().title = "Draft " + str(i)
            app.set_created(dates.before_now(86400*i))
            app.set_owner(acc.id)
            app.save()
            drafts.append(app)

        report = []
        for draft in drafts:
            report.append({
                "draft" : draft.id
            })

        return {
            "account": {
                "username": acc.id,
                "password": pw,
                "api_key": acc.api_key
            },
            "drafts": report
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["account"]["username"])
        for draft in params["drafts"]:
            models.DraftApplication.remove_by_id(draft)
            models.Application.remove_by_id(draft)  # In case the point of the test was to accept the draft and create an application

        return {"status": "success"}