from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from portality.lib import dates
from portality import models
from datetime import datetime


class PublisherCsvUpload(TestDrive):

    def setup(self) -> dict:
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, "Publisher " + un, [constants.ROLE_PUBLISHER])
        acc.set_password(pw)
        acc.save()

        def eliminate_existing(issns):
            for issn in issns:
                existing = models.Journal.find_by_issn(issn)
                for e in existing:
                    e.delete()

        def make_journal(title, pissn, eissn, owner=None, in_doaj=True):
            source = JournalFixtureFactory.make_journal_source(in_doaj=in_doaj)
            journal = models.Journal(**source)
            journal.set_id(journal.makeid())
            journal.set_owner(owner)
            bj = journal.bibjson()
            bj.title = title
            bj.pissn = pissn
            bj.eissn = eissn
            journal.save()
            return journal

        # ensure that the issns we're going to use aren't already in use
        eliminate_existing([
            "0000-0001",
            "0000-0002",
            "0000-0003",
            "0000-0004",
            "0000-0005",
            "0000-0006",
            "0000-0007",
            "0000-0008",
            "0000-0009",
            "0000-0010",
            "0000-0011",
            "0000-0012",
            "0000-0013",
            "0000-0014",
            "0000-0015",
            "0000-0016"
        ])

        # 2 valid journals
        valid1 = make_journal("Electronics Letters", "0000-0001", "0000-0002", owner=acc.id)
        valid2 = make_journal("Journal of Veterinary Internal Medicine", "0000-0003", "0000-0004", owner=acc.id)

        # note that we don't make 0000-0005, as this journal will come back as not found

        # Not the owner
        not_owner = make_journal("Not Owner", "0000-0007", "0000-0008", owner="someone_else")

        # No updates
        no_updates = make_journal("No Updates", "0000-0009", "0000-0010", owner=acc.id)

        # Changed the title
        changed_title = make_journal("Original Title", "0000-0011", "0000-0012", owner=acc.id)

        # Withdrawn Journal
        withdrawn = make_journal("Withdrawn Journal", "0000-0013", "0000-0014", owner=acc.id, in_doaj=False)

        # validation failure
        validation_fail = make_journal("Validation Failure", "0000-0015", "0000-0016", owner=acc.id)

        return {
            "account": {
                "username": acc.id,
                "password": pw
            },
            "journals": {
                "valid1": valid1.id,
                "valid2": valid2.id,
                "not_owner": not_owner.id,
                "no_updates": no_updates.id,
                "changed_title": changed_title.id,
                "withdrawn": withdrawn.id,
                "validation_fail": validation_fail.id
            }
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["account"]["username"])
        for k, v in params["journals"].items():
            models.Journal.remove_by_id(v)
        return {"status": "success"}


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
    ap.remove_current_journal()
    ap.remove_related_journal()
    ap.application_type = constants.APPLICATION_TYPE_NEW_APPLICATION
    ap.set_id(ap.makeid())
    ap.set_last_manual_update(dates.before(datetime.utcnow(), lmu_diff))
    ap.set_created(dates.before(datetime.utcnow(), cd_diff))
    ap.set_application_status(status)

    if editor is not None:
        ap.set_editor(editor)

    ap.save()
    return ap
