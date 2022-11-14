from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from portality.lib import dates
from portality import models
from datetime import datetime


class TodoEditor(TestDrive):

    def setup(self) -> dict:
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, "TodoEditor " + un, ["editor"])
        acc.set_password(pw)
        acc.save()

        gn = "TodoEditor Group " + un
        eg = models.EditorGroup(**{
            "name": gn
        })
        eg.set_editor(acc.id)
        eg.save()

        apps = build_applications(un, eg)

        return {
            "account": {
                "username": acc.id,
                "password": pw
            },
            "editor_group": {
                "id": eg.id,
                "name": eg.name
            },
            "applications": apps
        }


def build_application(title, lmu_diff, cd_diff, status, editor=None, editor_group=None):
    source = ApplicationFixtureFactory.make_application_source()
    ap = models.Application(**source)
    ap.bibjson().title = title
    ap.set_id(ap.makeid())
    ap.set_last_manual_update(dates.before(datetime.utcnow(), lmu_diff))
    ap.set_created(dates.before(datetime.utcnow(), cd_diff))
    ap.set_application_status(status)

    if editor is not None:
        ap.set_editor(editor)

    if editor_group is not None:
        ap.set_editor_group(editor_group)

    ap.save()
    return ap


def build_applications(un, eg):
    w = 7 * 24 * 60 * 60

    apps = {}

    app = build_application(un + " Stalled Application", 6 * w, 12 * w, constants.APPLICATION_STATUS_IN_PROGRESS,
                                 editor_group=eg.name)
    app.save()
    apps["stalled"] = [{
        "id": app.id,
        "title": un + " Stalled Application"
    }]

    app = build_application(un + " Old Application", 8 * w, 8 * w, constants.APPLICATION_STATUS_IN_PROGRESS,
                                 editor_group=eg.name)
    app.save()
    apps["old"] = [{
        "id": app.id,
        "title": un + " Old Application"
    }]

    app = build_application(un + " Completed Application", 1 * w, 1 * w, constants.APPLICATION_STATUS_COMPLETED,
                                 editor_group=eg.name)
    app.save()
    apps["completed"] = [{
        "id": app.id,
        "title": un + " Completed Application"
    }]

    app = build_application(un + " Pending Application", 1 * w, 1 * w, constants.APPLICATION_STATUS_PENDING,
                                 editor_group=eg.name)
    app.remove_editor()
    app.save()
    apps["pending"] = [{
        "id": app.id,
        "title": un + " Pending Application"
    }]

    return apps