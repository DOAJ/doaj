from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from portality.lib import dates
from portality import models
from datetime import datetime


class TodoAssociate(TestDrive):

    def setup(self) -> dict:
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, "TodoAssociate " + un, [constants.ROLE_ASSOCIATE_EDITOR])
        acc.set_password(pw)
        acc.save()

        gn = "TodoAssociate Group " + un
        eg = models.EditorGroup(**{
            "name": gn
        })
        eg.add_associate(acc.id)
        eg.save()

        apps = build_applications(un)

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


def build_applications(un):
    w = 7 * 24 * 60 * 60

    apps = {}

    app = build_application(un + " Stalled Application", 3 * w, 3 * w,
                                 constants.APPLICATION_STATUS_IN_PROGRESS, editor=un)
    app.save()
    apps["stalled"] = [{
        "id": app.id,
        "title": un + " Stalled Application"
    }]

    app = build_application(un + " Old Application", 6 * w, 6 * w, constants.APPLICATION_STATUS_IN_PROGRESS,
                                 editor=un)
    app.save()
    apps["old"] = [{
        "id": app.id,
        "title": un + " Old Application"
    }]

    app = build_application(un + " Pending Application", 1 * w, 1 * w, constants.APPLICATION_STATUS_PENDING,
                                 editor=un)
    app.save()
    apps["pending"] = [{
        "id": app.id,
        "title": un + " Pending Application"
    }]

    app = build_application(un + " All Other Applications", 2 * w, 2 * w,
                                 constants.APPLICATION_STATUS_IN_PROGRESS, editor=un)
    app.save()
    apps["all"] = [{
        "id": app.id,
        "title": un + " All Other Applications"
    }]

    return apps


def build_application(title, lmu_diff, cd_diff, status, editor=None):
    source = ApplicationFixtureFactory.make_application_source()
    ap = models.Application(**source)
    ap.bibjson().title = title
    ap.set_id(ap.makeid())
    ap.set_last_manual_update(dates.before(datetime.utcnow(), lmu_diff))
    ap.set_created(dates.before(datetime.utcnow(), cd_diff))
    ap.set_application_status(status)

    if editor is not None:
        ap.set_editor(editor)

    ap.save()
    return ap
