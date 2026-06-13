from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from portality import models


class FormRearrangement(TestDrive):
    def setup(self) -> dict:
        publisher_un = "LordSniffleton"
        publisher_pw = self.create_random_str()
        publisher_acc = models.Account.make_account(
            publisher_un + "@example.com",
            publisher_un,
            "Publisher " + publisher_un,
            [constants.ROLE_PUBLISHER]
        )
        publisher_acc.set_password(publisher_pw)
        publisher_acc.save()

        admin_un = "DukeDingleberry"
        admin_pw = self.create_random_str()
        admin_acc = models.Account.make_account(
            admin_un + "@example.com",
            admin_un,
            "Admin " + admin_un,
            [constants.ROLE_ADMIN]
        )
        admin_acc.set_password(admin_pw)
        admin_acc.save()

        editor_un = "CountessCrumblewhisk"
        editor_pw = self.create_random_str()
        editor_acc = models.Account.make_account(
            editor_un + "@example.com",
            editor_un,
            "Editor " + editor_un,
            [constants.ROLE_EDITOR]
        )
        editor_acc.set_password(editor_pw)
        editor_acc.save()

        # Journal setup
        source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        j = models.Journal(**source)
        j.remove_current_application()
        j.set_id(j.makeid())
        j.set_owner(publisher_acc.id)
        j.bibjson().eissn = "1987-0007"
        j.bibjson().pissn = "3141-5926"
        j.bibjson().title = "Annals of Aquatic Diplomacy"
        j.bibjson().journal_url = "https://please-dont-splash.org"
        del j.bibjson().discontinued_date
        j.save(blocking=True)

        # New application setup
        source = ApplicationFixtureFactory.make_application_source()
        a = models.Application(**source)
        a.remove_current_journal()
        a.remove_related_journal()
        a.application_type = constants.APPLICATION_TYPE_NEW_APPLICATION
        a.set_id(a.makeid())
        a.set_editor(editor_acc.id)
        a.set_owner(publisher_acc.id)
        a.bibjson().eissn = "2718-2818"
        a.bibjson().title = "Journal of Speculative Mycology"
        a.bibjson().journal_url = "https://fungi-that-might-exist.com"
        a.set_application_status(constants.APPLICATION_STATUS_IN_PROGRESS)
        a.save(blocking=True)

        # Update request setup
        source = ApplicationFixtureFactory.make_update_request_source()
        ur = models.Application(**source)
        ur.set_id(ur.makeid())
        ur.set_editor(editor_acc.id)
        ur.set_owner(publisher_acc.id)
        ur.bibjson().pissn = "0042-2718"
        ur.bibjson().title = "Proceedings of Recursive Archaeology"
        ur.bibjson().journal_url = "https://digging-up-the-future.net"
        ur.save(blocking=True)

        return {
            "accounts": {
                "admin": {"username": admin_acc.id, "password": admin_pw},
                "editor": {"username": editor_acc.id, "password": editor_pw},
                "publisher": {"username": publisher_acc.id, "password": publisher_pw},
            },
            "journals": {j.bibjson().title: j.id},
            "applications": {a.bibjson().title: a.id},
            "update_requests": {ur.bibjson().title: ur.id}
        }

    def teardown(self, params) -> dict:
        for accid in ["admin", "editor", "publisher"]:
            models.Account.remove_by_id(params["accounts"][accid]["username"])

        for title, id in params["journals"].items():
            models.Journal.remove_by_id(id)

        for title, id in params["applications"].items():
            models.Application.remove_by_id(id)

        for title, id in params["update_requests"].items():
            models.Application.remove_by_id(id)

        return {"status": "success"}
