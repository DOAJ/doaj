from doajtest.fixtures import JournalFixtureFactory
from doajtest.testdrive.factory import TestDrive
from portality.lib import dates
from portality import models, constants


class Flags(TestDrive):

    def __init__(self):
        self.another_eg = None
        self.journals = []
        self.admin_password = None
        self.admin = None
        self.anotheradmin = None
        self.editor = None
        self.editor_password = None
        self.random_user = None
        self.random_user_password = None
        self.eg = None

    def setup(self) -> dict:
        random_str = self.create_random_str()
        self.create_accounts(random_str)
        self.build_journals(random_str)
        return {
            "accounts": {
                "admin": {
                    "username": self.admin.id,
                    "password": self.admin_password
                },
                "another admin": {
                    "username": self.anotheradmin.id,
                    "password": self.anotheradmin_password
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
            "journals": self.journals,
            "non_renderable": {
                "editor_groups": [self.eg.name, self.another_eg.name]
            },
            "script": {
                "script_name": "approaching_flag_deadline",
                "title": "Run background task"
            }
        }

    def create_accounts(self, random_str):

        admin_name = "LordWiggleworth_" + random_str
        self.admin_password = self.create_random_str()
        self.admin = models.Account.make_account(admin_name + "@example.com", admin_name, "FlagsManed " + admin_name,
                                                 ["admin", "editor"])
        self.admin.set_password(self.admin_password)
        self.admin.save()

        anotheradmin_name = "ProfessorQuibbleton_" + random_str
        self.anotheradmin_password = self.create_random_str()
        self.anotheradmin = models.Account.make_account(anotheradmin_name + "@example.com", anotheradmin_name, "Admin " + anotheradmin_name,
                                                 ["admin", "editor"])
        self.anotheradmin.set_password(self.anotheradmin_password)
        self.anotheradmin.save()

        random_name = "BaronFeatherfall_" + random_str
        self.random_user_password = self.create_random_str()
        self.random_user = models.Account.make_account(random_name + "@example.com", random_name,
                                                       "Admin " + random_name,
                                                       ["admin"])
        self.random_user.set_password(self.random_user_password)
        self.random_user.save()

        editor_name = "MadamPonderleaf_" + random_str
        self.editor = models.Account.make_account(editor_name + "@example.com", editor_name, "Editor " + editor_name,
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

    def build_journals(self, random_str):
        journals = [
            {
                "type": models.Journal,
                "title": "Journal of Quantum Homeopathy " + random_str,
                "assigned_to": self.admin.id,
                "flagged_to": self.admin.id,
                "group": self.eg.name,
                "deadline": 2,
                "note": "Peer review process unclear. The journal claims to use “ancient wisdom and telepathic consensus” to select papers. Should we request further clarification, or just accept that the universe decides?"
            },
            {
                "type": models.Journal,
                "title": "The Mars Agricultural Review " + random_str,
                "assigned_to": self.editor.id,
                "flagged_to": self.admin.id,
                "group": self.eg.name,
                "deadline": 10,
                "note": "Ethical concerns? Their conflict of interest statement is just 'Trust us.' Also, every editorial board member shares the same last name. Suspicious? Or just an enthusiastic family business?"
            },
            {
                "type": models.Journal,
                "title": "Cryptid Behavioral Studies Quarterly " + random_str,
                "assigned_to": self.editor.id,
                "flagged_to": self.admin.id,
                "group": self.eg.name,
                "note": "Formatting issues. Their abstracts are in Comic Sans, their references are in Wingdings, and their figures appear to be hand-drawn with crayon. Surprisingly, it almost adds to the charm."
            },
            {
                "type": models.Journal,
                "title": "The Bermuda Triangle Journal of Lost and Found " + random_str,
                "assigned_to": self.editor.id,
                "flagged_to": self.editor.id,
                "group": self.eg.name,
                "note": "Reviewer qualifications unclear. The journal states that all peer reviews are conducted by 'a highly trained team of clairvoyant pigeons.' While I admire their commitment to interdisciplinary methods, I feel we should request ORCID iDs… or at least some proof that the pigeons exist."
            },
            {
                "type": models.Journal,
                "title": "Feline Aerodynamics Review " + random_str,
                "assigned_to": self.admin.id,
                "group": self.eg.name
            },
            {
                "type": models.Journal,
                "title": "Journal of Intergalactic Diplomacy " + random_str,
                "assigned_to": self.random_user.id,
                "flagged_to": self.admin.id,
                "group": self.another_eg.name,
                "deadline": 0,
                "note": "Editorial process... innovative? They claim to have a 100% acceptance rate because “rejecting knowledge is against our values.” Admirable, but I feel like that’s not how this works."
            },
            {
                "type": models.Journal,
                "title": "Applied Alchemy & Unstable Chemistry " + random_str,
                "assigned_to": self.random_user.id,
                "flagged_to": self.editor.id,
                "note": "Journal scope mismatch. The journal is called The International Review of Advanced Neuroscience but 90\% of its articles are about cat memes. Honestly, I’d subscribe, but should we approve it?",
                "group": self.another_eg.name
            }
        ]

        for record in journals:
            source = JournalFixtureFactory.make_journal_source(True)
            ap = models.Journal(**source)
            bj = ap.bibjson()
            bj.title = record["title"]
            ap.set_id(ap.makeid())
            ap.set_last_manual_update(dates.today())
            ap.set_created(dates.before_now(200))
            ap.set_editor_group(record["group"])
            ap.set_editor(record["assigned_to"])
            if "flagged_to" in record:
                note = {"id": self.create_random_str(),
                        "note": record["note"],
                        "date": dates.now(),
                        "author_id": self.admin.id,

                        "flag": {
                            "assigned_to": record["flagged_to"],
                            "deadline": dates.days_after_now(record["deadline"]) if "deadline" in record.keys() else dates.far_in_the_future(),
                        }}
                ap.set_notes(note)
            ap.save()
            self.journals.append(ap.id)

        return self.journals

    def teardown(self, params):
        for acc in params.get("accounts").values():
            models.Account.remove_by_id(acc["username"])

        for app in params.get("journals"):
            models.Journal.remove_by_id(app)

        print(params.get("non_renderable"))
        print(params.get("non_renderable").get("editor_groups"))
        for eg in params.get("non_renderable").get("editor_groups"):
            models.EditorGroup.remove_by_id(eg)

        return {"success": True}


if __name__ == "__main__":
    flags = Flags()
    params = flags.setup()
    flags.teardown(params)
