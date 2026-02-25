from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from portality import models
from portality.core import app

class UrNudge(TestDrive):
    def setup(self) -> dict:
        random_id = self.create_random_str()


        un = "CelestialFrontierPress_" + random_id
        pw = self.create_random_str()
        acc = models.Account.make_account("cfp@example.com", un, un, [constants.ROLE_PUBLISHER, constants.ROLE_API])
        acc.set_password(pw)
        acc.generate_api_key()
        acc.save()

        un1 = "DeepOrbitAcademicPress_" + random_id
        pw1 = self.create_random_str()
        acc1 = models.Account.make_account("doap@example.com", un1, un1, [constants.ROLE_PUBLISHER, constants.ROLE_API])
        acc1.set_password(pw1)
        acc1.save()

        source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        j = models.Journal(**source)
        j.remove_current_application()
        j.set_id(j.makeid())
        j.set_owner(acc.id)
        j.bibjson().title = "Journal of Exoplanetary Biosignatures " + random_id
        del j.bibjson().discontinued_date
        del j.bibjson().is_replaced_by
        del j.bibjson().replaces
        j.bibjson().eissn = self.generate_unique_issn()
        j.bibjson().pissn = self.generate_unique_issn()
        j.save()

        source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        j1 = models.Journal(**source)
        j1.remove_current_application()
        j1.bibjson().title = "Annals of Stellar Habitat Studies " + random_id
        del j1.bibjson().discontinued_date
        del j1.bibjson().is_replaced_by
        del j1.bibjson().replaces
        j1.set_id(j.makeid())
        j1.set_owner(acc1.id)
        j1.bibjson().eissn = self.generate_unique_issn()
        j1.bibjson().pissn = self.generate_unique_issn()
        j1.save()

        return {
            "accounts": {
                "username": acc.id,
                "password": pw
            },
            "journals": {j.bibjson().title: app.config.get("BASE_URL") + "/toc/" + j.bibjson().eissn,
                         j1.bibjson().title: app.config.get("BASE_URL") + "/toc/" + j1.bibjson().eissn},
            "non_renderable": {
                "accounts": [acc.id, acc1.id],
                "journals": [j.id, j1.id],
            }
        }

    def teardown(self, params) -> dict:
        ids = params["non_renderable"]
        for aid in ids["accounts"]:
            models.Account.remove_by_id(aid)
        for jid in ids["journals"]:
            models.Journal.remove_by_id(jid)
        return {"status": "success"}