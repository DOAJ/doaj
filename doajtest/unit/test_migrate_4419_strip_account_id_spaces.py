import importlib
from unittest.mock import patch

from doajtest.fixtures.v2.journals import JournalFixtureFactory
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models
from portality.bll import DOAJ
from portality.core import es_connection as ES

mig = importlib.import_module("portality.migrate.4419_strip_account_id_spaces.strip_account_id_spaces")


class TestStripAccountIdSpaces(DoajTestCase):

    def setUp(self):
        super().setUp()
        self.bob = self._account("bob ", "bob@example.com", ["publisher", "api"])
        self._account("alice", "alice@example.com")
        self._account("carol", "carol@example.com")
        self._account("carol ", "carol2@example.com")

        j = models.Journal(**JournalFixtureFactory.make_journal_source())
        j.set_owner("bob ")
        j.set_editor("carol ")
        j.save(blocking=True)
        self.journal_id = j.id

        a = models.Application(**ApplicationFixtureFactory.make_application_source())
        a.set_owner("alice")
        a.set_editor("bob ")
        a.save(blocking=True)
        self.application_id = a.id

        eg = models.EditorGroup()
        eg.set_name("Group")
        eg.set_editor("alice")
        eg.set_associates(["bob ", "alice"])
        eg.save(blocking=True)
        self.eg_id = eg.id

        # bob only in a note and a flag: journal has no dynamic template, so these get .keyword, not .exact
        j2 = models.Journal(**JournalFixtureFactory.make_journal_source())
        j2.set_id(j2.makeid())
        j2.set_owner("alice")
        j2.add_note("checked", author_id="bob ")
        j2.add_note("please review", author_id="alice", assigned_to="bob ")
        j2.save(blocking=True)
        self.journal2_id = j2.id

        # pre-notes-index journal: author_id only in the legacy admin.notes, which ES maps itself (.keyword, no .exact)
        legacy = JournalFixtureFactory.make_journal_source()
        legacy["id"] = models.Journal.makeid()
        legacy["admin"]["owner"] = "alice"
        legacy["admin"]["notes"] = [{"id": "n1", "note": "old", "date": "2020-01-01T00:00:00Z", "author_id": "bob "}]
        models.Journal.bulk([legacy], refresh=True)
        self.journal3_id = legacy["id"]

    def _account(self, username, email, roles=None):
        acc = models.Account.make_account(email, username=username, roles=roles)
        acc.set_password("password123")
        acc.save(blocking=True)
        return acc

    def test_01_dry_run_changes_nothing(self):
        summary = mig.run(migrate=False)
        assert summary == {"renamed": ["bob "], "clashes": ["carol "], "failed": []}
        assert models.Account.pull("bob ") is not None
        assert models.Account.pull("bob") is None
        assert models.Journal.pull(self.journal_id).owner == "bob "

    def test_02_migrate_renames_and_updates_linked_records(self):
        summary = mig.run(migrate=True)
        assert summary == {"renamed": ["bob "], "clashes": ["carol "], "failed": []}

        assert models.Account.pull("bob ") is None
        bob = models.Account.pull("bob")
        assert bob.email == "bob@example.com"
        assert bob.has_role("publisher") and bob.has_role("api")
        assert bob.check_password("password123")
        assert bob.data["api_key"] == self.bob.data["api_key"]

        assert models.Journal.pull(self.journal_id).owner == "bob"
        j2 = models.Journal.pull(self.journal2_id)
        assert j2.owner == "alice"
        assert sorted(n.get("author_id") for n in j2.notes) == ["alice", "bob"]
        assert j2.data["admin"]["flag"]["assigned_to"] == "bob"
        legacy = ES.get(index=models.Journal.index_name(), id=self.journal3_id)["_source"]["admin"]["notes"]
        assert legacy[0]["author_id"] == "bob"
        app = models.Application.pull(self.application_id)
        assert app.editor == "bob" and app.owner == "alice"
        assert models.EditorGroup.pull(self.eg_id).associates == ["bob", "alice"]

        # nothing left pointing at the old username, so a rerun is a no-op
        assert list(mig.find_references("bob ")) == []
        models.Account.refresh()
        assert mig.run(migrate=True)["renamed"] == []

    def test_03_clash_skipped_untouched(self):
        mig.run(migrate=True)
        assert models.Account.pull("carol ").email == "carol2@example.com"
        assert models.Account.pull("carol").email == "carol@example.com"
        assert models.Journal.pull(self.journal_id).editor == "carol "

    def test_04_rerun_after_partial_failure(self):
        with patch.object(mig, "rewrite_references", return_value=1):
            assert mig.run(migrate=True)["failed"] == ["bob "]
        # copy made, old kept because the linked records were not done
        assert models.Account.pull("bob") is not None
        assert models.Account.pull("bob ") is not None

        # the copy from the first run is recognised, not treated as a clash
        assert mig.run(migrate=True)["renamed"] == ["bob "]
        assert models.Account.pull("bob ") is None
        assert models.Journal.pull(self.journal_id).owner == "bob"

    def test_05_login_lookup_before_and_after(self):
        svc = DOAJ.accountService()
        with patch.dict(self.app_test.config, {"LOGIN_VIA_ACCOUNT_ID": True}):
            # before: typed with or without the space reaches the right account; clash keeps its own account
            assert svc.resolve_user("bob ").id == "bob "
            assert svc.resolve_user("carol ").id == "carol "
            assert svc.resolve_user("  ") is None
            mig.run(migrate=True)
            # after: the old spelling still logs in
            assert svc.resolve_user("bob ").id == "bob"
            assert svc.resolve_user("bob").id == "bob"

    def test_06_user_experience_through_login_view(self):
        from portality.app import app
        client = app.test_client()
        login = dict(user="bob ", password="password123", action="password_login")
        with patch.dict(self.app_test.config, {"LOGIN_VIA_ACCOUNT_ID": True}):
            assert b"Welcome back" in client.post("/account/login", data=login, follow_redirects=True).data
            assert client.get("/account/bob%20").status_code == 200

            mig.run(migrate=True)

            # same browser session, next click: logged out once, the same page any anonymous visitor gets (no 500)
            assert client.get("/account/bob").status_code == app.test_client().get("/account/bob").status_code == 401

            # logs back in with the spelling they always used
            assert b"Welcome back" in client.post("/account/login", data=login, follow_redirects=True).data
            assert client.get("/account/bob").status_code == 200
