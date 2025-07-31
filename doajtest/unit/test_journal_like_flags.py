from contextlib import contextmanager
from copy import deepcopy

from multidict import MultiDict

from doajtest.helpers import DoajTestCase, create_random_str
from doajtest.unit.application_processors.test_application_processor_emails import UPDATE_REQUEST_SOURCE_TEST_1
from portality import constants
from portality.crosswalks.application_form import ApplicationFormXWalk
from portality.forms.application_forms import ApplicationFormFactory
from portality.lib import dates
from portality.models import Account, Journal, Application
from doajtest.fixtures import AccountFixtureFactory, JournalFixtureFactory, ApplicationFixtureFactory
from flask_login import login_user, current_user

from portality.ui.messages import Messages

DEFAULT_FLAG_TEXT = "This is a flag."
DEFAULT_NOTE_TEXT = "This is a note."
RESOLVED_NOTE = "This used to be a flag"

short_deadline = dates.format(dates.days_after_now(2), dates.FMT_DATE_STD)

APPLICATION_FORM = ApplicationFixtureFactory.make_application_form
APPLICATION_FORMINFO = ApplicationFixtureFactory.make_application_form_info()
APPLICATION_SOURCE = ApplicationFixtureFactory.make_update_request_source()


def _create_note_object(author_id=None, assignee_id=None, note=DEFAULT_NOTE_TEXT, deadline=None,
                        id=create_random_str()):
    if author_id is None:
        author_id = current_user.id

    if deadline is None and assignee_id is not None:
        deadline = dates.far_in_the_future()

    return {"date": dates.today(), "note": note, "id": id, "author_id": author_id,
            "assigned_to": "" if assignee_id is None else assignee_id, "deadline": deadline}

def _add_flag_to_form_source(form, flag):

    flag_form_obj = {
        "flag_created_date": dates.today(),
        "deadline": flag["deadline"],
        "flag_assignee": flag["assigned_to"],
        "flag_setter": flag["author_id"],
        "flag_note_id": flag["id"],
        "flag_note": flag["note"]
    }

    form["flags"] = [flag_form_obj]

    return form

class TestJournalLikeFlagsModel(DoajTestCase):

    def setUp(self):
        super(TestJournalLikeFlagsModel, self).setUpClass()
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
        self.journal.remove_notes()
        self.journal.save()

        self.pc = ApplicationFormFactory.context("admin")

    def tearDown(self):
        super(TestJournalLikeFlagsModel, self).tearDown()
        self.journal.remove_notes()
        self.journal.save()

    @contextmanager
    def _log_in(self, user: Account):
        with self.app_test.test_request_context():
            login_user(user)
            yield

    def test_flags_model(self):
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
        assert self.journal.ordered_notes[0]["flag"]["deadline"] ==  short_deadline, "More urgent flag should be first"
        assert self.journal.ordered_notes[1]["flag"]["deadline"] == dates.far_in_the_future(out_format=dates.FMT_DATE_STD), "Less urgent flag should be second"
        assert self.journal.most_urgent_flag_deadline == short_deadline, "The most urgent flag not identified correctly"

        self.journal.resolve_flag(flag_id=flag_id, updated_note=RESOLVED_NOTE)

        assert len(self.journal.flags) == 1, "Flag not set"
        assert self.journal.flags[0]["note"] != RESOLVED_NOTE
        assert len(
            self.journal.notes) == 3, "We expect 3 notes: one with a flag and 2 without, including the one that used to be a flag."
        assert len(self.journal.notes_except_flags) == 2, "Flags not correctly identified among notes."
        assert flag_id in [note["id"] for note in
                           self.journal.notes_except_flags], "Note that used to be a flag not found in notes_except_flags"


    def test_setFlagWithCorrectDeadline(self):
        with self._log_in(self.admin):
            fsource = ApplicationFixtureFactory.make_application_form(flag=True, assignee=self.admin.id, deadline=short_deadline, note="Flag with a correct deadline")
            form = self.pc.wtform(MultiDict(fsource))
            app = ApplicationFormXWalk.form2obj(form)
            app.save()
            assert app.is_flagged == True, "Flag not set"
            assert len(app.flags) == 1
            f = app.flags[0]
            assert f["flag"]["deadline"] == short_deadline
            assert f["author_id"] == current_user.id

    def setFlagWithIncorrectDeadline(self):
        with self._log_in(self.admin):
            fsource = ApplicationFixtureFactory.make_application_form(flag=True, assignee=self.admin.id,
                                                                      note="Flag without deadline")
            form = self.pc.wtform(MultiDict(fsource))
            with self.assertRaises(ValueError):
                app = ApplicationFormXWalk.form2obj(form)

    def test_setFlagWithoutDeadline(self):
        ftext = "Flag without deadline"
        with self._log_in(self.admin):
            fsource = ApplicationFixtureFactory.make_application_form(flag=True, assignee=self.admin.id,
                                                                      note=ftext)
            form = self.pc.wtform(MultiDict(fsource))
            app = ApplicationFormXWalk.form2obj(form)
            app.save()
            assert app.is_flagged == True, "Flag not set"
            assert len(app.flags) == 1
            f = app.flags[0]
            assert f["flag"]["deadline"] == dates.far_in_the_future(out_format=dates.FMT_DATE_STD)

    def test_setFlagWithoutAssignee(self):
        ftext = "Flag without an assignee"
        with self._log_in(self.admin):
            fsource = ApplicationFixtureFactory.make_application_form(flag=True, note=ftext, deadline=short_deadline)
            form = self.pc.wtform(MultiDict(fsource))
            app = ApplicationFormXWalk.form2obj(form)
            app.save()
            assert app.is_flagged == False, "Flag without an assignee should be automatically converted to a note"
            assert ftext in [note["note"] for note in app.notes]

    def test_resolveFlag(self):
        ftext = "Resolved flag"
        with self._log_in(self.admin):
            ready_application = Application(**UPDATE_REQUEST_SOURCE_TEST_1)
            ready_application.set_application_status(constants.APPLICATION_STATUS_READY)
            ready_application.set_current_journal(self.journal.id)
            ready_application.remove_notes()

            # Construct an application form
            fc = ApplicationFormFactory.context("admin")
            processor = fc.processor(source=ready_application)
            processor.form.flags.entries.clear()
            # Make changes to the application status via the form
            processor.form.flags.append_entry(
                {
                    "flag_note_id": create_random_str(),
                    "flag_deadline": "",
                    "flag_assignee": self.another_admin.id,
                    "flag_note": ftext,
                    "flag_resolved": "true"
                })

            # Emails are sent during the finalise stage, and requires the app context to build URLs
            processor.finalise(current_user)
            app = ApplicationFormXWalk.form2obj(processor.form)
            app.save(blocking=True)
            assert app.is_flagged == False, "Flag hasn't been resolved"
            msg = Messages.FORMS__APPLICATION_FLAG__RESOLVED.format(
                date=dates.today(),
                username=current_user.id,
                note=ftext
            )
            assert msg in [note["note"] for note in app.notes]


    def editFlagAsAdmin(self):
        # expected result: success
        pass

    def editFlagAsNonAdmin(self):
        # expected result: error
        pass
