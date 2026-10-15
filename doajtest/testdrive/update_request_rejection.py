from portality import constants
from portality import models
from doajtest.testdrive.factory import TestDrive


class UpdateRequestRejection(TestDrive):
    """
    Setup for doajtest/testbook/application_state_change/update_request_rejection.yml.

    Every one of that file's four tests exercises the update-request reject/
    unreject/resubmit logic (portality/bll/services/application.py
    unreject_application), which hinges on Application.find_latest_by_current_journal:
    an update request can't be unrejected if a *newer* update request is currently
    open against the same journal.

    Saving a *live* update request (one with current_journal set) also runs the real
    UR_CONCURRENCY_TIMEOUT guard (ConcurrentUpdateRequestService), which blocks a
    second submission against the same journal within that window (10s by default).
    Two of the four tests script the tester into submitting two update requests
    against the same journal in quick succession, which risks tripping that guard
    for real. To avoid that, any "older" update request each test needs is built
    here already in its *final* historical state - e.g. already rejected, with
    related_journal set and current_journal never touched - so it never goes near
    that guard at all. Only the one live submission each test is actually about is
    left for the tester to perform for real, via the publisher dashboard.

    Provides one admin account, one publisher account (owner of all four journals,
    so "My update requests" works for it), and four journals:
      - journal_1: clean, no update request history - for "Reject, Unreject and
        Accept" (the only test that needs no pre-built history, since it only ever
        has one live update request)
      - journal_2: has one pre-built, already-rejected update request - for
        "Reject then Resubmit", so the tester only has to submit the *second*
        (resubmitted) update request live
      - journal_3: has one pre-built rejected update request AND one pre-built
        currently-open update request - for "Reject, Resubmit, Unreject", which
        proves you can't unreject the older one while the newer one is open
      - journal_4: has two pre-built rejected update requests, with clearly
        different APC amounts and an older/newer date_rejected - for "Reject,
        Reject, Unreject", which proves accepting the *older* rejected update
        request still works (and wins) even though a newer, also-rejected one
        exists for the same journal
    """

    def _account(self, prefix, roles):
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, prefix + " " + un, roles)
        acc.set_password(pw)
        acc.save()
        return acc, pw

    def setup(self) -> dict:
        admin, admin_pw = self._account("Admin", [constants.ROLE_ADMIN])
        publisher, publisher_pw = self._account("Publisher", [constants.ROLE_PUBLISHER])

        journals = []
        applications = []

        # journal_1: clean - "Reject, Unreject and Accept" makes its one live UR here
        journal_1 = self.journal(
            title="Update Request Rejection - Reject Unreject Accept " + self.run_seed,
            owner=publisher.id, has_apc=False,
        )
        journals.append(journal_1)

        # journal_2: one pre-built rejected UR in its past - "Reject then Resubmit"
        # submits its one live (resubmitted) UR against this journal
        journal_2 = self.journal(
            title="Update Request Rejection - Reject Then Resubmit " + self.run_seed,
            owner=publisher.id, has_apc=False,
        )
        ur2_old = self.application(
            title="Update Request Rejection - Reject Then Resubmit - superseded UR " + self.run_seed,
            owner=publisher.id, is_update_request=True, related_journal=journal_2.id,
            status=constants.APPLICATION_STATUS_REJECTED, date_rejected="2025-01-01T00:00:00Z",
        )
        journals.append(journal_2)
        applications.append(ur2_old)

        # journal_3: one pre-built rejected UR, plus one pre-built *currently open*
        # UR - proves the rejected one can't be unrejected while the open one exists
        journal_3 = self.journal(
            title="Update Request Rejection - Reject Resubmit Unreject " + self.run_seed,
            owner=publisher.id, has_apc=False,
        )
        ur3_rejected = self.application(
            title="Update Request Rejection - Reject Resubmit Unreject - rejected UR (try to unreject this one) " + self.run_seed,
            owner=publisher.id, is_update_request=True, related_journal=journal_3.id,
            status=constants.APPLICATION_STATUS_REJECTED, date_rejected="2025-01-01T00:00:00Z",
        )
        ur3_open = self.application(
            title="Update Request Rejection - Reject Resubmit Unreject - resubmitted UR (currently open) " + self.run_seed,
            owner=publisher.id, current_journal=journal_3.id,
            status=constants.APPLICATION_STATUS_UPDATE_REQUEST,
        )
        journal_3.set_current_application(ur3_open.id)
        journal_3.save()
        journals.append(journal_3)
        applications += [ur3_rejected, ur3_open]

        # journal_4: two pre-built rejected URs with clearly different APC amounts
        # and an older/newer date_rejected - proves accepting the older one directly
        # still works, and that its data (not the newer rejected one's) wins
        journal_4 = self.journal(
            title="Update Request Rejection - Reject Reject Unreject " + self.run_seed,
            owner=publisher.id, has_apc=False,
        )
        ur4_older = self.application(
            title="Update Request Rejection - Reject Reject Unreject - OLDER rejected UR, accept this one " + self.run_seed,
            owner=publisher.id, is_update_request=True, related_journal=journal_4.id,
            status=constants.APPLICATION_STATUS_REJECTED, date_rejected="2025-01-01T00:00:00Z",
            has_apc=True, apc=("USD", 100),
        )
        ur4_newer = self.application(
            title="Update Request Rejection - Reject Reject Unreject - newer rejected UR, ignore this one " + self.run_seed,
            owner=publisher.id, is_update_request=True, related_journal=journal_4.id,
            status=constants.APPLICATION_STATUS_REJECTED, date_rejected="2025-02-01T00:00:00Z",
            has_apc=True, apc=("USD", 250),
        )
        journals.append(journal_4)
        applications += [ur4_older, ur4_newer]

        models.Application.refresh()
        models.Journal.refresh()

        report = {
            "admin": {"username": admin.id, "password": admin_pw},
            "publisher": {"username": publisher.id, "password": publisher_pw},
        }
        self.report_journal_ids(journals, report)
        self.report_application_ids(applications, report)
        report["journals_named"] = {
            "reject_unreject_accept": journal_1.id,
            "reject_then_resubmit": journal_2.id,
            "reject_resubmit_unreject": journal_3.id,
            "reject_reject_unreject": journal_4.id,
        }
        report["applications_named"] = {
            "reject_then_resubmit__superseded_ur": ur2_old.id,
            "reject_resubmit_unreject__rejected_ur": ur3_rejected.id,
            "reject_resubmit_unreject__open_ur": ur3_open.id,
            "reject_reject_unreject__older_ur": ur4_older.id,
            "reject_reject_unreject__newer_ur": ur4_newer.id,
        }
        return report

    def teardown(self, params) -> dict:
        for key in ("admin", "publisher"):
            models.Account.remove_by_id(params[key]["username"])
        self.teardown_applications(params)
        self.teardown_journals(params)
        return self.SUCCESS
