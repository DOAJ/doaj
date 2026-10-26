from portality import constants
from portality import models
from doajtest.testdrive.factory import TestDrive


class ApplicationStateChange(TestDrive):
    """
    Setup for doajtest/testbook/application_state_change/application_state_change.yml.

    Each of the five tests in that file destructively changes one record's status
    (accepting/rejecting locks it against further edits), so this builds five
    independent Ready-status records - one per test - each on its own journal
    where relevant, so acting on one can't interfere with another:
      - a new application to accept
      - a new application to reject
      - an update request (against its own in-DOAJ journal) to accept
      - an update request (against its own in-DOAJ journal) to reject
      - an update request (against its own in-DOAJ journal) to send back for revisions

    All five are owned by the same publisher account and assigned to the same
    editor/editor group, so they show up as real, actionable records in the admin
    "Applications/Update Requests" search rather than tripping over a missing
    owner account when accepted (accept_application looks up the owner account to
    attach the resulting journal to it and email it).
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
        editor, editor_pw = self._account("Editor", [constants.ROLE_ASSOCIATE_EDITOR])

        eg = models.EditorGroup(**{
            "name": "Application State Change " + self.run_seed,
            "editor": editor.id,
            "maned": admin.id,
            "associates": [],
        })
        eg.save()

        applications = []
        journals = []

        accept_new = self.application(
            title="Application State Change - Accept New Application " + self.run_seed,
            status=constants.APPLICATION_STATUS_READY,
            owner=publisher.id, editor_group=eg.name, editor=editor.id,
        )
        reject_new = self.application(
            title="Application State Change - Reject New Application " + self.run_seed,
            status=constants.APPLICATION_STATUS_READY,
            owner=publisher.id, editor_group=eg.name, editor=editor.id,
        )
        applications += [accept_new, reject_new]

        ur_labels = ["Accept Update Request", "Reject Update Request", "Revisions Required Update Request"]
        urs = {}
        for label in ur_labels:
            j = self.journal(
                title="Application State Change - " + label + " Journal " + self.run_seed,
                owner=publisher.id, editor_group=eg.name, editor=editor.id,
            )
            ur = self.application(
                title="Application State Change - " + label + " " + self.run_seed,
                status=constants.APPLICATION_STATUS_READY,
                owner=publisher.id, editor_group=eg.name, editor=editor.id,
                current_journal=j.id,
            )
            j.set_current_application(ur.id)
            j.save()
            journals.append(j)
            applications.append(ur)
            urs[label] = ur.id

        models.Application.refresh()
        models.Journal.refresh()

        report = {
            "admin": {"username": admin.id, "password": admin_pw},
            "publisher": {"username": publisher.id, "password": publisher_pw},
            "editor": {"username": editor.id, "password": editor_pw},
        }
        self.report_application_ids(applications, report)
        self.report_journal_ids(journals, report)
        report["editor_group"] = {"name": eg.name}
        report["applications_named"] = {
            "accept_new_application": accept_new.id,
            "reject_new_application": reject_new.id,
            "accept_update_request": urs["Accept Update Request"],
            "reject_update_request": urs["Reject Update Request"],
            "revisions_update_request": urs["Revisions Required Update Request"],
        }
        return report

    def teardown(self, params) -> dict:
        for key in ("admin", "publisher", "editor"):
            models.Account.remove_by_id(params[key]["username"])
        self.teardown_applications(params)
        self.teardown_journals(params)

        eg = models.EditorGroup.pull_by_key("name", params["editor_group"]["name"])
        if eg is not None:
            eg.delete()

        return self.SUCCESS
