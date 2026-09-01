from portality.models import DataDump
from portality.lib import dicts
from portality.core import app

from copy import deepcopy

class DataDumpFixtureFactory:
    @classmethod
    def make_data_dump(cls, overlay=None):
        source = cls.make_source(overlay)
        return DataDump(**source)

    @classmethod
    def make_source(cls, overlay=None):
        container = app.config.get("STORE_PUBLIC_DATA_DUMP_CONTAINER")
        source = deepcopy(DATA_DUMP_SOURCE)
        source["id"] = DataDump.makeid()
        source["article"]["container"] = container
        source["journal"]["container"] = container
        if overlay is not None:
            source = dicts.deep_merge(source, overlay, overlay=True)
        return source

    @classmethod
    def make_n_data_dumps(cls, n, dump_date=None, journal__filename=None, article__filename=None, overlay=None):
        dds = []
        if overlay is None:
            overlay = {}
        for i in range(n):
            individual_overlay = deepcopy(overlay)
            if dump_date is not None:
                individual_overlay["dump_date"] = dump_date(i)
            if journal__filename is not None:
                individual_overlay["journal"] = {"filename": journal__filename(i)}
            if article__filename is not None:
                individual_overlay["article"] = {"filename": article__filename(i)}
            source = cls.make_data_dump(individual_overlay)
            dds.append(source)
        return dds

    @classmethod
    def save_data_dumps(cls, dds, block=False):
        block_data = []
        for dd in dds:
            dd.save()
            block_data.append((dd.id, dd.last_updated))
        if block:
            DataDump.blockall(block_data)

DATA_DUMP_SOURCE = {
    "id": DataDump.makeid(),
    "es_type": DataDump.__type__,
    "created_date": "2023-10-01T00:00:00Z",
    "last_updated": "2023-10-01T00:00:00Z",
    "dump_date": "2023-10-01T00:00:00Z",
    "article": {
        "container": "container",
        "filename": "articles.tar.gz",
        "size": 123456,
        "url": "https://example.com/articles.json",
    },
    "journal": {
        "container": "container",
        "filename": "journals.tar.gz",
        "size": 123456,
        "url": "https://example.com/journals.json",
    }
}