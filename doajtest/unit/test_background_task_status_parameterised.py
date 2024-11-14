from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from portality.models.background import BackgroundJob
from portality.lib.paths import rel2abs

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "background_task_status"),
                               "background_task_status",
                               "test_id",
                               {"test_id" : []})

import json

from doajtest.fixtures.background import save_mock_bgjob
from doajtest.helpers import DoajTestCase, apply_test_case_config, patch_config
from portality import constants
from portality.bll import DOAJ
from portality.tasks.anon_export import AnonExportBackgroundTask
from portality.tasks.journal_csv import JournalCSVBackgroundTask

background_task_status = DOAJ.backgroundTaskStatusService()

# Configures the monitoring period and the allowed number of errors in that period before a queue is marked
# as unstable
BG_MONITOR_ERRORS_CONFIG = {
    'set_in_doaj': {
        'check_sec': 3000,
        'allowed_num_err': 0
    },
    'anon_export': {
        'check_sec': 3000,
        'allowed_num_err': 0,
    },
    'journal_csv': {
        'check_sec': 3000,
        'allowed_num_err': 0
    }
}

# Configures the total number of queued items and the age of the oldest of those queued items allowed
# before the queue is marked as unstable.  This is provided by type, so we can monitor all types separately
BG_MONITOR_QUEUED_CONFIG = {
    'set_in_doaj': {
        'total': 1,
        'oldest': 3000,
    },
    'anon_export': {
        'total': 1,
        'oldest': 3000,
    },
    'journal_csv': {
        'total': 1,
        'oldest': 3000,
    }
}

BG_MONITOR_LAST_SUCCESSFULLY_RUN_CONFIG = {
    'anon_export': {
        'last_run_successful_in': 5000
    },
    'set_in_doaj': {
        'last_run_successful_in': 5000
    },
    'journal_csv': {
        'last_run_successful_in': 5000
    }
}


class TestBackgroundTaskStatus(DoajTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.org_config = patch_config(cls.app_test, {
            'HUEY_SCHEDULE': {
                JournalCSVBackgroundTask.__action__: constants.CRON_NEVER,
                AnonExportBackgroundTask.__action__: constants.CRON_NEVER,
            },
            "BG_MONITOR_ERRORS_CONFIG": BG_MONITOR_ERRORS_CONFIG,
            "BG_MONITOR_QUEUED_CONFIG": BG_MONITOR_QUEUED_CONFIG,
            "BG_MONITOR_LAST_SUCCESSFULLY_RUN_CONFIG": BG_MONITOR_LAST_SUCCESSFULLY_RUN_CONFIG
        })

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        patch_config(cls.app_test, cls.org_config)

    @parameterized.expand(load_cases)
    def test_01_background_task_status(self, name, kwargs):
        in_queue_arg = kwargs.get("in_queue")
        oldest_queued_arg = kwargs.get("oldest_queued")
        error_count_arg = kwargs.get("error_count")
        error_age_arg = kwargs.get("error_age")
        lrs_success_or_error_arg = kwargs.get("lrs_success_or_error")
        queued_arg = kwargs.get("queued")
        errors_arg = kwargs.get("errors")
        lrs_arg = kwargs.get("lrs")

        in_queue = int(in_queue_arg)
        oldest_queued = 3600 if oldest_queued_arg == "old" else 600
        error_count = int(error_count_arg)
        error_age = 600 if error_age_arg == "in_period" else 3600

        queues = [("events", "set_in_doaj"),
                  ("scheduled_long", "anon_export"),
                  ("scheduled_short", "journal_csv")]

        # set up
        ###########################################
        blocks = []
        for q, a in queues:
            if in_queue > 0:
                # create the number of jobs that should be in status "queued"
                # their ages are set to the oldest allowed age + the index number for the purposes of disambiguation
                for i in range(in_queue):
                    job = save_mock_bgjob(action=a, status="queued", created_before_sec=oldest_queued + i, is_save=True, blocking=False, queue_id=q)
                    blocks.append((job.id, job.last_updated))

            if error_count > 0:
                # create a single error job if the requested age
                job = save_mock_bgjob(action=a, status="error", created_before_sec=error_age, is_save=True, blocking=False, queue_id=q)
                blocks.append((job.id, job.last_updated))

            if lrs_success_or_error_arg != "empty":
                age = 4000
                # if there is an error that's being tested (see above), we need to make sure that the more recent job is "complete"
                # to deactivate this test, if the lrs test is supposed to be "stable".
                if error_count > 0 and lrs_success_or_error_arg == "complete":
                    age = 100
                job = save_mock_bgjob(action=a, status=lrs_success_or_error_arg, created_before_sec=age, is_save=True, blocking=False, queue_id=q)
                blocks.append((job.id, job.last_updated))

        BackgroundJob.blockall(blocks)

        # Execute
        ###########################################
        status = background_task_status.create_background_status()


        # Assert
        ###########################################

        for q, a in queues:
            assert status['queues'][q]["errors"][a]["status"] == errors_arg
            assert status['queues'][q]["queued"][a]["status"] == queued_arg
            assert status['queues'][q]["last_run_successful"][a]["status"] == lrs_arg

            if "unstable" in [errors_arg, queued_arg, lrs_arg]:
                assert status['queues'][q]["status"] == "unstable"
            else:
                assert status['queues'][q]["status"] == "stable"

            if "unstable" in [errors_arg, queued_arg, lrs_arg]:
                assert status['status'] == "unstable"
            else:
                assert status['status'] == "stable"

