from typing import Union

from portality import models
from portality.lib import jsonpath_utils
from portality.lib.ris import RisEntry

RIS_ARTICLE_MAPPING = {
    'T1': '$.bibjson.title',
    'AU': '$.bibjson.author[*].name',
    'PY': '$.bibjson.year',
    'JO': '$.bibjson.journal.title',
    'VL': '$.bibjson.journal.volume',
    'SP': '$.bibjson.start_page',
    'EP': '$.bibjson.end_page',
    'UR': '$.bibjson.link[*].url',
    'AB': '$.bibjson.abstract',
    'KW': '$.bibjson.keywords[*]',
    'DOI': '$.bibjson.identifier[?(@.type == "doi")].id',
    'SN': '$.bibjson.journal.issns[*]',
}


class ArticleRisXWalk:

    @classmethod
    def article2ris(cls, article: Union[models.Article, dict]) -> RisEntry:
        if isinstance(article, models.Article):
            article = article.data

        entry = RisEntry(type_of_reference='JOUR')
        for tag, query in RIS_ARTICLE_MAPPING.items():
            for v in jsonpath_utils.find_values(query, article):
                entry[tag].append(v)

        return entry
