from doajtest.helpers import DoajTestCase
from doajtest.fixtures import BackgroundFixtureFactory

from portality import models
from portality.background import BackgroundApi

import time

class TestBackground(DoajTestCase):

    def setUp(self):
        super(TestBackground, self).setUp()

    def tearDown(self):
        super(TestBackground, self).tearDown()

    def test_01_with_user_success(self):
        acc = models.Account()
        acc.set_id("testuser")
        acc.save()
        time.sleep(2)

        task = BackgroundFixtureFactory.get_task(acc.id)
        BackgroundApi.execute(task)
        time.sleep(2)

        job = task.background_job
        assert job.status == "complete"
        assert len(job.audit) > 2   # there will be some messages, no need to be too specific

    def test_02_with_user_cleanup_fail(self):
        acc = models.Account()
        acc.set_id("testuser")
        acc.save()
        time.sleep(2)

        task = BackgroundFixtureFactory.get_task(acc.id, cleanup_fail=True)
        BackgroundApi.execute(task)
        time.sleep(2)

        job = task.background_job
        assert job.status == "error"
        assert len(job.audit) > 2   # there will be some messages, no need to be too specific

    def test_03_with_user_run_fail(self):
        acc = models.Account()
        acc.set_id("testuser")
        acc.save()
        time.sleep(2)

        task = BackgroundFixtureFactory.get_task(acc.id, run_fail=True)
        BackgroundApi.execute(task)
        time.sleep(2)

        job = task.background_job
        assert job.status == "error"
        assert len(job.audit) > 2   # there will be some messages, no need to be too specific

    def test_04_no_user_success(self):
        task = BackgroundFixtureFactory.get_task()
        BackgroundApi.execute(task)
        time.sleep(2)

        job = task.background_job
        assert job.status == "complete"
        assert len(job.audit) > 2   # there will be some messages, no need to be too specific

    def test_05_no_user_cleanup_fail(self):
        task = BackgroundFixtureFactory.get_task(cleanup_fail=True)
        BackgroundApi.execute(task)
        time.sleep(2)

        job = task.background_job
        assert job.status == "error"
        assert len(job.audit) > 2   # there will be some messages, no need to be too specific

    def test_06_no_user_run_fail(self):
        task = BackgroundFixtureFactory.get_task(run_fail=True)
        BackgroundApi.execute(task)
        time.sleep(2)

        job = task.background_job
        assert job.status == "error"
        assert len(job.audit) > 2   # there will be some messages, no need to be too specific