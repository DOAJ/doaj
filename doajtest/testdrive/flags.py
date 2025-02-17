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
        self.assed1_password = None
        self.assed1 = None
        self.assed2 = None
        self.assed2_password = None
        self.editor = None
        self.editor_password = None
        self.random_user = None
        self.random_user_password = None
        self.eg = None

    def setup(self) -> dict:
        self.create_accounts()
        self.create_applications()
        return {
            "accounts": {
                "admin": {
                    "username": self.admin.id,
                    "password": self.admin_password
                },
                "editor_1": {
                    "username": self.editor.id,
                    "password": self.editor_password
                },
                "associate_editor_1": {
                    "username": self.assed1.id,
                    "password": self.assed1_password
                },
                "associate_editor_2": {
                    "username": self.assed2.id,
                    "password": self.assed2_password
                },
                "random_user": {
                    "username": self.random_user.id,
                    "password": self.random_user_password
                }
            },
            "applications": self.apps,
            "editor group": [self.editor.name],
            "non_renderable": {
                "eg": self.eg.id,
                "applications": self.apps
            }
        }

    def create_accounts(self):
        admin_name = self.create_random_str()
        self.admin_password = self.create_random_str()
        self.admin = models.Account.make_account(admin_name + "@example.com", admin_name, "FlagsManed " + admin_name,
                                                 ["admin"])
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

        assed1_name = self.create_random_str()
        self.assed1_password = self.create_random_str()
        self.assed1 = models.Account.make_account(assed1_name + "@example.com", assed1_name,
                                                  "Associate Editor 1 " + assed1_name, ["associate_editor"])
        self.assed1.set_password(self.assed1_password)
        self.assed1.save()

        assed2_name = self.create_random_str()
        self.assed2_password = self.create_random_str()
        self.assed2 = models.Account.make_account(assed2_name + "@example.com", assed2_name,
                                                  "Associate Editor 1 " + assed2_name, ["associate_editor"])
        self.assed2.set_password(self.assed1_password)
        self.assed2.save()

        gn = self.create_random_str()
        group_name = "Maned Group " + gn
        self.eg = models.EditorGroup(**{
            "name": group_name
        })
        self.eg.set_maned(self.admin.id)
        self.eg.set_editor(self.editor.id)
        self.eg.set_associates([self.assed1.id, self.assed2.id])
        self.eg.save()

    def build_application(self, aid, title, lmu_diff, cd_diff, status, notes=None,
                          additional_fn=None):

        source = ApplicationFixtureFactory.make_application_source()
        ap = models.Application(**source)
        source["admin"]["application_type"] = constants.APPLICATION_TYPE_NEW_APPLICATION
        source["admin"]["current_journal"] = None
        bj = ap.bibjson()
        bj.title = title
        ap.set_id(aid)
        ap.set_last_manual_update(dates.before_now(lmu_diff))
        ap.set_created(dates.before_now(cd_diff))
        ap.set_application_status(status)
        if notes is not None:
            ap.set_notes(notes)
        if additional_fn is not None:
            additional_fn(ap)
        ap.save()
        return ap

    def create_applications(self):
        accounts = {"Admin": self.admin,
                    "Editor": self.editor,
                    "Assed1": self.assed1,
                    "Assed2": self.assed2}
        deadlines_in_days = [-2, 2, 9, 12, None]
        deadline = lambda d: dates.days_after_now(d) if days else ""
        one_app_flagged_to_editor = False
        one_app_flagged_to_assed = False


        for key, val in accounts.items():
            for days in deadlines_in_days:
                note = {"id": self.create_random_str(),
                        "note": self.create_random_str(),
                        "date": dates.now(),
                        "author_id": self.admin.id,

                        "flag": {
                            "assigned_to": val.id,
                            "deadline": deadline(days) if days is not None else dates.far_in_the_future(),
                            "resolved": False
                        }}
                app = self.build_application(aid=self.create_random_str(),
                                             title=f'Application flagged for {key}, with deadline in {days} days',
                                             lmu_diff=0, cd_diff=31, status=constants.APPLICATION_STATUS_IN_PROGRESS,
                                             notes=note)

                if (not one_app_flagged_to_assed) and key == "Assed1":
                    app.set_editor_group(self.eg.name)
                    app.set_editor(self.editor.id)
                    app.save()
                    print("one_app_flagged_to_assed: ", app.id, self.editor.id)
                    one_app_flagged_to_assed = True

                if (not one_app_flagged_to_editor) and key == "Editor":
                    app.set_editor_group(self.eg.name)
                    app.set_editor(self.editor.id)
                    app.save()
                    print("one_app_flagged_to_editor: ", app.id, self.editor.id)
                    one_app_flagged_to_editor = True

                self.apps.append(app.id)

    def teardown(self, params):
        for acc in params.get("accounts").values():
            models.Account.remove_by_id(acc["username"])

        non_renderable = params.get("non_renderable", {})
        models.EditorGroup.remove_by_id(non_renderable["eg"])
        for app in non_renderable["applications"]:
            models.Application.remove_by_id(app)

        return {"success": True}


if __name__ == "__main__":
    flags = Flags()
    params = flags.setup()
    flags.teardown(params)
