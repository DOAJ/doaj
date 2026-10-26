from doajtest.fixtures import JournalFixtureFactory
from doajtest.testdrive.factory import TestDrive
from portality.lib import dates
from portality import models, constants
from portality.core import app


class Flags(TestDrive):

    def __init__(self):
        self.id = self.create_random_str()
        self.another_eg = None
        self.journals = []
        self.admin_password = None
        self.admin = None
        self.anotheradmin = None
        self.editor = None
        self.editor_password = None
        self.publisher = None
        self.publisher_password = None
        self.random_user = None
        self.random_user_password = None
        self.eg = None

    def setup(self) -> dict:
        self.create_accounts()
        self.build_journals()
        return {
            "id": self.id,
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
            "journals": [
                {"id": j.id,
                 "title": j.bibjson().title,
                 "url": app.config.get("BASE_URL", "") + "/admin/journal/" + j.id,
                 } for j in self.journals
            ],
            "non_renderable": {
                "editor_groups": [self.eg.name, self.another_eg.name],
                "publisher": self.publisher.id
            },
            "script": {
                "script_name": "approaching_flag_deadline",
                "title": "Run background task"
            }
        }

    def _attach_id(self):
        return "__" + self.id

    def create_accounts(self):

        admin_name = "LordWiggleworth" + self._attach_id()
        self.admin_password = self.create_random_str()
        self.admin = models.Account.make_account(admin_name + "@example.com", admin_name, admin_name,
                                                 ["admin", "editor"])
        self.admin.set_password(self.admin_password)
        self.admin.save()

        anotheradmin_name = "ProfessorQuibbleton" + self._attach_id()
        self.anotheradmin_password = self.create_random_str()
        self.anotheradmin = models.Account.make_account(anotheradmin_name + "@example.com", anotheradmin_name, anotheradmin_name,
                                                 ["admin", "editor"])
        self.anotheradmin.set_password(self.anotheradmin_password)
        self.anotheradmin.save()

        random_name = "BaronFeatherfall" + self._attach_id()
        self.random_user_password = self.create_random_str()
        self.random_user = models.Account.make_account(random_name + "@example.com", random_name,
                                                       random_name,
                                                       ["admin"])
        self.random_user.set_password(self.random_user_password)
        self.random_user.save()

        editor_name = "MadamPonderleaf" + self._attach_id()
        self.editor = models.Account.make_account(editor_name + "@example.com", editor_name, editor_name,
                                                  ["editor"])
        self.editor_password = self.create_random_str()
        self.editor.set_password(self.editor_password)
        self.editor.save()

        publisher = "Publisher" + self._attach_id()
        self.publisher = models.Account.make_account(publisher + "@example.com", publisher, publisher,
                                                  ["publisher", "api"])
        self.publisher_password = self.create_random_str()
        self.publisher.set_password(self.publisher_password)
        self.publisher.save()

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

    def build_journals(self):
        journals = [
            {
                "type": models.Journal,
                "title": "Journal of Quantum Homeopathy " + self._attach_id(),
                "assigned_to": self.admin.id,
                "flagged_to": self.admin.id,
                "group": self.eg.name,
                "deadline": 2,
                "note": "Peer review process unclear. The journal claims to use “ancient wisdom and telepathic consensus” to select papers. Should we request further clarification, or just accept that the universe decides?"
            },
            {
                "type": models.Journal,
                "title": "The Mars Agricultural Review " + self._attach_id(),
                "assigned_to": self.editor.id,
                "flagged_to": self.admin.id,
                "group": self.eg.name,
                "deadline": 10,
                "note": "Ethical concerns? Their conflict of interest statement is just 'Trust us.' Also, every editorial board member shares the same last name. Suspicious? Or just an enthusiastic family business?"
            },
            {
                "type": models.Journal,
                "title": "Cryptid Behavioral Studies Quarterly " + self._attach_id(),
                "assigned_to": self.editor.id,
                "flagged_to": self.admin.id,
                "group": self.eg.name,
                "note": "Formatting issues. Their abstracts are in Comic Sans, their references are in Wingdings, and their figures appear to be hand-drawn with crayon. Surprisingly, it almost adds to the charm."
            },
            {
                "type": models.Journal,
                "title": "The Bermuda Triangle Journal of Lost and Found " + self._attach_id(),
                "assigned_to": self.editor.id,
                "flagged_to": self.editor.id,
                "group": self.eg.name,
                "note": "Reviewer qualifications unclear. The journal states that all peer reviews are conducted by 'a highly trained team of clairvoyant pigeons.' While I admire their commitment to interdisciplinary methods, I feel we should request ORCID iDs… or at least some proof that the pigeons exist."
            },
            {
                "type": models.Journal,
                "title": "Feline Aerodynamics Review " + self._attach_id(),
                "assigned_to": self.admin.id,
                "group": self.eg.name
            },
            {
                "type": models.Journal,
                "title": "Journal of Intergalactic Diplomacy " + self._attach_id(),
                "assigned_to": self.random_user.id,
                "flagged_to": self.admin.id,
                "group": self.another_eg.name,
                "deadline": 0,
                "note": "Editorial process... innovative? They claim to have a 100% acceptance rate because “rejecting knowledge is against our values.” Admirable, but I feel like that’s not how this works."
            },
            {
                "type": models.Journal,
                "title": "Applied Alchemy & Unstable Chemistry " + self._attach_id(),
                "assigned_to": self.random_user.id,
                "flagged_to": self.editor.id,
                "note": "Journal scope mismatch. The journal is called The International Review of Advanced Neuroscience but 90\% of its articles are about cat memes. Honestly, I’d subscribe, but should we approve it?",
                "group": self.another_eg.name,
                "deadline": 30,
            }
        ]

        for record in journals:
            source = JournalFixtureFactory.make_journal_source(True)
            j = models.Journal(**source)
            bj = j.bibjson()
            bj.title = record["title"]
            del bj.replaces
            del bj.is_replaced_by
            del bj.discontinued_date
            j.set_id(j.makeid())
            j.set_last_manual_update(dates.today())
            bj.publisher = self.publisher.id
            j.set_owner(self.publisher.id)
            j.set_created(dates.before_now(200))
            j.set_editor_group(record["group"])
            j.set_editor(record["assigned_to"])
            if "flagged_to" in record:
                note = {"id": self.create_random_str(),
                        "note": record["note"],
                        "date": dates.now(),
                        "author_id": self.admin.id,

                        "flag": {
                            "assigned_to": record["flagged_to"],
                            "deadline": dates.days_after_now(record["deadline"]) if "deadline" in record.keys() else dates.far_in_the_future(),
                        }}
                j.set_notes(note)
            j.save()
            self.journals.append(j)

        return self.journals

    def teardown(self, params):
        for acc in params.get("accounts").values():
            models.Account.remove_by_id(acc["username"])

        for j in params.get("journals"):
            models.Journal.remove_by_id(j["id"])

        for eg in params.get("non_renderable").get("editor_groups"):
            models.EditorGroup.remove_by_id(eg)

        models.Account.remove_by_id(params.get("non_renderable").get("publisher"))

        return {"success": True}


if __name__ == "__main__":
    flags = Flags()
    params = flags.setup()
    flags.teardown(params)
