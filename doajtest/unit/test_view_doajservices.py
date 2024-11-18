from doajtest.fixtures import ArticleFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.crosswalks.article_ris import ArticleRisXWalk
from portality.models import Article
from portality.util import url_for


class TestDoajservices(DoajTestCase):

    def test_export_article_ris(self):
        article = Article(**ArticleFixtureFactory.make_article_source())
        article.save(blocking=True)
        Article.refresh()

        ris = ArticleRisXWalk.article2ris(article).to_text()

        with self.app_test.test_client() as t_client:
            url = url_for('doajservices.export_article_ris', article_id=article.id, fmt='ris')
            response = t_client.get(url)
            assert response.status_code == 200
            assert response.get_data(as_text=True) == ris

    def test_export_article_ris__not_found(self):
        with self.app_test.test_client() as t_client:
            url = url_for('doajservices.export_article_ris',
                          article_id='article_id_that_does_not_exist', fmt='ris')
            response = t_client.get(url)
            assert response.status_code == 404
