from portality.models import JournalCSV
from portality.lib import dicts
from portality.core import app

from copy import deepcopy

class JournalCSVFixtureFactory:
    @classmethod
    def make_journal_csv(cls, overlay=None):
        source = cls.make_source(overlay)
        return JournalCSV(**source)

    @classmethod
    def make_source(cls, overlay=None):
        container = app.config.get("STORE_JOURNAL_CSV_CONTAINER")
        source = deepcopy(JOURNAL_CSV_SOURCE)
        source["id"] = JournalCSV.makeid()
        source["container"] = container
        if overlay is not None:
            source = dicts.deep_merge(source, overlay, overlay=True)
        return source

    @classmethod
    def make_n_csvs(cls, n, export_date=None, filename=None, overlay=None):
        jcs = []
        if overlay is None:
            overlay = {}
        for i in range(n):
            individual_overlay = deepcopy(overlay)
            if export_date is not None:
                individual_overlay["export_date"] = export_date(i)
            if filename is not None:
                individual_overlay["filename"] = filename(i)
            source = cls.make_journal_csv(individual_overlay)
            jcs.append(source)
        return jcs

    @classmethod
    def save_journal_csvs(cls, jcs, block=False):
        block_data = []
        for jc in jcs:
            jc.save()
            block_data.append((jc.id, jc.last_updated))
        if block:
            JournalCSV.blockall(block_data)

JOURNAL_CSV_SOURCE = {
    "id": JournalCSV.makeid(),
    "es_type": JournalCSV.__type__,
    "created_date": "2023-10-01T00:00:00Z",
    "last_updated": "2023-10-01T00:00:00Z",
    "export_date": "2023-10-01T00:00:00Z",
    "container": "container",
    "filename": "journals.csv",
    "size": 123456,
    "url": "https://example.com/journals.csv"
}