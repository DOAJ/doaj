import time
import unittest
from datetime import datetime
from typing import List
from unittest.mock import MagicMock
from unittest.mock import patch

from doajtest.fixtures import JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.lib import dates
from portality.models import Journal, datalog_journal_added
from portality.models.datalog_journal_added import DatalogJournalAdded
from portality.tasks import datalog_journal_added_update
from portality.tasks.datalog_journal_added_update import DatalogJournalAddedUpdate, to_display_data, \
    to_datalog_journal_added
from portality.tasks.helpers import background_helper

input_filename = 'fake_filename'
input_worksheet_name = 'fake_worksheet_name'
input_google_key_path = 'fake_google_key_path'

testdata_datalog_list = [
    DatalogJournalAdded(title='titlec',
                        issn='1234-3000',
                        date_added='2021-01-01',
                        has_continuations=True,
                        ),
    DatalogJournalAdded(title='titleb',
                        issn='1234-2000',
                        date_added='2021-01-01',
                        has_continuations=True,
                        ),
    DatalogJournalAdded(title='titlea',
                        issn='1234-1000',
                        date_added='2020-01-01',
                        has_continuations=True,
                        ),
]


class TestDatalogJournalAddedUpdate(DoajTestCase):

    def test_sync_datalog_journal_added(self):
        journals = create_test_journals(4)
        save_and_block_last(journals[-1:])
        datalog_journal_added_update.sync_datalog_journal_added()
        assert DatalogJournalAdded.count() == 1

        save_and_block_last(journals[:-1])
        datalog_journal_added_update.sync_datalog_journal_added()
        assert DatalogJournalAdded.count() == 4

    def test_execute__normal(self):
        """
        test background job execute

        Returns
        -------

        """

        save_test_datalog()

        journals = save_test_journals(4)

        worksheet = MagicMock()
        worksheet.get_all_values.return_value = [
            ['Journal Title', ''],
            [journals[-1].bibjson().title, journals[-1].bibjson().eissn],
        ]

        # Replace the real worksheet with the mock
        with patch('portality.lib.gsheet.load_client') as mock_client:
            (mock_client.return_value
             .open.return_value
             .worksheet.return_value) = worksheet

            background_helper.execute_by_bg_task_type(DatalogJournalAddedUpdate,
                                                      filename=input_filename,
                                                      worksheet_name=input_worksheet_name,
                                                      google_key_path=input_google_key_path)

        worksheet.get_all_values.assert_called()
        new_rows_added_to_excels, row_idx, *_ = worksheet.insert_rows.call_args.args

        assert new_rows_added_to_excels == [
            to_display_data(to_datalog_journal_added(d)) for d in journals[:-1]
        ]

        assert row_idx == 2

    def test_find_new_xlsx_rows(self):
        save_test_datalog()
        values = datalog_journal_added_update.find_new_xlsx_rows(testdata_datalog_list[-1].issn)
        assert values == [
            to_display_data(d) for d in testdata_datalog_list[:-1]
        ]

        values = datalog_journal_added_update.find_new_xlsx_rows(testdata_datalog_list[1].issn)
        assert values == [
            to_display_data(d) for d in testdata_datalog_list[:1]
        ]

    def test_to_display_data(self):
        assert ['titleg', '1234-7000', '01-January-2222', 'Yes', ] == to_display_data(
            DatalogJournalAdded(title='titleg',
                                issn='1234-7000',
                                date_added='2222-01-01',
                                has_continuations=True,
                                ),
        )

        assert ['titlexxx', '1234-9999', '02-January-2222', ''] == to_display_data(
            DatalogJournalAdded(title='titlexxx',
                                issn='1234-9999',
                                date_added='2222-01-02',
                                has_continuations=False,
                                ),
        )

    def test_latest_row_index(self):
        values = [
            ['xxxx', 'ddd'],
            ['Journal Title', ''],
            ['titlea', '1234-1000'],
            ['titleb', '1234-2000'],
            ['titlec', '1234-3000'],
        ]

        assert datalog_journal_added_update.find_latest_row_index(values) == 2

        values = [
            ['Journal Title', ''],
            ['titlea', '1234-1000'],
        ]

        assert datalog_journal_added_update.find_latest_row_index(values) == 1

    def test_find_new_datalog_journals(self):
        save_test_journals(3)

        def _count_new_datalog_journals(latest_date_str):
            datalog_list = datalog_journal_added_update.find_new_datalog_journals(
                dates.parse(latest_date_str)
            )
            datalog_list = list(datalog_list)
            return len(datalog_list)

        assert _count_new_datalog_journals('2101-01-01') == 3
        assert _count_new_datalog_journals('2101-01-01T22:22:22Z') == 2
        assert _count_new_datalog_journals('2102-01-01') == 2
        assert _count_new_datalog_journals('2103-01-01') == 1
        assert _count_new_datalog_journals('2104-01-01') == 0

    def test_is_datalog_exist(self):
        save_test_datalog()
        # save_all_block_last(testdata_datalog_list)

        assert datalog_journal_added.is_issn_exists('1234-3000', '2021-01-01')
        assert datalog_journal_added.is_issn_exists('1234-1000', datetime(2020, 1, 1))
        assert not datalog_journal_added.is_issn_exists('9999-9999', datetime(2021, 1, 1))


def save_test_datalog():
    for t in testdata_datalog_list:
        t.save()

    time.sleep(2)

    DatalogJournalAdded.refresh()


def create_test_journals(n_journals):
    journals = JournalFixtureFactory.make_many_journal_sources(count=n_journals, in_doaj=True)
    journals = map(lambda d: Journal(**d), journals)
    journals = list(journals)
    assert len(journals) == n_journals
    test_dates = [
        '2103-01-01T03:00:00Z',
        '2102-01-01T02:00:00Z',
        '2101-01-01T22:22:22Z',
        '2101-01-01T01:00:00Z',
    ]
    for i, j in enumerate(journals):
        if i < len(test_dates):
            j['created_date'] = test_dates[i]
    return journals


def save_test_journals(n_journals: int) -> List[Journal]:
    journals = create_test_journals(n_journals)
    save_and_block_last(journals)
    return journals


def save_and_block_last(journals: List[Journal]):
    sub_journals, last_journal = journals[:-1], journals[-1]
    for j in sub_journals:
        j.save()
    last_journal.save(blocking=True)


if __name__ == '__main__':
    unittest.main()
    # TestDatalogJournalAddedUpdate().test_execute()
