# -*- coding: UTF-8 -*-

from time import sleep
import json

from doajtest.helpers import DoajTestCase

from flask_login import logout_user

from portality import models
from portality.background import BackgroundException
from portality.tasks.suggestion_bulk_edit import suggestion_manage

from doajtest.fixtures import ApplicationFixtureFactory, AccountFixtureFactory, EditorGroupFixtureFactory

TEST_SUGGESTION_COUNT = 25


class TestTaskSuggestionBulkEdit(DoajTestCase):

    def setUp(self):
        super(TestTaskSuggestionBulkEdit, self).setUp()

        self.suggestions = []
        for app_src in ApplicationFixtureFactory.make_many_application_sources(count=TEST_SUGGESTION_COUNT):
            self.suggestions.append(models.Suggestion(**app_src))
            self.suggestions[-1].save()

        self.default_eg = EditorGroupFixtureFactory.setup_editor_group_with_editors()

        self.forbidden_accounts = [
            AccountFixtureFactory.make_editor_source()['id'],
            AccountFixtureFactory.make_assed1_source()['id'],
            AccountFixtureFactory.make_assed2_source()['id'],
            AccountFixtureFactory.make_assed3_source()['id']
        ]

        self._make_and_push_test_context(acc=models.Account(**AccountFixtureFactory.make_managing_editor_source()))

    def tearDown(self):
        super(TestTaskSuggestionBulkEdit, self).tearDown()

    def test_01_editor_group_successful_assign(self):
        """Bulk assign an editor group to a bunch of suggestions using a background task"""
        new_eg = EditorGroupFixtureFactory.setup_editor_group_with_editors(group_name='Test Editor Group')

        # test dry run
        r = suggestion_manage({"query": {"terms": {"_id": [s.id for s in self.suggestions]}}}, editor_group=new_eg.name, dry_run=True)
        assert r == TEST_SUGGESTION_COUNT, r

        r = suggestion_manage({"query": {"terms": {"_id": [s.id for s in self.suggestions]}}}, editor_group=new_eg.name, dry_run=False)
        assert r == TEST_SUGGESTION_COUNT, r

        sleep(1)

        job = models.BackgroundJob.all()[0]

        modified_suggestions = [s.pull(s.id) for s in self.suggestions]

        for ix, s in enumerate(modified_suggestions):
            assert s.editor_group == new_eg.name, \
                "modified_suggestions[{}].editor_group is {}" \
                "\nHere is the BackgroundJob audit log:\n{}"\
                    .format(ix, s.editor_group, json.dumps(job.audit, indent=2))

    def test_02_note_successful_add(self):
        # test dry run
        r = suggestion_manage({"query": {"terms": {"_id": [s.id for s in self.suggestions]}}}, note="Test note", dry_run=True)
        assert r == TEST_SUGGESTION_COUNT, r

        r = suggestion_manage({"query": {"terms": {"_id": [s.id for s in self.suggestions]}}}, note="Test note", dry_run=False)
        assert r == TEST_SUGGESTION_COUNT, r

        sleep(1)

        job = models.BackgroundJob.all()[0]

        modified_suggestions = [s.pull(s.id) for s in self.suggestions]
        for ix, s in enumerate(modified_suggestions):
            assert s, 'modified_suggestions[{}] is None, does not seem to exist?'
            assert s.notes, "modified_suggestions[{}] has no notes. It is \n{}".format(ix, json.dumps(s.data, indent=2))
            assert 'note' in s.notes[-1], json.dumps(s.notes[-1], indent=2)
            assert s.notes[-1]['note'] == 'Test note', "The last note on modified_suggestions[{}] is {}\nHere is the BackgroundJob audit log:\n{}".format(ix, s.notes[-1]['note'], json.dumps(job.audit, indent=2))

    def test_03_bulk_edit_not_admin(self):

        for acc_id in self.forbidden_accounts:
            logout_user()
            self._make_and_push_test_context(acc=models.Account.pull(acc_id))

            with self.assertRaises(BackgroundException):
                # test dry run
                r = suggestion_manage({"query": {"terms": {"_id": [s.id for s in self.suggestions]}}}, note="Test note", dry_run=True)

            with self.assertRaises(BackgroundException):
                r = suggestion_manage({"query": {"terms": {"_id": [s.id for s in self.suggestions]}}}, note="Test note", dry_run=False)
