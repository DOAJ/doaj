from contextlib import contextmanager

from doajtest.helpers import DoajTestCase, create_random_str
from portality.lib import dates
from portality.models import Account, Journal
from doajtest.fixtures import AccountFixtureFactory, JournalFixtureFactory
from flask_login import login_user, current_user

DEFAULT_FLAG_TEXT = "This is a flag."
DEFAULT_NOTE_TEXT = "This is a note."
RESOLVED_NOTE = "This used to be a flag"


def _create_note_object(author_id=None, assignee_id=None, note=DEFAULT_NOTE_TEXT, deadline=None,
                        id=create_random_str()):
    if author_id is None:
        author_id = current_user.id

    if deadline is None and assignee_id is not None:
        deadline = dates.far_in_the_future()

    return {"date": dates.today(), "note": note, "id": id, "author_id": author_id,
            "assigned_to": "" if assignee_id is None else assignee_id, "deadline": deadline}


class TestJournalLikeFlagsModel(DoajTestCase):

    def setUp(self):
        jsource = JournalFixtureFactory.make_journal_source(in_doaj=True)
        self.journal = Journal(**jsource)
        self.journal.remove_notes()
        self.journal.save()

    def tearDown(self):
        super(TestJournalLikeFlagsModel, self).tearDownClass()

    def test_flags(self):
        short_deadline = dates.days_after_now(2)
        flag = _create_note_object(author_id=create_random_str(), assignee_id=create_random_str(),
                                   deadline=short_deadline)
        flag_id = create_random_str()
        flag_far_in_the_future = _create_note_object(author_id=create_random_str(), assignee_id=create_random_str(),
                                                     note="No need to look at that till year 9999", id=flag_id)
        note = _create_note_object(author_id=create_random_str())

        self.journal.add_note(**note)
        self.journal.save(blocking=True)
        assert not self.journal.is_flagged, "This journal is not flagged yet"

        self.journal.add_note(**flag_far_in_the_future)
        self.journal.save(blocking=True)
        assert self.journal.is_flagged, "This journal is flagged now"

        assert len(self.journal.flags) == 1, "Flag not set"
        assert len(self.journal.notes) == 2, "We expect 2 notes: one with a flag and one without."
        assert len(self.journal.notes_except_flags) == 1, "Flags not correctly identified among notes."

        self.journal.add_note(**flag)
        self.journal.save(blocking=True)

        assert self.journal.is_flagged, "This journal is flagged now"

        assert len(self.journal.flags) == 2, "Flag not set"
        assert len(self.journal.notes) == 3, "We expect 3 notes: two with a flag and one without."
        assert len(self.journal.notes_except_flags) == 1, "Flags not correctly identified among notes."
        assert self.journal.ordered_notes[0]["flag"]["deadline"] ==  dates.format(short_deadline,dates.FMT_DATE_STD), "More urgent flag should be first"
        assert self.journal.ordered_notes[1]["flag"]["deadline"] == dates.far_in_the_future(out_format=dates.FMT_DATE_STD), "Less urgent flag should be second"
        assert self.journal.most_urgent_flag_deadline == dates.format(short_deadline,dates.FMT_DATE_STD), "The most urgent flag not identified correctly"

        self.journal.resolve_flag(flag_id=flag_id, updated_note=RESOLVED_NOTE)

        assert len(self.journal.flags) == 1, "Flag not set"
        assert self.journal.flags[0]["note"] != RESOLVED_NOTE
        assert len(
            self.journal.notes) == 3, "We expect 3 notes: one with a flag and 2 without, including the one that used to be a flag."
        assert len(self.journal.notes_except_flags) == 2, "Flags not correctly identified among notes."
        assert flag_id in [note["id"] for note in
                           self.journal.notes_except_flags], "Note that used to be a flag not found in notes_except_flags"


class TestJournalLikeFlagsCrossWalk(DoajTestCase):

    def setUpClass(self):
        super(TestJournalLikeFlagsCrossWalk, self).setUpClass()
        self.admin = Account.make_account(email="admin@test.com", username="admin", name="Admin", roles=["admin"])
        self.admin.set_password('admin_pass')
        self.admin.save()

        self.another_admin = Account.make_account(email="another_admin@test.com", username="another_admin",
                                                  name="Another Admin", roles=["admin"])
        self.another_admin.set_password('another_admin_pass')
        self.another_admin.save()

        esource = AccountFixtureFactory.make_editor_source()
        self.editor = Account(**esource)
        self.editor.save()

        self.another_editor = Account.make_account(email="another_editor@example.com", name="Another Editor",
                                                   roles=["editor"])
        self.another_editor.save()

        jsource = JournalFixtureFactory.make_journal_source(in_doaj=True)
        self.journal = Journal(**jsource)
        self.journal.save()

    def tearDownClass(self):
        super(TestJournalLikeFlagsCrossWalk, self).tearDownClass()

    def setUp(self):
        super(TestJournalLikeFlagsCrossWalk, self).setUp()

    def tearDown(self):
        super(TestJournalLikeFlagsCrossWalk, self).tearDown()
        self.journal.remove_notes()

    @contextmanager
    def _log_in(self, user: Account):
        with self.app_test.test_request_context():
            login_user(user)
            yield

    def setFlagWithCorrectDeadline(self):
        with self._log_in(self.admin):
            note = _create_note_object(assignee=self.another_admin, deadline=dates.days_after_now(2))
            self.journal.add_note(note)
            self.journal.save(blocking=True)
            assert len(self.journal.flags) == 1

    def setFlagWithIncorrectDeadline(self):
        # expected result: error
        pass

    def setFlagWithoutDeadline(self):
        # expected result: success
        pass

    def setFlagWithNonAdminAssignee(self):
        # expected result: error
        pass

    def setFlagWithoutAssignee(self):
        # expected result: flag saved as a regular note
        pass

    def resolveFlag(self):
        # expected result: flag saved as a note with the correct message
        pass

    def editFlagAsAdmin(self):
        # expected result: success
        pass

    def editFlagAsNonAdmin(self):
        # expected result: error
        pass
