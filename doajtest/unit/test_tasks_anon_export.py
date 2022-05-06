import gzip
import json
from pathlib import Path

from doajtest.helpers import DoajTestCase
from portality import background_helper
from portality.core import app
from portality.models import BackgroundJob, Account
from portality.scripts import anon_export
from portality.store import StoreFactory, StoreLocal
from portality.tasks.anon_export import AnonExportBackgroundTask


class TestAnonExport(DoajTestCase):
    store_impl = None

    @classmethod
    def setUpClass(cls) -> None:
        super(TestAnonExport, cls).setUpClass()
        cls.store_impl = app.config["STORE_IMPL"]
        app.config["STORE_IMPL"] = "portality.store.StoreLocal"

    @classmethod
    def tearDownClass(cls) -> None:
        super(TestAnonExport, cls).tearDownClass()
        app.config["STORE_IMPL"] = cls.store_impl

    def setUp(self):
        super(TestAnonExport, self).setUp()
        self.container_id = app.config.get("STORE_CACHE_CONTAINER")
        self.mainStore = StoreFactory.get("cache")

    def tearDown(self):
        super(TestAnonExport, self).tearDown()
        self.mainStore.delete_container(self.container_id)

    # @unittest.skip
    def test_execute(self):

        # prepare test data
        for _ in range(3):
            BackgroundJob().save(blocking=True)
        new_background_jobs = list(BackgroundJob.scroll())

        for _ in range(2):
            Account().save(blocking=True)
        new_accounts = list(Account.scroll())

        # run execute
        background_helper.execute_by_bg_task_type(AnonExportBackgroundTask)

        main_store: StoreLocal = anon_export.mainStore
        container_id = anon_export.container
        target_names = main_store.list(container_id)

        # must have some file in main store
        self.assertGreater(len(target_names), 0)

        for target_name in target_names:

            # load data from store
            _target_path = Path(main_store.get(container_id, target_name).name)
            data_str = gzip.decompress(_target_path.read_bytes()).decode(errors='ignore')
            rows = data_str.strip().split('\n')
            json_rows = (json.loads(s) for s in rows)
            json_rows = (j for j in json_rows if 'index' not in j.keys())
            json_rows = list(json_rows)

            if target_name.startswith('background_job'):
                test_data_list = new_background_jobs
            elif target_name.startswith('account'):
                test_data_list = new_accounts
            else:
                print(f'unknown target_name[{target_name}]')
                continue

            print(f'number of rows have been saved to store: [{target_name}] {len(json_rows)}')
            self.assertEqual(len(json_rows), len(test_data_list))
            self.assertIn(test_data_list[0].id, [j['id'] for j in json_rows])
