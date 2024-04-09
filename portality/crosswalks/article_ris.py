from typing import Union

from portality import models
from portality.lib import jsonpath_utils
from portality.lib.ris import RisEntry


def extra_author_names(article) -> list:
    query = '$.bibjson.author[*].name'
    values = jsonpath_utils.find_values(query, article)
    return sorted(set(values))


RIS_ARTICLE_MAPPING = {
    'T1': '$.bibjson.title',
    'AU': extra_author_names,
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
            if callable(query):
                values = query(article)
            else:
                values = jsonpath_utils.find_values(query, article)

            for v in values:
                entry[tag].append(v)

        return entry
