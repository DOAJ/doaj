import gzip
import json
from pathlib import Path

from doajtest.helpers import DoajTestCase, StoreLocalPatcher
from doajtest.unit_tester import bgtask_tester
from portality.models import BackgroundJob, Account
from portality.store import StoreLocal
from portality.tasks.anon_export import AnonExportBackgroundTask
from portality.tasks.helpers import background_helper


class TestAnonExport(DoajTestCase):

    def setUp(self):
        super().setUp()
        self.store_local_patcher = StoreLocalPatcher()
        self.store_local_patcher.setUp(self.app_test)

    def tearDown(self):
        super().tearDown()
        self.store_local_patcher.tearDown(self.app_test)

    def test_execute(self):

        # prepare test data
        BackgroundJob.destroy_index()
        Account.destroy_index()
        BackgroundJob.save_all((BackgroundJob() for _ in range(3)), blocking=True)
        Account.save_all((Account() for _ in range(2)), blocking=True)
        BackgroundJob.refresh()
        Account.refresh()

        new_background_jobs = list(BackgroundJob.scroll())
        new_accounts = list(Account.scroll())

        # run execute
        background_task = background_helper.execute_by_bg_task_type(AnonExportBackgroundTask)

        # assert audit messages
        self.assertIn('audit', background_task.background_job.data)
        msgs = {l.get('message') for l in background_task.background_job.data['audit']}
        self.assertTrue(any('Compressing temporary file' in m for m in msgs))
        self.assertTrue(any('account.bulk.1' in m for m in msgs))

        main_store = StoreLocal(None)
        container_id = self.app_test.config.get("STORE_ANON_DATA_CONTAINER")
        target_names = main_store.list(container_id)

        # must have some file in main store
        self.assertGreater(len(target_names), 0)

        for target_name in target_names:

            # load data from store
            _target_path = Path(main_store.get(container_id, target_name).name)
            data_str = gzip.decompress(_target_path.read_bytes()).decode(errors='ignore')
            if data_str:
                rows = data_str.strip().split('\n')

                # Filter out the index: directives, leaving the actual record data
                json_rows = (json.loads(j) for j in rows)
                json_rows = filter(lambda j: len(j.keys()) > 1, json_rows)
                # drop additional background job record for AnonExportBackgroundTask execute
                json_rows = (j for j in json_rows if (
                        j.get('action') != 'anon_export' and
                        j.get('status') != 'processing'
                ))
                json_rows = list(json_rows)

                if target_name.startswith('background_job'):
                    test_data_list = new_background_jobs
                elif target_name.startswith('account'):
                    test_data_list = new_accounts
                else:
                    print(f'unexpected data dump for target_name[{target_name}]')
                    continue

                print(f'number of rows have been saved to store: [{target_name}] {len(json_rows)}')
                self.assertEqual(len(json_rows), len(test_data_list))
                self.assertIn(test_data_list[0].id, [j['id'] for j in json_rows])
            else:
                print(f'empty archive {target_name}')

    def test_prepare__queue_id(self):
        bgtask_tester.test_queue_id_assigned(AnonExportBackgroundTask)
