from portality.models import DataDump

from copy import deepcopy

class DataDumpFixtureFactory:
    @classmethod
    def make_data_dump(cls, overlay=None):
        source = cls.make_source()
        return DataDump(**source)

    @classmethod
    def make_source(cls, overlay=None):
        source = deepcopy(DATA_DUMP_SOURCE)
        source["id"] = DataDump.makeid()
        return source

    @classmethod
    def make_n_data_dumps(cls, n, dump_date=None, journal_filenames=None, article_filenames=None):
        dds = []
        for i in range(n):
            overlay = {}
            if dump_date is not None:
                overlay["dump_date"] = dump_date(i)
            if journal_filenames is not None:
                overlay["journal"] = {"filename": journal_filenames(i)}
            if article_filenames is not None:
                overlay["article"] = {"filename": article_filenames(i)}
            source = cls.make_data_dump(overlay)
            dds.append(source)
        return dds


DATA_DUMP_SOURCE = {
    "id": DataDump.makeid(),
    "es_type": DataDump.__type__,
    "created_date": "2023-10-01T00:00:00Z",
    "last_udpated": "2023-10-01T00:00:00Z",
    "dump_date": "2023-10-01T00:00:00Z",
    "article": {
        "container": "container",
        "filename": "articles.json",
        "size": 123456,
        "url": "https://example.com/articles.json",
    },
    "journal": {
        "container": "container",
        "filename": "journals.json",
        "size": 123456,
        "url": "https://example.com/journals.json",
    }
}