from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.testdrive.todo_editor import build_application
from portality import models


class EditorialGroupStatus(TestDrive):
    """
    Setup for the testbook tests:
      - dashboard/editorial_group_status.yml   (Editorial Group Status - ManEd)
      - dashboards/editorial_group_status.yml  (Editorial Group Status for Editors)

    Builds one account which is admin + editor, and which is both the managing
    editor and the editor of two editor groups.  Each group has three associate
    editor members and a spread of applications: some assigned to a couple of the
    associates, some left unassigned, across a range of statuses.  This gives the
    dashboard "Activity" panel something to show for the group totals, the
    per-associate-editor counts, the unassigned count and the by-status breakdown.
    """

    # (title suffix, status, associate index or None for unassigned)
    GROUP_ONE_APPS = [
        ("Assed 1 Pending", constants.APPLICATION_STATUS_PENDING, 0),
        ("Assed 1 In Progress", constants.APPLICATION_STATUS_IN_PROGRESS, 0),
        ("Assed 1 Completed", constants.APPLICATION_STATUS_COMPLETED, 0),
        ("Assed 2 In Progress", constants.APPLICATION_STATUS_IN_PROGRESS, 1),
        ("Assed 2 Ready", constants.APPLICATION_STATUS_READY, 1),
        ("Unassigned Pending", constants.APPLICATION_STATUS_PENDING, None),
        ("Unassigned In Progress", constants.APPLICATION_STATUS_IN_PROGRESS, None),
        ("Unassigned On Hold", constants.APPLICATION_STATUS_ON_HOLD, None),
    ]

    GROUP_TWO_APPS = [
        ("Assed 1 In Progress", constants.APPLICATION_STATUS_IN_PROGRESS, 0),
        ("Assed 1 Ready", constants.APPLICATION_STATUS_READY, 0),
        ("Assed 3 Pending", constants.APPLICATION_STATUS_PENDING, 2),
        ("Assed 3 In Progress", constants.APPLICATION_STATUS_IN_PROGRESS, 2),
        ("Unassigned Pending 1", constants.APPLICATION_STATUS_PENDING, None),
        ("Unassigned Pending 2", constants.APPLICATION_STATUS_PENDING, None),
        ("Unassigned In Progress", constants.APPLICATION_STATUS_IN_PROGRESS, None),
        ("Unassigned Completed", constants.APPLICATION_STATUS_COMPLETED, None),
    ]

    def _account(self, prefix, roles):
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, prefix + " " + un, roles)
        acc.set_password(pw)
        acc.save()
        return acc, pw

    def _group(self, name, maned, editor, associates):
        eg = models.EditorGroup(**{"name": name})
        eg.set_maned(maned)
        eg.set_editor(editor)
        for a in associates:
            eg.add_associate(a)
        eg.save()
        return eg

    def _applications(self, un, group_name, associates, spec):
        apps = []
        for suffix, status, assoc_idx in spec:
            title = un + " " + group_name + " - " + suffix
            editor = associates[assoc_idx] if assoc_idx is not None else None
            ap = build_application(title, 0, 0, status, editor=editor, editor_group=group_name)
            if editor is None:
                ap.remove_editor()
                ap.save()
            apps.append({"id": ap.id, "title": title})
        return apps

    def setup(self) -> dict:
        un = self.create_random_str()

        main, pw = self._account("EditorialGroupStatus", [constants.ROLE_ADMIN, "editor"])

        associates = []
        for i in range(3):
            acc, _ = self._account("Associate Editor " + str(i + 1), ["associate_editor"])
            associates.append(acc.id)

        gn1 = "EGS Group One " + un
        gn2 = "EGS Group Two " + un
        eg1 = self._group(gn1, main.id, main.id, associates)
        eg2 = self._group(gn2, main.id, main.id, associates)

        apps1 = self._applications(un, gn1, associates, self.GROUP_ONE_APPS)
        apps2 = self._applications(un, gn2, associates, self.GROUP_TWO_APPS)

        return {
            "account": {
                "username": main.id,
                "password": pw
            },
            "associate_editors": associates,
            "group_one": {
                "id": eg1.id,
                "name": eg1.name
            },
            "group_two": {
                "id": eg2.id,
                "name": eg2.name
            },
            "applications": {
                "group_one": apps1,
                "group_two": apps2
            }
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["account"]["username"])
        for assoc in params["associate_editors"]:
            models.Account.remove_by_id(assoc)

        for group in params["applications"].values():
            for detail in group:
                models.Application.remove_by_id(detail["id"])

        models.EditorGroup.remove_by_id(params["group_one"]["id"])
        models.EditorGroup.remove_by_id(params["group_two"]["id"])

        return {"status": "success"}
