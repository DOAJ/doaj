from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from portality import models


class NewEditorialFormLayout(TestDrive):
    def setup(self) -> dict:
        publisher_un = "SirSneezesALot"
        publisher_pw = self.create_random_str()
        publisher_acc = models.Account.make_account(publisher_un + "@example.com", publisher_un, "Publisher " + publisher_un, [constants.ROLE_PUBLISHER])
        publisher_acc.set_password(publisher_pw)
        publisher_acc.save()

        admin_un = "BaronVonBurp"
        admin_pw = self.create_random_str()
        admin_acc = models.Account.make_account(admin_un + "@example.com", admin_un,
                                                    "Admin " + admin_un,
                                                    [constants.ROLE_ADMIN])
        admin_acc.set_password(admin_pw)
        admin_acc.save()

        editor_un = "LadyGigglesworth"
        editor_pw = self.create_random_str()
        editor_acc = models.Account.make_account(editor_un + "@example.com", editor_un,
                                                "Editor " + editor_un,
                                                [constants.ROLE_EDITOR])
        editor_acc.set_password(editor_pw)
        editor_acc.save()

        source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        j = models.Journal(**source)
        j.remove_current_application()
        j.set_id(j.makeid())
        j.title = "Annals of Interspecies Etiquette"
        j.set_owner(publisher_acc.id)
        j.bibjson().eissn = "1987-0007"
        j.bibjson().pissn = "3141-5926"
        j.save()

        source = ApplicationFixtureFactory.make_application_source()
        a = models.Application(**source)
        a.remove_current_journal()
        a.remove_related_journal()
        a.application_type = constants.APPLICATION_TYPE_NEW_APPLICATION
        a.set_id(a.makeid())
        a.title = "Journal of Hypothetical Entomology"
        a.set_editor(editor_acc.id)
        a.set_owner(publisher_acc.id)
        a.bibjson().eissn = "2718-2818"
        a.set_application_status(constants.APPLICATION_STATUS_IN_PROGRESS)
        a.save()

        source = ApplicationFixtureFactory.make_application_source()
        ur = models.Application(**source)
        ur.remove_current_journal()
        ur.remove_related_journal()
        ur.application_type = constants.APPLICATION_TYPE_NEW_APPLICATION
        ur.set_id(a.makeid())
        ur.title = "Annals of Temporal Mechanics"
        ur.set_editor(editor_acc.id)
        ur.set_owner(publisher_acc.id)
        ur.bibjson().pissn = "0042-2718"
        ur.set_application_status(constants.APPLICATION_STATUS_IN_PROGRESS)
        ur.save()


        return {
            "accounts": {
                "admin": {"username": admin_acc.id,
                 "password": admin_pw},
                "editor": {"username": editor_acc.id,
                 "password": editor_pw},
                "publisher": {"username": publisher_acc.id,
                 "password": publisher_pw},
            },
            "journals": {j.title: j.id},
            "applications": {a.title: a.id, ur.title :ur.id}
        }

    def teardown(self, params) -> dict:
        for accid in ["admin", "editor", "publisher"]:
            models.Account.remove_by_id(params["accounts"][accid]["username"])
        for title, id in params["journals"].items():
            models.Journal.remove_by_id(id)
        for title, id in params["applications"].items():
            models.Application.remove_by_id(id)
        return {"status": "success"}