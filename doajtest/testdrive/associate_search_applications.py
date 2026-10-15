from portality import constants
from doajtest.testdrive.factory import TestDrive
from portality import models
from portality.models import EditorGroup


class AssociateSearchApplications(TestDrive):
    def setup(self) -> dict:
        associate_un = self.create_random_str()
        associate_pw = self.create_random_str()
        associate_acc = models.Account.make_account(
            associate_un + "@example.com", associate_un, "Associate " + associate_un,
            [constants.ROLE_ASSOCIATE_EDITOR]
        )
        associate_acc.set_password(associate_pw)
        associate_acc.save(blocking=True)

        eg = EditorGroup(**{
            "name": "Associate Search Applications Group " + self.run_seed,
            "maned": associate_acc.id,
            "editor": associate_acc.id,
            "associates": [associate_acc.id],
        })
        eg.save(blocking=True)

        # A spread of statuses and countries so the facets/sort/status-link steps in
        # the test have something real to filter, sort and click on. All assigned to
        # the same associate editor, since /editor/your_applications is scoped by
        # application.editor, not just editor_group membership.
        specs = [
            ("Accepted Application", constants.APPLICATION_STATUS_ACCEPTED, "US"),
            ("Rejected Application", constants.APPLICATION_STATUS_REJECTED, "GB"),
            ("Ready Application One", constants.APPLICATION_STATUS_READY, "FR"),
            ("Ready Application Two", constants.APPLICATION_STATUS_READY, "DE"),
            ("Pending Application", constants.APPLICATION_STATUS_PENDING, "IN"),
        ]

        applications = []
        for title, status, country in specs:
            a = self.application(
                title=f"{title} {self.run_seed}",
                editor_group=eg.name, editor=associate_acc.id,
                status=status,
                save=False,
            )
            a.bibjson().country = country
            a.save(blocking=True)
            applications.append(a)

        report = {}
        self.report_application_ids(applications, report)
        report["accounts"] = {
            "associate": {"username": associate_acc.id, "password": associate_pw},
        }
        report["editor_group"] = {"id": eg.id, "name": eg.name}
        report["notes"] = [
            "Log in as the 'associate' account below, then go to "
            "/editor/your_applications.",
            "5 applications are assigned to this account, covering Accepted, "
            "Rejected, Ready (x2) and Pending statuses, with different publisher "
            "countries, for the facet/sort/status-link steps in this test.",
        ]
        return report

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["accounts"]["associate"]["username"])
        for aid in params.get("applications", []):
            models.Application.remove_by_id(aid)
        EditorGroup.remove_by_id(params["editor_group"]["id"])
        return self.SUCCESS
