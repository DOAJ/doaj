from portality.api.v1.common import Api

from portality import models


class DiscoveryApi(Api):

    @classmethod
    def search_articles(cls, q):
        return [models.Article(id="1ef4d6", bibjson={"title": "Mock Article 1"}), models.Article(id="1ef4d7", bibjson={"title": "Mock Article 2"})]

    @classmethod
    def search_journals(cls, q):
        return [models.Journal(id="2ef4d6", bibjson={"title": "Mock Journal 1"}), models.Journal(id="2ef4d7", bibjson={"title": "Mock Journal 2"})]