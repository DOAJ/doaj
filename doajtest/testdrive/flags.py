from doajtest.fixtures import ApplicationFixtureFactory, JournalFixtureFactory
from doajtest.testdrive.factory import TestDrive
from portality.lib import dates
from portality import models, constants


class Flags(TestDrive):

    def __init__(self):
        self.another_eg = None
        self.apps = []
        self.admin_password = None
        self.admin = None
        self.editor = None
        self.editor_password = None
        self.random_user = None
        self.random_user_password = None
        self.eg = None

    def setup(self) -> dict:
        self.create_accounts()
        self.build_applications()
        return {
            "accounts": {
                "admin": {
                    "username": self.admin.id,
                    "password": self.admin_password
                },
                "editor": {
                    "username": self.editor.id,
                    "password": self.editor_password
                },
                "random_user": {
                    "username": self.random_user.id,
                    "password": self.random_user_password
                }
            },
            "applications": self.apps,
            "non_renderable": {
                "editor_groups": [self.eg.name, self.another_eg.name]
            }
        }

    def create_accounts(self):
        admin_name = self.create_random_str()
        self.admin_password = self.create_random_str()
        self.admin = models.Account.make_account(admin_name + "@example.com", admin_name, "FlagsManed " + admin_name,
                                                 ["admin", "editor"])
        self.admin.set_password(self.admin_password)
        self.admin.save()

        random_name = self.create_random_str()
        self.random_user_password = self.create_random_str()
        self.random_user = models.Account.make_account(random_name + "@example.com", random_name,
                                                       "FlagsManed " + random_name,
                                                       ["admin"])
        self.random_user.set_password(self.random_user_password)
        self.random_user.save()

        editor_name = self.create_random_str()
        self.editor = models.Account.make_account(editor_name + "@example.com", editor_name, "editor " + editor_name,
                                                  ["editor"])
        self.editor_password = self.create_random_str()
        self.editor.set_password(self.editor_password)
        self.editor.save()

        gn = self.create_random_str()
        group_name = "Your Group " + gn
        self.eg = models.EditorGroup(**{
            "name": group_name
        })
        self.eg.set_maned(self.admin.id)
        self.eg.set_editor(self.editor.id)
        self.eg.save()

        gn = self.create_random_str()
        group_name = "Another Group " + gn
        self.another_eg = models.EditorGroup(**{"name": group_name})
        self.another_eg.set_maned(self.random_user.id)
        self.another_eg.set_editor(self.editor.id)
        self.another_eg.save()

    def build_applications(self):
        applications = [
            {
                "type": models.Journal,
                "title": "Journal of Quantum Homeopathy",
                "assigned_to": self.admin.id,
                "flagged_to": self.admin.id,
                "group": self.eg.name,
                "deadline": 2,
                "note": "Peer review process unclear. The journal claims to use “ancient wisdom and telepathic consensus” to select papers. Should we request further clarification, or just accept that the universe decides?"
            },
            {
                "type": models.Application,
                "title": "The Mars Agricultural Review",
                "application_type": constants.APPLICATION_TYPE_NEW_APPLICATION,
                "status": "in progress",
                "assigned_to": self.editor.id,
                "flagged_to": self.admin.id,
                "group": self.eg.name,
                "deadline": 10,
                "note": "Ethical concerns? Their conflict of interest statement is just 'Trust us.' Also, every editorial board member shares the same last name. Suspicious? Or just an enthusiastic family business?"
            },
            {
                "type": models.Application,
                "title": "Cryptid Behavioral Studies Quarterly",
                "application_type": constants.APPLICATION_TYPE_UPDATE_REQUEST,
                "assigned_to": self.editor.id,
                "flagged_to": self.admin.id,
                "group": self.eg.name,
                "note": "Formatting issues. Their abstracts are in Comic Sans, their references are in Wingdings, and their figures appear to be hand-drawn with crayon. Surprisingly, it almost adds to the charm."
            },
            {
                "type": models.Application,
                "title": "The Bermuda Triangle Journal of Lost and Found",
                "application_type": constants.APPLICATION_TYPE_NEW_APPLICATION,
                "status": "on hold",
                "assigned_to": self.editor.id,
                "flagged_to": self.editor.id,
                "group": self.eg.name,
                "note": "Reviewer qualifications unclear. The journal states that all peer reviews are conducted by 'a highly trained team of clairvoyant pigeons.' While I admire their commitment to interdisciplinary methods, I feel we should request ORCID iDs… or at least some proof that the pigeons exist."
            },
            {
                "type": models.Journal,
                "title": "Feline Aerodynamics Review",
                "assigned_to": self.admin.id,
                "group": self.eg.name
            },
            {
                "type": models.Application,
                "title": "Journal of Intergalactic Diplomacy",
                "application_type": constants.APPLICATION_TYPE_NEW_APPLICATION,
                "assigned_to": self.random_user.id,
                "flagged_to": self.admin.id,
                "group": self.another_eg.name,
                "deadline": 0,
                "note": "Editorial process... innovative? They claim to have a 100% acceptance rate because “rejecting knowledge is against our values.” Admirable, but I feel like that’s not how this works."
            },
            {
                "type": models.Application,
                "title": "Applied Alchemy & Unstable Chemistry",
                "application_type": constants.APPLICATION_TYPE_UPDATE_REQUEST,
                "assigned_to": self.random_user.id,
                "flagged_to": self.editor.id,
                "note": "Journal scope mismatch. The journal is called The International Review of Advanced Neuroscience but 90\% of its articles are about cat memes. Honestly, I’d subscribe, but should we approve it?",
                "group": self.another_eg.name
            }
        ]

        for record in applications:
            source = ApplicationFixtureFactory.make_application_source()
            ap = models.Application(**source)
            if "application_type" in record:
                source["admin"]["application_type"] = record["application_type"]
            bj = ap.bibjson()
            bj.title = record["title"]
            ap.set_id(self.create_random_str())
            ap.set_last_manual_update(dates.today())
            ap.set_created(dates.before_now(200))
            ap.remove_current_journal()
            ap.remove_related_journal()
            ap.set_editor_group(record["group"])
            ap.set_editor(record["assigned_to"])
            if "status" in record:
                ap.set_application_status(record["status"])
            if "flagged_to" in record:
                note = {"id": self.create_random_str(),
                        "note": record["note"],
                        "date": dates.now(),
                        "author_id": self.admin.id,

                        "flag": {
                            "assigned_to": record["flagged_to"],
                            "deadline": dates.days_after_now(record["deadline"]) if "deadline" in record.keys() else dates.far_in_the_future(),
                            "resolved": False
                        }}
                ap.set_notes(note)
            ap.save(blocking=True)
            self.apps.append(ap.id)

    def teardown(self, params):
        for acc in params.get("accounts").values():
            models.Account.remove_by_id(acc["username"])

        for app in params.get("applications"):
            models.Application.remove_by_id(app)

        print(params.get("non_renderable"))
        print(params.get("non_renderable").get("editor_groups"))
        for eg in params.get("non_renderable").get("editor_groups"):
            models.EditorGroup.remove_by_id(eg)

        return {"success": True}


if __name__ == "__main__":
    flags = Flags()
    params = flags.setup()
    flags.teardown(params)
