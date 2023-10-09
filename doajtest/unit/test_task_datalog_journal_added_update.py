import time
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from doajtest.helpers import DoajTestCase
from portality.models.datalog_journal_added import DatalogJournalAdded
from portality.tasks import datalog_journal_added_update
from portality.tasks.datalog_journal_added_update import DatalogJournalAddedUpdate, to_display_data
from portality.tasks.helpers import background_helper

input_filename = 'fake_filename'
input_worksheet_name = 'fake_worksheet_name'
input_google_key_path = 'fake_google_key_path'

testdata_datalog_list = [
    DatalogJournalAdded(title='titlec',
                        issn='1234-3000',
                        date_added='2021-01-01',
                        has_seal=True,
                        has_continuations=True,
                        ),
    DatalogJournalAdded(title='titleb',
                        issn='1234-2000',
                        date_added='2021-01-01',
                        has_seal=True,
                        has_continuations=True,
                        ),
    DatalogJournalAdded(title='titlea',
                        issn='1234-1000',
                        date_added='2020-01-01',
                        has_seal=True,
                        has_continuations=True,
                        ),
]


class TestDatalogJournalAddedUpdate(DoajTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super(TestDatalogJournalAddedUpdate, cls).setUpClass()
        for t in testdata_datalog_list:
            t.save()

        time.sleep(2)
        # test_data_list[-1].save(blocking=True)
        # print('hihih')

    def test_execute__normal(self):
        """
        test background job execute

        Returns
        -------

        """
        worksheet = MagicMock()
        worksheet.get_all_values.return_value = [
            ['Journal Title', ''],
            ['titlea', '1234-1000'],
        ]

        # Replace the real worksheet with the mock
        with patch('portality.lib.gsheet.load_client') as mock_client:
            (mock_client.return_value
             .open.return_value
             .worksheet.return_value) = worksheet

            background_task = background_helper.execute_by_bg_task_type(DatalogJournalAddedUpdate,
                                                                        filename=input_filename,
                                                                        worksheet_name=input_worksheet_name,
                                                                        google_key_path=input_google_key_path)

        worksheet.get_all_values.assert_called()
        values, row_idx, *_ = worksheet.insert_rows.call_args.args

        assert values == [
            to_display_data(d) for d in testdata_datalog_list[:-1]
        ]

        assert row_idx == 2

    def test_find_new_xlsx_rows(self):
        values = datalog_journal_added_update.find_new_xlsx_rows(testdata_datalog_list[-1].issn)
        assert values == [
            to_display_data(d) for d in testdata_datalog_list[:-1]
        ]

        values = datalog_journal_added_update.find_new_xlsx_rows(testdata_datalog_list[1].issn)
        assert values == [
            to_display_data(d) for d in testdata_datalog_list[:1]
        ]

    def test_to_display_data(self):
        assert ['titleg', '1234-7000', '01-January-2222', 'Seal', 'Yes', ] == to_display_data(
            DatalogJournalAdded(title='titleg',
                                issn='1234-7000',
                                date_added='2222-01-01',
                                has_seal=True,
                                has_continuations=True,
                                ),
        )

        assert ['titlexxx', '1234-9999', '02-January-2222', '', ''] == to_display_data(
            DatalogJournalAdded(title='titlexxx',
                                issn='1234-9999',
                                date_added='2222-01-02',
                                has_seal=False,
                                has_continuations=False,
                                ),
        )

        # print('-------------')
        # print(values)

        # worksheet.get_all_values.assert_not_called()
        #     # Now, when you use the worksheet object, it will behave like the mock
        #     result = worksheet.some_method()
        #
        # # Assertions or further testing using the mock
        # assert result == "Mocked result"
        # worksheet.some_method.assert_called_once_with()

        # run execute

        # # prepare test data
        # for _ in range(3):
        #     BackgroundJob().save()
        # for _ in range(2):
        #     Account().save(blocking=True)

        # new_background_jobs = list(BackgroundJob.scroll())
        # new_accounts = list(Account.scroll())

        # # run execute
        # background_task = background_helper.execute_by_bg_task_type(AnonExportBackgroundTask)

    #     # assert audit messages
    #     self.assertIn('audit', background_task.background_job.data)
    #     msgs = {l.get('message') for l in background_task.background_job.data['audit']}
    #     self.assertTrue(any('Compressing temporary file' in m for m in msgs))
    #     self.assertTrue(any('account.bulk.1' in m for m in msgs))
    #
    #     main_store = StoreLocal(None)
    #     container_id = self.app_test.config.get("STORE_ANON_DATA_CONTAINER")
    #     target_names = main_store.list(container_id)
    #
    #     # must have some file in main store
    #     self.assertGreater(len(target_names), 0)
    #
    #     for target_name in target_names:
    #
    #         # load data from store
    #         _target_path = Path(main_store.get(container_id, target_name).name)
    #         data_str = gzip.decompress(_target_path.read_bytes()).decode(errors='ignore')
    #         if data_str:
    #             rows = data_str.strip().split('\n')
    #
    #             # Filter out the index: directives, leaving the actual record data
    #             json_rows = list(filter(lambda j: len(json.loads(j).keys()) > 1, rows))
    #
    #             if target_name.startswith('background_job'):
    #                 test_data_list = new_background_jobs
    #             elif target_name.startswith('account'):
    #                 test_data_list = new_accounts
    #             else:
    #                 print(f'unexpected data dump for target_name[{target_name}]')
    #                 continue
    #
    #             print(f'number of rows have been saved to store: [{target_name}] {len(json_rows)}')
    #             self.assertEqual(len(json_rows), len(test_data_list))
    #             self.assertIn(test_data_list[0].id, [json.loads(j)['id'] for j in json_rows])
    #         else:
    #             print(f'empty archive {target_name}')
    #
    # def test_prepare__queue_id(self):
    #     bgtask_tester.test_queue_id_assigned(AnonExportBackgroundTask)


if __name__ == '__main__':
    unittest.main()
    # TestDatalogJournalAddedUpdate().test_execute()
