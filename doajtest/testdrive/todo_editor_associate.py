from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.testdrive.todo_associate import build_applications as build_associate_applications
from doajtest.testdrive.todo_editor import build_applications as build_editor_applications
from portality import models


class TodoEditorAssociate(TestDrive):

    def setup(self) -> dict:
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, "TodoEditorAssociate " + un, ["editor", constants.ROLE_ASSOCIATE_EDITOR])
        acc.set_password(pw)
        acc.save()

        gn = "TodoEditorAssociate Group " + un
        eg = models.EditorGroup(**{
            "name": gn
        })
        eg.set_editor(acc.id)
        eg.save()

        aapps = build_associate_applications(un)
        eapps = build_editor_applications(un, eg)

        return {
            "account": {
                "username": acc.id,
                "password": pw
            },
            "editor_group": {
                "id": eg.id,
                "name": eg.name
            },
            "applications": {
                "associate": aapps,
                "editor": eapps
            }
        }