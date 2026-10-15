from doajtest.fixtures import ApplicationFixtureFactory, JournalFixtureFactory
from portality import constants
from doajtest.testdrive.factory import TestDrive
from portality import models
from portality.models import EditorGroup

class RejectWithContinuation(TestDrive):
    def setup(self) -> dict:

        random_str = self.create_random_str()

        un = "ProfessorFrostfire_" + random_str
        pw1 = self.create_random_str()
        admin = models.Account.make_account(un + "@example.com", un, un, [constants.ROLE_ADMIN])
        admin.set_password(pw1)
        admin.save(blocking=True)

        eg = EditorGroup(**{
            "name": "The Quill & Gavel Club " + random_str,
            "maned": admin.id,
            "editor": admin.id,
            "associates": [admin.id]
        })
        eg.save(blocking=True)

        jsource = JournalFixtureFactory.make_journal_source(True)
        jtitle = "Annals of Cryovolcanic Ecology " + random_str
        journal = models.Journal(**jsource)
        journal.set_id(jtitle.replace(" ", "").lower())
        jeissn = self.generate_unique_issn()
        peissn = self.generate_unique_issn()
        journal.bibjson().eissn = jeissn
        journal.bibjson().pissn = peissn
        journal.bibjson().title = jtitle
        journal.set_editor_group(eg.id)
        journal.set_editor(admin.id)
        journal.save()

        asource = ApplicationFixtureFactory.make_application_source()
        atitle = "Advances in Cold Lava Mechanics " + random_str
        application = models.Application(**asource)
        application.set_id(atitle.replace(" ", "").lower())
        application.bibjson().eissn = self.generate_unique_issn()
        application.bibjson().pissn = self.generate_unique_issn()
        application.bibjson().title = atitle
        application.bibjson().replaces = [jeissn]
        application.set_application_status(constants.APPLICATION_STATUS_IN_PROGRESS)
        application.set_editor_group(eg.id)
        application.set_editor(admin.id)
        application.remove_current_journal()
        application.remove_related_journal()
        del application.bibjson().discontinued_date
        application.save(blocking=True)

        return {
            "admin": {
                "username": admin.id,
                "password": pw1
            },
            "records": {
                "application": {"title": application.bibjson().title, "id": application.id},
                "journal": journal.bibjson().title,
            },
            "non_renderable": {
                "journal": journal.id,
                "application": application.id,
                "edgroup": eg.id
            }
        }

    def teardown(self, params):
        models.Account.remove_by_id(params["admin"]["username"])
        eg = EditorGroup.remove_by_id(params["non_renderable"]["edgroup"])
        models.Journal.remove_by_id(params["non_renderable"]["journal"])
        models.Application.remove_by_id(params["non_renderable"]["application"])

        return {"status": "success"}
