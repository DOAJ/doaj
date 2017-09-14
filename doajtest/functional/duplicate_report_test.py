""" Test the duplicate reporting and deletion script in its entirety """


from portality.core import app
from doajtest.helpers import DoajTestCase
from portality.scripts import article_duplicates_report_remove as a_dedupe

from esprit.raw import make_connection


class TestArticleMatch(DoajTestCase):

    def setUp(self):
        super(TestArticleMatch, self).setUp()

    def tearDown(self):
        super(TestArticleMatch, self).tearDown()

    def test_01_test_global_duplicates(self):
        """Check duplication reporting across all articles in the index"""

        conn = make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

        dupcount, delcount = a_dedupe.duplicates_per_article(conn, delete=False, snapshot=False)

        assert dupcount == 2
        assert delcount == 0
