from portality import constants
from portality import models
from portality.core import app
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from doajtest.testdrive.factory import TestDrive


class JournalForm(TestDrive):
    """
    Setup for the testbook tests in journal_form/maned_form.yml
    ("Journal Form / ManEd Form").

    Provides:
      - two admin accounts (admin1, admin2) - both can open the same journal, for
        the "Note features for admin" test (add note as admin1, view-but-not-edit
        as admin2)
      - a publisher account that owns the journals, plus a second publisher
        account to transfer ownership to (the "Journal Owner Transfer" test)
      - an editor and two associate editors, in two editor groups, so the
        "Editor Group" and "Assigned to" autocomplete/dropdowns in the Editorial
        area have something to resolve
      - one "primary" in-DOAJ journal, owned by the publisher and assigned to the
        first editor group + the editor, with NO owner-transfer / full-review /
        withdrawal history and no notes - the clean target for the note, owner
        transfer and full review steps
      - two spare in-DOAJ journals for the withdraw/reinstate and
        "Subscribe to Open" steps, so those don't disturb the primary journal

    NB: journal_form/editor_form.yml and journal_form/associate_form.yml are NOT
    covered here - editors and associate editors no longer have an editable
    journal form (the /editor/your_journals, /editor/group_journals and editable
    /editor/journal/<id> routes have been removed; only a read-only view remains).
    """

    def _account(self, prefix, roles):
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, prefix + " " + un, roles)
        acc.set_password(pw)
        acc.save()
        return acc, pw

    def _journal(self, title, owner, editor_group=None, editor=None):
        source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        admin = source["admin"]
        for k in ("last_owner_transfer", "last_withdrawn", "last_reinstated",
                  "last_full_review", "current_application", "related_applications", "notes"):
            admin.pop(k, None)

        j = models.Journal(**source)
        j.remove_current_application()
        j.set_id(j.makeid())
        j.bibjson().pissn = self.generate_unique_issn()
        j.bibjson().eissn = self.generate_unique_issn()
        j.bibjson().title = title
        j.set_owner(owner)
        if editor_group is not None:
            j.set_editor_group(editor_group)
        if editor is not None:
            j.set_editor(editor)
        j.save()
        return j

    def setup(self) -> dict:
        admin1, admin1_pw = self._account("Admin", [constants.ROLE_ADMIN])
        admin2, admin2_pw = self._account("Admin", [constants.ROLE_ADMIN])

        owner, owner_pw = self._account("Publisher", [constants.ROLE_PUBLISHER])
        transfer_to, transfer_to_pw = self._account("Publisher", [constants.ROLE_PUBLISHER])

        editor, editor_pw = self._account("Editor", [constants.ROLE_EDITOR])
        associates = []
        for i in range(2):
            acc, _ = self._account("Associate Editor " + str(i + 1), [constants.ROLE_ASSOCIATE_EDITOR])
            associates.append(acc.id)

        eg1 = models.EditorGroup(**{
            "name": "Journal Form Editors " + self.run_seed,
            "editor": editor.id,
            "maned": admin1.id,
            "associates": associates,
        })
        eg1.save()

        eg2 = models.EditorGroup(**{
            "name": "Journal Form Reviewers " + self.run_seed,
            "editor": editor.id,
            "maned": admin1.id,
            "associates": associates,
        })
        eg2.save()

        primary = self._journal("Journal Form Primary " + self.run_seed, owner.id, eg1.name, editor.id)

        spares = []
        for i in range(2):
            j = self._journal("Journal Form Spare " + str(i + 1) + " " + self.run_seed, owner.id, eg1.name)
            spares.append({"id": j.id, "title": j.bibjson().title})

        models.Journal.refresh()

        base = app.config.get("BASE_URL", "")
        return {
            "admin_1": {"username": admin1.id, "password": admin1_pw},
            "admin_2": {"username": admin2.id, "password": admin2_pw},
            "publisher_owner": {"username": owner.id, "password": owner_pw},
            "publisher_transfer_target": {"username": transfer_to.id, "password": transfer_to_pw},
            "editor": {"username": editor.id, "password": editor_pw},
            "associate_editors": associates,
            "editor_groups": [eg1.name, eg2.name],
            "primary_journal": {
                "id": primary.id,
                "title": primary.bibjson().title,
                "admin_form": base + "/admin/journal/" + primary.id,
                "toc": base + "/toc/" + primary.id,
            },
            "spare_journals": spares,
            "notes": [
                "Log in as admin_1 (and admin_2 in a separate private window) for the "
                "'Note features for admin' test - both can open the primary journal at "
                "its admin_form URL.",
                "primary_journal is in DOAJ, owned by publisher_owner, assigned to the "
                "'Journal Form Editors ...' group and the editor account, with no owner "
                "transfer / full review / withdrawal history and no notes - use it for the "
                "note, owner transfer and full review steps.",
                "Use publisher_transfer_target as the new owner in the 'Journal Owner "
                "Transfer' test.",
                "Use a spare_journal for the withdraw/reinstate and Subscribe to Open "
                "steps so the primary journal stays clean.",
            ],
        }

    def teardown(self, params) -> dict:
        for key in ("admin_1", "admin_2", "publisher_owner", "publisher_transfer_target", "editor"):
            models.Account.remove_by_id(params[key]["username"])
        for assoc in params["associate_editors"]:
            models.Account.remove_by_id(assoc)

        models.Journal.remove_by_id(params["primary_journal"]["id"])
        for j in params["spare_journals"]:
            models.Journal.remove_by_id(j["id"])

        for name in params["editor_groups"]:
            eg = models.EditorGroup.pull_by_key("name", name)
            if eg is not None:
                eg.delete()

        models.Journal.refresh()
        return self.SUCCESS
