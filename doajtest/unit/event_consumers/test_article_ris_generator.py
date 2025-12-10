from portality import models
from portality import constants
from doajtest.helpers import DoajTestCase
from doajtest.fixtures import ArticleFixtureFactory

from portality.events.consumers.article_ris_generator import ArticleRISGenerator
from portality.lib.thread_utils import wait_until


class TestArticleRISGenerator(DoajTestCase):
    def setUp(self):
        super(TestArticleRISGenerator, self).setUp()

    def tearDown(self):
        super(TestArticleRISGenerator, self).tearDown()

    def test_should_consume(self):
        a = ArticleFixtureFactory.make_article_source()
        event = models.Event(constants.EVENT_ARTICLE_SAVE, context={"article" : a})
        assert ArticleRISGenerator.should_consume(event)

        event = models.Event(constants.EVENT_ARTICLE_SAVE)
        assert not ArticleRISGenerator.should_consume(event)

        event = models.Event("test:event", context={"application" : "2345"})
        assert not ArticleRISGenerator.should_consume(event)

    def test_consume_success(self):
        a = ArticleFixtureFactory.make_article_source()
        article = models.Article(**a)
        article.save(blocking=True)

        with self._make_and_push_test_context_manager("/"):
            event = models.Event(constants.EVENT_ARTICLE_SAVE, context={"article" : article.data})
            ArticleRISGenerator.consume(event)

        wait_until(lambda: models.RISExport.count() == 1)
        assert models.RISExport.count() == 1


    def test_consume_fail(self):
        event = models.Event(constants.EVENT_ARTICLE_SAVE)
        with self.assertRaises(Exception):
            ArticleRISGenerator.consume(event)

