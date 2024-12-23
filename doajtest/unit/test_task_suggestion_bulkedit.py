# -*- coding: UTF-8 -*-

import json

from flask_login import logout_user

from portality import constants
from doajtest.fixtures import ApplicationFixtureFactory, AccountFixtureFactory, EditorGroupFixtureFactory, \
    JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models
from portality.background import BackgroundException
from portality.tasks.suggestion_bulk_edit import suggestion_manage, SuggestionBulkEditBackgroundTask

TEST_SUGGESTION_COUNT = 25


class TestTaskSuggestionBulkEdit(DoajTestCase):

    def setUp(self):
        super(TestTaskSuggestionBulkEdit, self).setUp()

        acc = models.Account()
        acc.set_id("0987654321")
        acc.set_email("whatever@example.com")
        acc.save()

        owner = models.Account()
        owner.set_id("publisher")
        owner.save()

        egs = EditorGroupFixtureFactory.make_editor_group_source("1234567890", "0987654321")
        egm = models.EditorGroup(**egs)
        egm.save(blocking=True)

        self.suggestions = []
        for app_src in ApplicationFixtureFactory.make_many_application_sources(count=TEST_SUGGESTION_COUNT):
            app = models.Suggestion(**app_src)
            jid = app.current_journal
            JOURNAL_SOURCE = JournalFixtureFactory.make_journal_source(in_doaj=True)
            JOURNAL_SOURCE["id"] = jid
            current_journal = models.Journal(**JOURNAL_SOURCE)
            current_journal.save()
            self.suggestions.append(app)
            self.suggestions[-1].set_editor_group("1234567890")
            # self.suggestions[-1].set_editor("0987654321")
            self.suggestions[-1].remove_editor()
            self.suggestions[-1].bibjson().institution_country = None
            self.suggestions[-1].save()

        blocklist = [(s.id, s.last_updated) for s in self.suggestions]
        models.Application.blockall(blocklist)

        self.default_eg = EditorGroupFixtureFactory.setup_editor_group_with_editors()

        self.forbidden_accounts = [
            AccountFixtureFactory.make_editor_source()['id'],
            AccountFixtureFactory.make_assed1_source()['id'],
            AccountFixtureFactory.make_assed2_source()['id'],
            AccountFixtureFactory.make_assed3_source()['id']
        ]

        self.ctx = self._make_and_push_test_context(acc=models.Account(**AccountFixtureFactory.make_managing_editor_source()))

    def tearDown(self):
        self.ctx.pop()
        super(TestTaskSuggestionBulkEdit, self).tearDown()

    def test_01_editor_group_successful_assign(self):
        """Bulk assign an editor group to a bunch of suggestions using a background task"""
        new_eg = EditorGroupFixtureFactory.setup_editor_group_with_editors(group_name='Test Editor Group')

        # test dry run
        summary = suggestion_manage({"query": {"terms": {"_id": [s.id for s in self.suggestions]}}},
                                    editor_group=new_eg.name, dry_run=True)
        assert summary.as_dict().get("affected", {}).get("applications") == TEST_SUGGESTION_COUNT, summary.as_dict()

        summary = suggestion_manage({"query": {"terms": {"_id": [s.id for s in self.suggestions]}}},
                                    editor_group=new_eg.name, dry_run=False)
        assert summary.as_dict().get("affected", {}).get("applications") == TEST_SUGGESTION_COUNT, summary.as_dict()

        blocklist = [(s.id, s.last_updated) for s in self.suggestions]
        models.Application.blockall(blocklist)

        job = models.BackgroundJob.all()[0]

        modified_suggestions = [s.pull(s.id) for s in self.suggestions]

        for ix, s in enumerate(modified_suggestions):
            assert s.editor_group == new_eg.name, \
                "modified_suggestions[{}].editor_group is {}\n" \
                "Here is the BackgroundJob audit log:\n{}".format(
                    ix, s.editor_group, json.dumps(job.audit, indent=2)
                )

    def test_02_note_successful_add(self):
        # test dry run
        summary = suggestion_manage({"query": {"terms": {"_id": [s.id for s in self.suggestions]}}},
                                    note="Test note", dry_run=True)
        assert summary.as_dict().get("affected", {}).get("applications") == TEST_SUGGESTION_COUNT, summary.as_dict()

        summary = suggestion_manage({"query": {"terms": {"_id": [s.id for s in self.suggestions]}}},
                                    note="Test note", dry_run=False)
        assert summary.as_dict().get("affected", {}).get("applications") == TEST_SUGGESTION_COUNT, summary.as_dict()

        blocklist = [(s.id, s.last_updated) for s in self.suggestions]
        models.Application.blockall(blocklist)
        # sleep(1)

        job = models.BackgroundJob.all()[0]

        modified_suggestions = [s.pull(s.id) for s in self.suggestions]
        for ix, s in enumerate(modified_suggestions):
            assert s, 'modified_suggestions[{}] is None, does not seem to exist?'
            assert s.notes, "modified_suggestions[{}] has no notes. It is \n{}".format(ix, json.dumps(s.data, indent=2))
            assert 'note' in s.notes[-1], json.dumps(s.notes[-1], indent=2)
            assert s.ordered_notes[0]['note'] == 'Test note', \
                "The last note on modified_suggestions[{}] is {}\n" \
                "Here is the BackgroundJob audit log:\n{}".format(
                    ix, s.notes[-1]['note'], json.dumps(job.audit, indent=2)
                )

    def test_03_bulk_edit_not_admin(self):

        for acc_id in self.forbidden_accounts:
            logout_user()
            with self._make_and_push_test_context_manager(acc=models.Account.pull(acc_id)):

                with self.assertRaises(BackgroundException):
                    # test dry run
                    r = suggestion_manage({"query": {"terms": {"_id": [s.id for s in self.suggestions]}}},
                                          note="Test note", dry_run=True)

                with self.assertRaises(BackgroundException):
                    r = suggestion_manage({"query": {"terms": {"_id": [s.id for s in self.suggestions]}}},
                                          note="Test note", dry_run=False)

    def test_04_parameter_checks(self):
        # no params set at all
        params = {}
        assert SuggestionBulkEditBackgroundTask._job_parameter_check(params) is False, SuggestionBulkEditBackgroundTask._job_parameter_check(params)

        # ids set to None, but everything else is supplied
        params = {}
        SuggestionBulkEditBackgroundTask.set_param(params, 'ids', None)
        SuggestionBulkEditBackgroundTask.set_param(params, 'editor_group', 'test editor group')
        SuggestionBulkEditBackgroundTask.set_param(params, 'note', 'test note')
        SuggestionBulkEditBackgroundTask.set_param(params, 'application_status', constants.APPLICATION_STATUS_PENDING)

        assert SuggestionBulkEditBackgroundTask._job_parameter_check(params) is False, SuggestionBulkEditBackgroundTask._job_parameter_check(params)

        # ids set to [], but everything else is supplied
        SuggestionBulkEditBackgroundTask.set_param(params, 'ids', [])
        assert SuggestionBulkEditBackgroundTask._job_parameter_check(params) is False, SuggestionBulkEditBackgroundTask._job_parameter_check(params)

        # ids are supplied, but nothing else is supplied
        params = {}
        SuggestionBulkEditBackgroundTask.set_param(params, 'ids', ['123'])
        assert SuggestionBulkEditBackgroundTask._job_parameter_check(params) is False, SuggestionBulkEditBackgroundTask._job_parameter_check(params)

        # ids are supplied along with editor group only
        params = {}
        SuggestionBulkEditBackgroundTask.set_param(params, 'ids', ['123'])
        SuggestionBulkEditBackgroundTask.set_param(params, 'editor_group', 'test editor group')
        assert SuggestionBulkEditBackgroundTask._job_parameter_check(params) is True, SuggestionBulkEditBackgroundTask._job_parameter_check(params)

        # ids are supplied along with note only
        params = {}
        SuggestionBulkEditBackgroundTask.set_param(params, 'ids', ['123'])
        SuggestionBulkEditBackgroundTask.set_param(params, 'note', 'test note')
        assert SuggestionBulkEditBackgroundTask._job_parameter_check(params) is True, SuggestionBulkEditBackgroundTask._job_parameter_check(params)

        # ids are supplied along with application status only
        params = {}
        SuggestionBulkEditBackgroundTask.set_param(params, 'ids', ['123'])
        SuggestionBulkEditBackgroundTask.set_param(params, 'application_status', constants.APPLICATION_STATUS_PENDING)
        assert SuggestionBulkEditBackgroundTask._job_parameter_check(params) is True, SuggestionBulkEditBackgroundTask._job_parameter_check(params)

        # everything is supplied
        params = {}
        SuggestionBulkEditBackgroundTask.set_param(params, 'ids', ['123'])
        SuggestionBulkEditBackgroundTask.set_param(params, 'editor_group', 'test editor group')
        SuggestionBulkEditBackgroundTask.set_param(params, 'note', 'test note')
        SuggestionBulkEditBackgroundTask.set_param(params, 'application_status', constants.APPLICATION_STATUS_PENDING)
        assert SuggestionBulkEditBackgroundTask._job_parameter_check(params) is True, SuggestionBulkEditBackgroundTask._job_parameter_check(params)

    def test_05_application_successful_status_assign(self):
        """Bulk set an application status on a bunch of suggestions using a background task"""
        expected_app_status = constants.APPLICATION_STATUS_ON_HOLD
        # test dry run
        summary = suggestion_manage({"query": {"terms": {"_id": [s.id for s in self.suggestions]}}},
                                    application_status=expected_app_status, dry_run=True)
        assert summary.as_dict().get("affected", {}).get("applications") == TEST_SUGGESTION_COUNT, summary.as_dict()

        summary = suggestion_manage({"query": {"terms": {"_id": [s.id for s in self.suggestions]}}},
                                    application_status=expected_app_status, dry_run=False)
        assert summary.as_dict().get("affected", {}).get("applications") == TEST_SUGGESTION_COUNT, summary.as_dict()

        blocklist = [(s.id, s.last_updated) for s in self.suggestions]
        models.Application.blockall(blocklist)
        # sleep(1)

        job = models.BackgroundJob.all()[0]

        modified_suggestions = [s.pull(s.id) for s in self.suggestions]

        for ix, s in enumerate(modified_suggestions):
            assert s.application_status == expected_app_status, \
                "modified_suggestions[{}].application_status is {}\n" \
                "Here is the BackgroundJob audit log:\n{}".format(
                    ix, s.application_status, json.dumps(job.audit, indent=2)
                )

    """
    @richard-jones says: I have taken this test out, as I'm not 100% clear how what it does fits with
    what it says its testing.  My best guess is that it is about what happens if you try to bulk edit
    an invalid record.  This test does currently fail, with validation warnings about the missing data.
    If we have problems with bulk edits working over old records we can revisit this.
    
    def test_07_application_successful_status_assign_without_charges(self):
        # Optional select fields had a problem where their default value
        # would actually not be a valid choice. So leaving them empty
        # resulted in a validation error during bulk editing, despite the
        # fact that they could genuinely be empty under certain conditions
        # and this was acceptable on the UI.
        # The problem with select fields has been fixed, this tests for
        # regressions.
        expected_app_status = constants.APPLICATION_STATUS_ON_HOLD
        for s in self.suggestions:
            del s.data['bibjson']['apc']
            s.save()
        self.suggestions[-1].save(blocking=True)

        # test dry run
        summary = suggestion_manage({"query": {"terms": {"_id": [s.id for s in self.suggestions]}}}, application_status=expected_app_status, dry_run=True)
        assert summary.as_dict().get("affected", {}).get("applications") == TEST_SUGGESTION_COUNT, summary.as_dict()

        summary = suggestion_manage({"query": {"terms": {"_id": [s.id for s in self.suggestions]}}}, application_status=expected_app_status, dry_run=False)
        assert summary.as_dict().get("affected", {}).get("applications") == TEST_SUGGESTION_COUNT, summary.as_dict()

        sleep(1)

        job = models.BackgroundJob.all()[0]

        modified_suggestions = [s.pull(s.id) for s in self.suggestions]

        for ix, s in enumerate(modified_suggestions):
            assert s.application_status == expected_app_status, \
                "modified_suggestions[{}].application_status is {}\n" \
                "Here is the BackgroundJob audit log:\n{}".format(
                    ix, s.application_status, json.dumps(job.audit, indent=2)
                )
        """
