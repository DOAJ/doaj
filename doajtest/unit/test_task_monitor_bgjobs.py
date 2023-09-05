from unittest.mock import patch

from doajtest.helpers import DoajTestCase
from portality import models
from portality.background import BackgroundApi
from portality.core import app
from portality.tasks import monitor_bgjobs


class TestMonitorBgjobsBackgroundTask(DoajTestCase):
    store_impl = None

    @staticmethod
    def execute_task_a():
        username = app.config.get("SYSTEM_USERNAME")
        job = monitor_bgjobs.MonitorBgjobsBackgroundTask.prepare(
            username, to_address_list=['to@alskdj.com'],
            from_address='from@akdjaksj.com', )
        task = monitor_bgjobs.MonitorBgjobsBackgroundTask(job)
        BackgroundApi.execute(task)

    @patch.object(monitor_bgjobs.app_email, 'send_mail')
    def test_run__mail_sent(self, mock_send_mail):
        assert models.BackgroundJob.count() == 0

        # create target  background_job records
        target_jobs = []
        for _ in range(2):
            bg = models.BackgroundJob()
            bg.fail()
            bg.user = 'system'
            bg.action = 'harvest'
            bg.save()
            target_jobs.append(bg)

        # create not related background_job
        bg = models.BackgroundJob()
        bg.save(blocking=True)

        # execute
        self.execute_task_a()

        # check result
        self.assertTrue(mock_send_mail.called)
        self.assertTrue(mock_send_mail.call_args)
        self.assertIn(
            target_jobs[0].id,
            mock_send_mail.call_args.kwargs.get('msg_body', '')
        )

    @patch.object(monitor_bgjobs.app_email, 'send_mail')
    def test_run__no_mail(self, mock_send_mail):
        assert models.BackgroundJob.count() == 0

        # create target  background_job records
        models.BackgroundJob.count()

        # create not related background_job
        bg = models.BackgroundJob()
        bg.save(blocking=True)

        # execute
        self.execute_task_a()

        # check result
        self.assertFalse(mock_send_mail.called)
