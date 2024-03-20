"""
test the bulk article API by web interface
"""
import json
import time

from doajtest.fixtures import article_doajxml
from doajtest.fixtures.article_doajxml import DoajXmlArticleFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models
from portality.models import BulkArticles
from portality.util import url_for


def load_json_by_handle(handle) -> str:
    articles = [article.data for article in article_doajxml.to_articles(handle)]
    data_json_str = json.dumps(articles)
    return data_json_str


def create_user_with_api_key():
    acc = models.Account.make_account(email="a1@example.com", roles=["user", "api"])
    acc.save(blocking=True)
    return acc


class TestBulkArticlesCreate(DoajTestCase):

    def test_bulk_article_create__201(self):
        acc = create_user_with_api_key()
        handle = DoajXmlArticleFixtureFactory.upload_1_issn_correct()
        with self.app_test.test_client() as t_client:
            response = t_client.post(url_for('api.bulk_article_create', api_key=acc.api_key),
                                     data=load_json_by_handle(handle),
                                     )
            assert response.status_code == 202

    def test_bulk_article_create__invalid_input(self):
        acc = create_user_with_api_key()
        with self.app_test.test_client() as t_client:
            response = t_client.post(url_for('api.bulk_article_create', api_key=acc.api_key),
                                     data='{invalid json forma]',
                                     )
            assert response.status_code == 400


class TestBulkArticlesStatus(DoajTestCase):

    def test_bulk_article_create_status__processed(self):
        acc = create_user_with_api_key()
        task = BulkArticles()
        task.incoming(acc.id)
        task.processed(1, 2, 3)
        task.save(blocking=True)

        time.sleep(1)

        with self.app_test.test_client() as t_client:
            resp = t_client.get(url_for('api.bulk_article_create_status',
                                        upload_id=task.id,
                                        api_key=acc.api_key))

            resp_content = json.loads(resp.data.decode('utf-8'))
            assert resp.status_code == 200
            assert resp_content['status'] == 'processed'
            assert resp_content['results']['imported'] == task.imported

    def test_bulk_article_create_status__acc_id_mismatch(self):
        acc = create_user_with_api_key()
        task = BulkArticles()
        task.incoming('askdjalskdjaslk')
        task.processed(1, 2, 3)
        task.save(blocking=True)

        time.sleep(1)

        with self.app_test.test_client() as t_client:
            resp = t_client.get(url_for('api.bulk_article_create_status',
                                        upload_id=task.id,
                                        api_key=acc.api_key))
            assert resp.status_code == 400

    def test_bulk_article_create_status__upload_id_not_exist(self):
        acc = create_user_with_api_key()

        with self.app_test.test_client() as t_client:
            resp = t_client.get(url_for('api.bulk_article_create_status',
                                        upload_id='lkadjlaksdjlaksdjlask',
                                        api_key=acc.api_key))
            assert resp.status_code == 400
