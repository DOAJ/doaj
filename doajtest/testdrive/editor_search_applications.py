from portality import constants
from portality import models
from portality.lib import dates
from doajtest.testdrive.factory import TestDrive


class EditorSearchApplications(TestDrive):
    """
    Setup for the testbook test editor_search/applications.yml
    ("Editor search / Applications / Test Editors Application Search").

    The test drives the faceted search at /editor/group_applications, which is
    scoped to the applications whose editor_group is one of the groups the
    logged-in user is the *editor* of (see query_filters.editor). It needs
    enough records (100+) to exercise paging and the page-size control, and
    enough variety for the facets, the sort options and the finished-vs-review
    link steps.

    Builds: one editor account + one editor group it edits, three associate
    editor members, and 120 applications in that group spread across statuses,
    editor assignments, publisher countries and publisher names.
    """

    APPLICATION_COUNT = 120

    # status -> how many of the 120 applications get it
    STATUS_SPREAD = [
        (constants.APPLICATION_STATUS_PENDING, 40),
        (constants.APPLICATION_STATUS_IN_PROGRESS, 30),
        (constants.APPLICATION_STATUS_ACCEPTED, 20),
        (constants.APPLICATION_STATUS_REJECTED, 15),
        (constants.APPLICATION_STATUS_READY, 8),
        (constants.APPLICATION_STATUS_COMPLETED, 4),
        (constants.APPLICATION_STATUS_ON_HOLD, 2),
        (constants.APPLICATION_STATUS_REVISIONS_REQUIRED, 1),
    ]

    # more than 10 so the "Country of publisher" facet is capped at 10 shown values
    COUNTRIES = ["US", "GB", "FR", "DE", "BR", "IN", "NG", "ZA", "JP", "AU",
                 "CA", "MX", "IT", "ES", "SE", "KE"]

    PUBLISHERS = ["Editor Search Press", "Open Access Collective", "Meridian Publishing",
                  "Aurora Academic", "Continental Journals", "Latitude Open"]

    # a distinctive word dropped into a handful of titles for the search-box step
    NEEDLE = "Zebrafish"

    def _account(self, prefix, roles):
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, prefix + " " + un, roles)
        acc.set_password(pw)
        acc.save()
        return acc, pw

    def setup(self) -> dict:
        editor_acc, editor_pw = self._account("Editor Search", ["editor"])

        associates = []
        for i in range(3):
            acc, _ = self._account("Associate Editor " + str(i + 1), ["associate_editor"])
            associates.append(acc.id)

        eg = models.EditorGroup(**{
            "name": "Editor Search Applications Group " + self.run_seed,
            "editor": editor_acc.id,
            "maned": editor_acc.id,
            "associates": associates,
        })
        eg.save()

        statuses = []
        for status, n in self.STATUS_SPREAD:
            statuses.extend([status] * n)
        # pad/trim to exactly APPLICATION_COUNT
        statuses = (statuses + [constants.APPLICATION_STATUS_PENDING] * self.APPLICATION_COUNT)[:self.APPLICATION_COUNT]

        application_ids = []
        for i in range(self.APPLICATION_COUNT):
            status = statuses[i]

            title = "Editor Search {seed} #{i:03d} ({status})".format(
                seed=self.run_seed, i=i, status=status)
            if i % 24 == 0:
                title = self.NEEDLE + " " + title

            a = self.application(title=title, editor_group=eg.name, status=status, save=False)

            # assign roughly half, round-robin across the three associates; leave the
            # rest unassigned so the "Has Associate Editor?" and "Editor" facets both work
            if i % 2 == 0:
                a.set_editor(associates[i % len(associates)])
            else:
                a.remove_editor()

            bj = a.bibjson()
            bj.publisher_country = self.COUNTRIES[i % len(self.COUNTRIES)]
            bj.publisher_name = self.PUBLISHERS[i % len(self.PUBLISHERS)]

            applied = dates.before_now(60 * 60 * 24 * (2 * i))
            a.set_created(applied)
            a.set_date_applied(applied)
            a.set_last_manual_update(applied)

            a.save()
            application_ids.append(a.id)

        models.Application.refresh()

        report = {
            "account": {
                "username": editor_acc.id,
                "password": editor_pw
            },
            "associate_editors": associates,
            "editor_group": {
                "id": eg.id,
                "name": eg.name
            },
            "applications": application_ids,
            "notes": [
                "Log in as the 'account' below (an editor), then go to /editor/group_applications.",
                "{n} applications are in this editor's group, so paging and the page-size "
                "control have plenty of data.".format(n=self.APPLICATION_COUNT),
                "Statuses covered: pending, in progress, accepted, rejected, ready, completed, "
                "on hold, revisions required - so both the 'View finished application' "
                "(accepted/rejected) and 'Review application' (pending/in progress) link "
                "steps have results.",
                "Publisher country and publisher name vary across the set for the facets; "
                "about half the applications are assigned to one of three associate editors "
                "and half are unassigned.",
                "Search the box for '{needle}' to match a small subset of the "
                "applications.".format(needle=self.NEEDLE),
            ]
        }
        return report

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["account"]["username"])
        for assoc in params["associate_editors"]:
            models.Account.remove_by_id(assoc)
        for aid in params.get("applications", []):
            models.Application.remove_by_id(aid)
        models.EditorGroup.remove_by_id(params["editor_group"]["id"])
        models.Application.refresh()
        return self.SUCCESS
