from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from doajtest.testdrive.todo_associate import build_applications as build_associate_applications
from doajtest.testdrive.todo_editor import build_applications as build_editor_applications
from portality import models
from portality.lib import dates
from datetime import datetime


class TodoManedEditorAssociate(TestDrive):

    def setup(self) -> dict:
        un = self.create_random_str()
        pw = self.create_random_str()
        admin = models.Account.make_account(un + "@example.com", un, "TodoManedEditorAssociate " + un,
                                            ["admin", "editor", constants.ROLE_ASSOCIATE_EDITOR])
        admin.set_password(pw)
        admin.save()

        oun = self.create_random_str()
        owner = models.Account.make_account(oun + "@example.com", oun, "Owner " + un, ["publisher"])
        owner.save()

        eun = self.create_random_str()
        assed = models.Account.make_account(eun + "@example.com", eun, "Associate Editor " + un, ["associate_editor"])
        assed.save()

        gn1 = "Maned Group " + un
        eg1 = models.EditorGroup(**{
            "name": gn1
        })
        eg1.set_maned(admin.id)
        eg1.add_associate(assed.id)
        eg1.save()

        gn2 = "Editor Group " + un
        eg2 = models.EditorGroup(**{
            "name": gn2
        })
        eg2.set_editor(admin.id)
        eg2.save()

        # the eponymous group
        eg3 = models.EditorGroup(**{
            "name": admin.id
        })
        eg3.set_maned(admin.id)
        eg3.set_editor(admin.id)
        eg3.add_associate(admin.id)
        eg3.save()

        aapps = build_associate_applications(un)
        eapps = build_editor_applications(un, eg2)
        mapps = build_maned_applications(un, eg1, owner.id, eg3)

        return {
            "account": {
                "username": admin.id,
                "password": pw
            },
            "users": [
                owner.id,
                assed.id
            ],
            "editor_group": {
                "id": eg2.id,
                "name": eg2.name
            },
            "maned_group": {
                "id": eg1.id,
                "name": eg1.name
            },
            "applications": {
                "associate": aapps,
                "editor": eapps,
                "maned": mapps
            }
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["account"]["username"])
        for user in params["users"]:
            models.Account.remove_by_id(user)
        models.EditorGroup.remove_by_id(params["editor_group"]["id"])
        models.EditorGroup.remove_by_id(params["maned_group"]["id"])
        for nature, details in params["applications"]["associate"].items():
            for detail in details:
                models.Application.remove_by_id(detail["id"])
        for nature, details in params["applications"]["editor"].items():
            for detail in details:
                models.Application.remove_by_id(detail["id"])
        for nature, details in params["applications"]["maned"].items():
            for detail in details:
                models.Application.remove_by_id(detail["id"])
        return {"status": "success"}


def build_maned_applications(un: str,
                             eg: models.EditorGroup, owner,
                             eponymous_group: models.EditorGroup):
    w = 7 * 24 * 60 * 60

    apps = {}

    app = build_application(un + " Maned Stalled Application", 8 * w, 9 * w, constants.APPLICATION_STATUS_IN_PROGRESS,
                            editor_group=eg.id, owner=owner)
    app.save()
    apps["stalled"] = [{
        "id": app.id,
        "title": un + " Maned Stalled Application"
    }]

    app = build_application(un + " Maned Old Application", 10 * w, 10 * w, constants.APPLICATION_STATUS_IN_PROGRESS,
                            editor_group=eg.id, owner=owner)
    app.save()
    apps["old"] = [{
        "id": app.id,
        "title": un + " Maned Old Application"
    }]

    app = build_application(un + " Maned Ready Application", 1 * w, 1 * w, constants.APPLICATION_STATUS_READY,
                            editor_group=eg.id, owner=owner)
    app.save()
    apps["ready"] = [{
        "id": app.id,
        "title": un + " Maned Completed Application"
    }]

    app = build_application(un + " Maned Completed Application", 2 * w, 2 * w, constants.APPLICATION_STATUS_COMPLETED,
                            editor_group=eg.id, owner=owner)
    app.save()
    apps["completed"] = [{
        "id": app.id,
        "title": un + " Maned Completed Application"
    }]

    app = build_application(un + " Maned Pending Application", 2 * w, 2 * w, constants.APPLICATION_STATUS_PENDING,
                            editor_group=eg.id, owner=owner)
    app.remove_editor()
    app.save()
    apps["pending"] = [{
        "id": app.id,
        "title": un + " Maned Pending Application"
    }]

    app = build_application(un + " Maned Low Priority Pending Application", 1 * w, 1 * w,
                            constants.APPLICATION_STATUS_PENDING,
                            editor_group=eponymous_group.id, owner=owner)
    app.remove_editor()
    app.save()
    apps["low_priority_pending"] = [{
        "id": app.id,
        "title": un + " Maned Low Priority Pending Application"
    }]

    lmur = build_application(un + " Last Month Maned Update Request", 5 * w, 5 * w,
                             constants.APPLICATION_STATUS_UPDATE_REQUEST,
                             editor_group=eponymous_group.id, owner=owner, update_request=True)
    lmur.save()

    tmur = build_application(un + " This Month Maned Update Request", 0, 0,
                             constants.APPLICATION_STATUS_UPDATE_REQUEST,
                             editor_group=eponymous_group.id, owner=owner, update_request=True)
    tmur.save()

    apps["update_request"] = [
        {
            "id": lmur.id,
            "title": un + " Last Month Maned Update Request"
        },
        {
            "id": tmur.id,
            "title": un + " This Month Maned Update Request"
        }
    ]

    return apps


def build_application(title, lmu_diff, cd_diff, status, editor=None, editor_group=None, owner=None,
                      update_request=False):
    source = ApplicationFixtureFactory.make_application_source()
    ap = models.Application(**source)
    ap.bibjson().title = title
    ap.set_id(ap.makeid())
    del ap.bibjson().discontinued_date

    if update_request:
        ap.application_type = constants.APPLICATION_TYPE_UPDATE_REQUEST
    else:
        ap.remove_current_journal()
        ap.remove_related_journal()
        ap.application_type = constants.APPLICATION_TYPE_NEW_APPLICATION

    ap.set_last_manual_update(dates.before(datetime.utcnow(), lmu_diff))
    ap.set_created(dates.before(datetime.utcnow(), cd_diff))
    ap.set_date_applied(dates.before(datetime.utcnow(), cd_diff))
    ap.set_application_status(status)

    if editor is not None:
        ap.set_editor(editor)

    if editor_group is not None:
        ap.set_editor_group(editor_group)

    if owner is not None:
        ap.set_owner(owner)

    ap.save()
    return ap
