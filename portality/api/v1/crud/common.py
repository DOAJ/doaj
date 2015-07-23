from portality.api.v1.crud.journals import JournalsCrudApi
from portality.api.v1.crud.articles import ArticlesCrudApi
from portality.api.v1.crud.applications import ApplicationsCrudApi


class CrudApi(JournalsCrudApi, ArticlesCrudApi, ApplicationsCrudApi):
    pass