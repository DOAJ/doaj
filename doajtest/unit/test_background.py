import time

from doajtest.fixtures import BackgroundFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models
from portality.background import BackgroundApi
from portality.constants import BgjobOutcomeStatus
from portality.models.background import BackgroundJobQueryBuilder


class TestBackground(DoajTestCase):

    def setUp(self):
        super(TestBackground, self).setUp()

    def tearDown(self):
        super(TestBackground, self).tearDown()

    def test_01_with_user_success(self):
        acc = models.Account()
        acc.set_id("testuser")
        acc.save(blocking=True)

        task = BackgroundFixtureFactory.get_task(acc.id)
        BackgroundApi.execute(task)
        time.sleep(1)

        job = task.background_job
        assert job.status == "complete"
        assert job.outcome_status == BgjobOutcomeStatus.Success
        assert len(job.audit) > 2   # there will be some messages, no need to be too specific

    def test_02_with_user_cleanup_fail(self):
        acc = models.Account()
        acc.set_id("testuser")
        acc.save(blocking=True)

        task = BackgroundFixtureFactory.get_task(acc.id, cleanup_fail=True)
        BackgroundApi.execute(task)
        time.sleep(1)

        job = task.background_job
        assert job.status == "error"
        assert job.outcome_status == BgjobOutcomeStatus.Fail
        assert len(job.audit) > 2  # there will be some messages, no need to be too specific

    def test_03_with_user_run_fail(self):
        acc = models.Account()
        acc.set_id("testuser")
        acc.save(blocking=True)

        task = BackgroundFixtureFactory.get_task(acc.id, run_fail=True)
        BackgroundApi.execute(task)
        time.sleep(1)

        job = task.background_job
        assert job.status == "error"
        assert len(job.audit) > 2  # there will be some messages, no need to be too specific
        assert job.outcome_status == BgjobOutcomeStatus.Fail

    def test_04_no_user_success(self):
        task = BackgroundFixtureFactory.get_task()
        BackgroundApi.execute(task)
        time.sleep(1)

        job = task.background_job
        assert job.status == "complete"
        assert len(job.audit) > 2  # there will be some messages, no need to be too specific
        assert job.outcome_status == BgjobOutcomeStatus.Success

    def test_05_no_user_cleanup_fail(self):
        task = BackgroundFixtureFactory.get_task(cleanup_fail=True)
        BackgroundApi.execute(task)
        time.sleep(1)

        job = task.background_job
        assert job.status == "error"
        assert len(job.audit) > 2  # there will be some messages, no need to be too specific
        assert job.outcome_status == BgjobOutcomeStatus.Fail

    def test_06_no_user_run_fail(self):
        task = BackgroundFixtureFactory.get_task(run_fail=True)
        BackgroundApi.execute(task)
        time.sleep(1)

        job = task.background_job
        assert job.status == "error"
        assert len(job.audit) > 2  # there will be some messages, no need to be too specific
        assert job.outcome_status == BgjobOutcomeStatus.Fail


class TestBackgroundJobQueryBuilder(DoajTestCase):

    def test_build_query_dict__a(self):
        query_dict = (BackgroundJobQueryBuilder()
                      .status_includes('some status')
                      .build_query_dict())
        expected_dict = {
            'query': {
                'bool': {
                    'must': [
                        {'terms': {'status.exact': ['some status']}}
                    ]
                }
            }
        }
        assert query_dict == expected_dict

    def test_build_query__b(self):
        status = ['status a', 'status b']
        query_dict = (BackgroundJobQueryBuilder()
                      .status_includes(status)
                      .size(99)
                      .order_by('field a', 'desc')
                      .action('action a')
                      .build_query_dict())
        expected_dict = {
            'query': {
                'bool': {
                    'must': [
                        {'terms': {'status.exact': status}},
                        {'term': {'action.exact': 'action a'}},
                    ]
                },
            },
            'size': 99,
            'sort': [{'field a': {'order': 'desc'}}]

        }
        assert query_dict == expected_dict
