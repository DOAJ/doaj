from typing import Union

from portality import models
from portality.lib.ris import RisEntry
from portality.models.v1.bibjson import GenericBibJSON


def extra_author_names(bibjson) -> list:
    authors = bibjson.author
    authors = [a.get("name") for a in authors if a.get("name") is not None]
    return sorted(set(authors))


RIS_ARTICLE_MAPPING = {
    'T1': lambda a: a.title,
    'AU': extra_author_names,
    'PY': lambda a: a.year,
    'JF': lambda a: a.journal_title,
    'PB': lambda a: a.publisher,
    'VL': lambda a: a.volume,
    'IS': lambda a: a.number,
    'SP': lambda a: a.start_page,
    'EP': lambda a: a.end_page,
    'UR': lambda a: [x.get("url") for x in a.get_urls()],
    'AB': lambda a: a.abstract,
    'KW': lambda a: a.keywords,
    'DO': lambda a: a.get_one_identifier(GenericBibJSON.DOI),
    'SN': lambda a: a.issns(),
    'LA': lambda a: a.journal_language,
}

class ArticleRisXWalk:

    @classmethod
    def article2ris(cls, article: models.Article) -> RisEntry:
        entry = {}
        bj = article.bibjson()
        for tag, query in RIS_ARTICLE_MAPPING.items():
            values = query(bj)
            if not isinstance(values, list):
                values = [values]
            values = [v for v in values if v is not None]
            for v in values:
                if tag not in entry:
                    entry[tag] = []
                entry[tag].append(v)
        ris = RisEntry.from_dict(entry)
        ris.type='JOUR'
        return ris
