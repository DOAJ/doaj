import datetime
import itertools
import logging
import re
import time
from typing import Callable, NoReturn, List, Iterable

import gspread

from portality import dao, regex
from portality.background import BackgroundTask
from portality.core import app
from portality.lib import dates, gsheet
from portality.models import Journal
from portality.models.datalog_journal_added import DatalogJournalAdded
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import main_queue

log = logging.getLogger(__name__)


class NewDatalogJournalQuery:
    def __init__(self, latest_date):
        self.latest_date = latest_date

    def query(self):
        return {
            'query': {
                'bool': {
                    'should': [{
                        'range': {
                            "created_date": {"gt": dates.format(self.latest_date)},
                        }
                    }]
                },
            },
            'sort': [
                {'created_date': {'order': 'desc'}}
            ]
        }


class LatestDatalogJournalQuery:
    def __init__(self):
        pass

    def query(self):
        return {
            'sort': [
                {'date_added': {'order': 'desc'}}
            ]
        }


def find_new_datalog_journals(latest_date: datetime.datetime) -> Iterable[DatalogJournalAdded]:
    records = Journal.iterate(NewDatalogJournalQuery(latest_date).query())
    return (to_datalog_journal_added(j) for j in records)


def to_datalog_journal_added(journal: Journal) -> DatalogJournalAdded:
    bibjson = journal.bibjson()
    title = bibjson.title
    issn = bibjson.eissn or bibjson.pissn
    has_seal = journal.has_seal()
    try:
        has_continuations = any([journal.get_future_continuations() + journal.get_past_continuations()])
    except RecursionError:
        has_continuations = False

    record = DatalogJournalAdded(title=title, issn=issn,
                                 date_added=journal.created_timestamp,
                                 has_seal=has_seal,
                                 has_continuations=has_continuations,
                                 journal_id=journal.id)

    return record


class LastDatalogJournalAddedQuery:
    def __init__(self):
        pass

    def query(self):
        return {
            "size": 1,
            "sort": [
                {
                    "date_added": {
                        "order": "desc"
                    }
                }
            ],
            "query": {
                "match_all": {}
            }
        }


def get_latest_date_added():
    record = next(DatalogJournalAdded.iterate(LastDatalogJournalAddedQuery().query()), None)
    if record is None:
        return datetime.datetime.now()
    else:
        return dates.parse(record.date_added)


def find_latest_row_index(records: List[List[str]]):
    records = iter(records)
    latest_row_index = 0
    while next(records, ['Journal Title'])[0] != 'Journal Title':
        latest_row_index += 1

    while True:
        row = next(records, ['x'])
        latest_row_index += 1
        if any(r.strip() for r in row):
            return latest_row_index


def find_first_issn(rows):
    for row in rows:
        for c in row:
            if re.match(regex.ISSN, c):
                return c
    return None


def find_new_xlsx_rows(last_issn, page_size=400) -> list:
    """
    find new datalog records and convert to xlsx display format

    Parameters
    ----------
    last_issn
    page_size

    Returns
    -------
        list of datalog as xlsx display format


    """

    new_records = DatalogJournalAdded.iterate(LatestDatalogJournalQuery().query(), page_size=page_size)
    new_records = itertools.takewhile(lambda r: r.issn != last_issn, new_records)
    new_records = list(new_records)
    new_xlsx_rows = [to_display_data(j) for j in new_records]
    return new_xlsx_rows


def to_display_data(datalog: DatalogJournalAdded) -> list:
    return [datalog.title, datalog.issn,
            dates.reformat(datalog.date_added, out_format=DatalogJournalAdded.DATE_FMT),
            'Seal' if datalog.has_seal else '',
            'Yes' if datalog.has_continuations else '']


def records_new_journals(filename,
                         worksheet_name,
                         google_key_path,
                         logger_fn: Callable[[str], NoReturn] = None
                         ):
    if logger_fn is None:
        logger_fn = print

    latest_date = get_latest_date_added()
    new_datalog_list = find_new_datalog_journals(latest_date)
    new_datalog_list = (dao.patch_model_for_bulk(r) for r in new_datalog_list)
    new_datalog_list = list(new_datalog_list)
    if new_datalog_list:
        # save new records to DB
        DatalogJournalAdded.bulk([r.data for r in new_datalog_list], )
        logger_fn(f'saved new records to datalog [{len(new_datalog_list)}]')
        time.sleep(6)  # wait for bulk save to complete
    else:
        logger_fn('No new records found')

    # save new records to google sheet
    client = gsheet.load_client(google_key_path)
    try:
        sh = client.open(filename)
    except gspread.exceptions.SpreadsheetNotFound:
        logger_fn(f'No spreadsheet named "{filename}" found')
        return
    try:
        worksheet = sh.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        logger_fn(f'No worksheet named "{worksheet_name}" found')
        return

    org_rows = worksheet.get_all_values()
    org_rows = list(org_rows)
    latest_row_idx = find_latest_row_index(org_rows)
    last_issn = find_first_issn(org_rows[latest_row_idx:])
    logger_fn(f'last_issn: {last_issn}')

    new_xlsx_rows = find_new_xlsx_rows(last_issn)
    worksheet.insert_rows(new_xlsx_rows, latest_row_idx + 1)
    logger_fn(f'inserted rows to google sheet [{len(new_xlsx_rows)}]')


class DatalogJournalAddedUpdate(BackgroundTask):
    """
    ~~DatalogJournalAddedUpdate:Feature->BackgroundTask:Process~~
    """
    __action__ = "datalog_journal_added_update"

    def run(self):
        kwargs = self.get_bgjob_params()
        kwargs['logger_fn'] = self.background_job.add_audit_message

        records_new_journals(kwargs.get('filename'),
                             kwargs.get('worksheet_name'),
                             kwargs.get('google_key_path'),
                             logger_fn=kwargs.get('logger_fn')
                             )

    def cleanup(self):
        pass

    @classmethod
    def prepare(cls, username, **kwargs):
        params = {}
        cls.set_param(params, "filename", background_helper.get_value_safe('filename', '', kwargs))
        cls.set_param(params, "worksheet_name", background_helper.get_value_safe('worksheet_name', 'Added', kwargs))
        cls.set_param(params, "google_key_path", background_helper.get_value_safe('google_key_path', '', kwargs))
        return background_helper.create_job(username=username,
                                            action=cls.__action__,
                                            params=params,
                                            queue_id=huey_helper.queue_id, )

    @classmethod
    def submit(cls, background_job):
        background_helper.submit_by_background_job(background_job, datalog_journal_added_update)


huey_helper = DatalogJournalAddedUpdate.create_huey_helper(main_queue)


@huey_helper.register_schedule
def scheduled_datalog_journal_added_update():
    huey_helper.scheduled_common(
        filename=app.config.get("DATALOG_JA_FILENAME"),
        worksheet_name=app.config.get("DATALOG_JA_WORKSHEET_NAME"),
        google_key_path=app.config.get("GOOGLE_KEY_PATH"),
    )


@huey_helper.register_execute(is_load_config=False)
def datalog_journal_added_update(job_id):
    huey_helper.execute_common(job_id)


if __name__ == '__main__':
    records_new_journals(
        filename=app.config.get("DATALOG_JA_FILENAME"),
        worksheet_name=app.config.get("DATALOG_JA_WORKSHEET_NAME"),
        google_key_path=app.config.get("GOOGLE_KEY_PATH"),
    )
