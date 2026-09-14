from portality import constants
from doajtest.testdrive.factory import TestDrive
from portality import models
from portality.core import app

# Shared across administrative_search/journals.yml, editor_search/journals.yml,
# associate_search/journals.yml and publisher_search/journals.yml - those four
# testbook files all exercise the same journal search/facet interface, just as
# different roles, so one dataset covers all of them.


class Journals(TestDrive):
    def setup(self) -> dict:
        admin_un = self.create_random_str()
        admin_pw = self.create_random_str()
        admin_acc = models.Account.make_account(
            admin_un + "@example.com", admin_un, "Admin " + admin_un, [constants.ROLE_ADMIN]
        )
        admin_acc.set_password(admin_pw)
        admin_acc.save(blocking=True)

        editor_un = self.create_random_str()
        editor_pw = self.create_random_str()
        editor_acc = models.Account.make_account(
            editor_un + "@example.com", editor_un, "Editor " + editor_un, [constants.ROLE_EDITOR]
        )
        editor_acc.set_password(editor_pw)
        editor_acc.save(blocking=True)

        assoc_un = self.create_random_str()
        assoc_pw = self.create_random_str()
        assoc_acc = models.Account.make_account(
            assoc_un + "@example.com", assoc_un, "Associate " + assoc_un, [constants.ROLE_ASSOCIATE_EDITOR]
        )
        assoc_acc.set_password(assoc_pw)
        assoc_acc.save(blocking=True)

        publisher_acc, publisher_pw = self.publisher_account()

        eg = models.EditorGroup(**{"name": "Testdrive Journals Group " + self.run_seed})
        eg.set_maned(admin_acc.id)
        eg.set_editor(editor_acc.id)
        eg.add_associate(assoc_acc.id)
        eg.save(blocking=True)

        # The one journal a real tester will click through end to end: it carries a
        # licence, an APC, a note only privileged roles should be able to search for,
        # and a related application, and it's individually assigned to the associate
        # editor (not just group-owned), so it shows up under every one of the four
        # search views this testdrive supports.
        note_text = f"Peer review is conducted entirely by a rotating panel of trained parrots {self.run_seed}"
        flagship = self.journal(
            in_doaj=True,
            title=f"Journal of Sentient Houseplants {self.run_seed}",
            owner=publisher_acc.id,
            editor_group=eg.name,
            editor=assoc_acc.id,
            license_type="CC BY",
            has_apc=True,
            notes=[{"note": note_text, "author_id": admin_acc.id}],
        )

        related_app = self.application(
            title=f"Journal of Sentient Houseplants {self.run_seed}",
            editor=editor_acc.id,
            status=constants.APPLICATION_STATUS_ACCEPTED,
        )
        flagship.add_related_application(related_app.id, date_accepted="2020-01-01T00:00:00Z")
        flagship.save(blocking=True)

        # Same group, same owner, no per-journal editor assignment and no APC - shows
        # up in the editor's "group journals" and the publisher's dashboard, but not
        # in the associate editor's "your journals" (assignment-scoped, not
        # group-scoped). Also gives the licence and APC facets a second value to filter on.
        no_apc = self.journal(
            in_doaj=True,
            title=f"Journal of Uneventful Volcanology {self.run_seed}",
            owner=publisher_acc.id,
            editor_group=eg.name,
            license_type="CC BY-NC-ND",
            has_apc=False,
        )

        # Withdrawn from DOAJ - exercises the "In DOAJ: No" facet (unlinked title,
        # "Last Withdrawn" metadata) while still belonging to the same owner/group/associate.
        withdrawn = self.journal(
            in_doaj=False,
            title=f"Journal of Withdrawn Enthusiasm {self.run_seed}",
            owner=publisher_acc.id,
            editor_group=eg.name,
            editor=assoc_acc.id,
            license_type="CC BY",
        )

        base = app.config.get("BASE_URL", "")

        def journal_report(j):
            return {
                "id": j.id,
                "admin_form": base + "/admin/journal/" + j.id,
                "toc": base + "/toc/" + j.bibjson().pissn,
            }

        return {
            "notes": [
                "Log in as 'admin', 'editor', 'associate' or 'publisher' to see this data "
                "through each role's journal search: /admin/, /editor/group_journals, "
                "/editor/your_journals and /publisher/ respectively.",
                "'Sentient Houseplants' is the main journal to click through: it has a "
                "licence, an APC, a related record, and a note - search admin/editor/"
                "associate note search for the distinctive text below, then confirm the "
                "same text finds nothing on the public search or API.",
                "'Uneventful Volcanology' is owned and grouped the same way, but is not "
                "individually assigned to the associate editor - it should appear under "
                "the editor's group journals but NOT the associate's 'your journals'.",
                "'Withdrawn Enthusiasm' is not in DOAJ - use it for the 'In DOAJ: No' facet.",
                f"Distinctive note text to search for: {note_text}",
            ],
            "accounts": {
                "admin": {"username": admin_acc.id, "password": admin_pw},
                "editor": {"username": editor_acc.id, "password": editor_pw},
                "associate": {"username": assoc_acc.id, "password": assoc_pw},
                "publisher": {"username": publisher_acc.id, "password": publisher_pw},
            },
            "journals": {
                "Sentient Houseplants": journal_report(flagship),
                "Uneventful Volcanology": journal_report(no_apc),
                "Withdrawn Enthusiasm": journal_report(withdrawn),
            },
            "applications": {
                "Sentient Houseplants (related application)": related_app.id,
            },
            "editor_group": {"id": eg.id, "name": eg.name},
        }

    def teardown(self, params) -> dict:
        for acc in params["accounts"].values():
            models.Account.remove_by_id(acc["username"])
        for j in params["journals"].values():
            models.Journal.remove_by_id(j["id"])
        for aid in params["applications"].values():
            models.Application.remove_by_id(aid)
        models.EditorGroup.remove_by_id(params["editor_group"]["id"])
        return self.SUCCESS
