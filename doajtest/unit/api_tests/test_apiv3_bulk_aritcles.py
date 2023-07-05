import json

from doajtest.fixtures import article_doajxml
from doajtest.fixtures.article_doajxml import DoajXmlArticleFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models
from portality.util import url_for


def load_json_by_handle(handle) -> str:
    articles = [article.data for article in article_doajxml.to_articles(handle)]
    data_json_str = json.dumps(articles)
    return data_json_str


def create_user_with_api_key():
    acc = models.Account.make_account(email="a1@example.com", roles=["user", "api"])
    acc.save(blocking=True)
    return acc


class TestBulkArticles(DoajTestCase):

    def test_bulk_article_create_async__201(self):
        acc = create_user_with_api_key()
        handle = DoajXmlArticleFixtureFactory.upload_1_issn_correct()
        with self.app_test.test_client() as t_client:
            response = t_client.post(url_for('api_v3.bulk_article_create_async', api_key=acc.api_key),
                                     data=load_json_by_handle(handle),
                                     )
            assert response.status_code == 201

    def test_bulk_article_create_async__invalid_input(self):
        acc = create_user_with_api_key()
        with self.app_test.test_client() as t_client:
            response = t_client.post(url_for('api_v3.bulk_article_create_async', api_key=acc.api_key),
                                     data='{invalid json forma]',
                                     )
            assert response.status_code == 400
