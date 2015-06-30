from doajtest.helpers import DoajTestCase
from portality import models
from portality.api.v1 import DiscoveryApi, DiscoveryException
import time

class TestArticleMatch(DoajTestCase):

    def setUp(self):
        super(TestArticleMatch, self).setUp()

    def tearDown(self):
        super(TestArticleMatch, self).tearDown()

    def test_01_journals(self):
        # populate the index with some journals
        for i in range(5):
            j = models.Journal()
            j.set_in_doaj(True)
            bj = j.bibjson()
            bj.title = "Test Journal {x}".format(x=i)
            bj.add_identifier(bj.P_ISSN, "{x}000-0000".format(x=i))
            bj.publisher = "Test Publisher {x}".format(x=i)
            bj.add_url("http://homepage.com/{x}".format(x=i), "homepage")
            j.save()

            # make sure the last updated dates are suitably different
            time.sleep(1)

        # add one that's not in DOAJ, which shouldn't turn up in our results
        j = models.Journal()
        j.set_in_doaj(False)
        bj = j.bibjson()
        bj.title = "Test Journal {x}".format(x=6)
        bj.add_identifier(bj.P_ISSN, "{x}000-0000".format(x=6))
        bj.publisher = "Test Publisher {x}".format(x=6)
        bj.add_url("http://homepage.com/{x}".format(x=6), "homepage")
        j.save()

        time.sleep(1)

        # now run some queries

        # 1. a general query that should hit everything (except number 6)
        res = DiscoveryApi.search_journals("Test", 1, 2)
        assert res.data.get("total") == 5
        assert len(res.data.get("results")) == 2
        assert res.data.get("page") == 1
        assert res.data.get("pageSize") == 2
        assert res.data.get("query") == "Test"

        # 2. a specific field query that should hit just one
        res = DiscoveryApi.search_journals("title:\"Test Journal 2\"", 1, 5)
        assert res.data.get("total") == 1
        assert len(res.data.get("results")) == 1
        assert res.data.get("page") == 1
        assert res.data.get("pageSize") == 5
        assert res.data.get("query") == "title:\"Test Journal 2\""

        # 3.paging out of range of results
        res = DiscoveryApi.search_journals("Test", 2, 10)
        assert res.data.get("total") == 5
        assert len(res.data.get("results")) == 0
        assert res.data.get("page") == 2
        assert res.data.get("pageSize") == 10
        assert res.data.get("query") == "Test"

        # 4. paging outside the allowed bounds (lower)
        res = DiscoveryApi.search_journals("Test", 0, 0)
        assert res.data.get("total") == 5
        assert len(res.data.get("results")) == 5
        assert res.data.get("page") == 1
        assert res.data.get("pageSize") == 10
        assert res.data.get("query") == "Test"

        # 5. page size above upper limit
        res = DiscoveryApi.search_journals("Test", 1, 100000)
        assert res.data.get("total") == 5
        assert len(res.data.get("results")) == 5
        assert res.data.get("page") == 1
        assert res.data.get("pageSize") == 100
        assert res.data.get("query") == "Test"

        # 6. Failed attempt at wildcard search
        with self.assertRaises(DiscoveryException):
            res = DiscoveryApi.search_journals("Te*t", 1, 10)

        # 7. Failed attempt at fuzzy search
        with self.assertRaises(DiscoveryException):
            res = DiscoveryApi.search_journals("title:Test~0.8", 1, 10)

    def test_02_articles(self):
        # populate the index with some articles
        for i in range(5):
            a = models.Article()
            a.set_in_doaj(True)
            bj = a.bibjson()
            bj.title = "Test Article {x}".format(x=i)
            bj.add_identifier(bj.P_ISSN, "{x}000-0000".format(x=i))
            bj.publisher = "Test Publisher {x}".format(x=i)
            a.save()

            # make sure the last updated dates are suitably different
            time.sleep(1)

        time.sleep(1)

        # now run some queries

        # 1. a general query that should hit everything
        res = DiscoveryApi.search_articles("Test", 1, 2)
        assert res.data.get("total") == 5
        assert len(res.data.get("results")) == 2
        assert res.data.get("page") == 1
        assert res.data.get("pageSize") == 2
        assert res.data.get("query") == "Test"

        # 2. a specific field query that should hit just one
        res = DiscoveryApi.search_articles("title:\"Test Article 2\"", 1, 5)
        assert res.data.get("total") == 1
        assert len(res.data.get("results")) == 1
        assert res.data.get("page") == 1
        assert res.data.get("pageSize") == 5
        assert res.data.get("query") == "title:\"Test Article 2\""

        # 3.paging out of range of results
        res = DiscoveryApi.search_articles("Test", 2, 10)
        assert res.data.get("total") == 5
        assert len(res.data.get("results")) == 0
        assert res.data.get("page") == 2
        assert res.data.get("pageSize") == 10
        assert res.data.get("query") == "Test"

        # 4. paging outside the allowed bounds (lower)
        res = DiscoveryApi.search_articles("Test", 0, 0)
        assert res.data.get("total") == 5
        assert len(res.data.get("results")) == 5
        assert res.data.get("page") == 1
        assert res.data.get("pageSize") == 10
        assert res.data.get("query") == "Test"

        # 5. page size above upper limit
        res = DiscoveryApi.search_articles("Test", 1, 100000)
        assert res.data.get("total") == 5
        assert len(res.data.get("results")) == 5
        assert res.data.get("page") == 1
        assert res.data.get("pageSize") == 100
        assert res.data.get("query") == "Test"

        # 6. Failed attempt at wildcard search
        with self.assertRaises(DiscoveryException):
            res = DiscoveryApi.search_articles("Te*t", 1, 10)

        # 7. Failed attempt at fuzzy search
        with self.assertRaises(DiscoveryException):
            res = DiscoveryApi.search_articles("title:Test~0.8", 1, 10)