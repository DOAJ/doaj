from doajtest.helpers import DoajTestCase
from portality import models
from portality.api.v1 import DiscoveryApi, DiscoveryException
from portality.api.v1.common import generate_link_headers
import time
from flask import url_for

class TestArticleMatch(DoajTestCase):

    def setUp(self):
        super(TestArticleMatch, self).setUp()
        self.max = self.app_test.config.get("DISCOVERY_MAX_RECORDS_SIZE")

    def tearDown(self):
        super(TestArticleMatch, self).tearDown()
        self.app_test.config["DISCOVERY_MAX_RECORDS_SIZE"] = self.max

    def test_01_journals(self):
        # populate the index with some journals
        saved_journals = []
        for i in range(5):
            j = models.Journal()
            j.set_in_doaj(True)
            bj = j.bibjson()
            bj.title = "Test Journal {x}".format(x=i)
            bj.add_identifier(bj.P_ISSN, "{x}000-0000".format(x=i))
            bj.publisher = "Test Publisher {x}".format(x=i)
            bj.add_url("http://homepage.com/{x}".format(x=i), "homepage")
            j.save()
            saved_journals.append((j.id, j.last_updated))

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
        saved_journals.append((j.id, j.last_updated))

        models.Journal.blockall(saved_journals)

        # now run some queries
        with self.app_test.test_request_context():
            # 1. a general query that should hit everything (except number 6)
            res = DiscoveryApi.search("journal", None, "Test", 1, 2)
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 2
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 2
            assert res.data.get("query") == "Test"

            # 2. a specific field query that should hit just one
            res = DiscoveryApi.search("journal", None, "title:\"Test Journal 2\"", 1, 5)
            assert res.data.get("total") == 1
            assert len(res.data.get("results")) == 1
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 5
            assert res.data.get("query") == "title:\"Test Journal 2\""

            # 3.paging out of range of results
            res = DiscoveryApi.search("journal", None, "Test", 2, 10)
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 0
            assert res.data.get("page") == 2
            assert res.data.get("pageSize") == 10
            assert res.data.get("query") == "Test"

            # 4. paging outside the allowed bounds (lower)
            res = DiscoveryApi.search("journal", None, "Test", 0, 0)
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 5
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 10
            assert res.data.get("query") == "Test"

            # 5. page size above upper limit
            res = DiscoveryApi.search("journal", None, "Test", 1, 100000)
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 5
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 100
            assert res.data.get("query") == "Test"

            # 6. Failed attempt at wildcard search
            with self.assertRaises(DiscoveryException):
                res = DiscoveryApi.search("journal", None, "Te*t", 1, 10)

            # 7. Failed attempt at fuzzy search
            with self.assertRaises(DiscoveryException):
                res = DiscoveryApi.search("journal", None, "title:Test~0.8", 1, 10)

            # 8. sort on a specific field, expect a default to "asc"
            res = DiscoveryApi.search("journal", None, "Test", 1, 10, "created_date")
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 5
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 10
            assert res.data.get("query") == "Test"
            assert res.data.get("results")[0].get("created_date") < res.data.get("results")[1].get("created_date")
            assert res.data.get("sort") == "created_date"

            # 9. sort on a specific field in a specified direction
            res = DiscoveryApi.search("journal", None, "Test", 1, 10, "created_date:desc")
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 5
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 10
            assert res.data.get("query") == "Test"
            assert res.data.get("results")[0].get("created_date") > res.data.get("results")[1].get("created_date")
            assert res.data.get("sort") == "created_date:desc"

            # 10. Malformed sort direction
            with self.assertRaises(DiscoveryException):
                res = DiscoveryApi.search("journal", None, "Test", 1, 10, "created_date:whatever")

            # 11. non-existant sort field
            with self.assertRaises(DiscoveryException):
                res = DiscoveryApi.search("journal", None, "Test", 1, 10, "some.missing.field:asc")

            # 12. with a forward slash, with and without escaping (note that we have to escape the : as it has meaning for lucene)
            res = DiscoveryApi.search("journal", None, '"http\://homepage.com/1"', 1, 10)
            assert res.data.get("total") == 1

            res = DiscoveryApi.search("journal", None, '"http\:\/\/homepage.com\/1"', 1, 10)
            assert res.data.get("total") == 1

    def test_02_articles(self):
        # populate the index with some articles
        for i in range(5):
            a = models.Article()
            a.set_in_doaj(True)
            bj = a.bibjson()
            bj.title = "Test Article {x}".format(x=i)
            bj.add_identifier(bj.P_ISSN, "{x}000-0000".format(x=i))
            bj.add_identifier(bj.DOI, "10.test/{x}".format(x=i))
            bj.publisher = "Test Publisher {x}".format(x=i)
            a.save()

            # make sure the last updated dates are suitably different
            time.sleep(1)

        time.sleep(1)

        # now run some queries

        with self.app_test.test_request_context():
            # 1. a general query that should hit everything
            res = DiscoveryApi.search("article", None, "Test", 1, 2)
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 2
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 2
            assert res.data.get("query") == "Test"

            # 2. a specific field query that should hit just one
            res = DiscoveryApi.search("article", None, "title:\"Test Article 2\"", 1, 5)
            assert res.data.get("total") == 1
            assert len(res.data.get("results")) == 1
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 5
            assert res.data.get("query") == "title:\"Test Article 2\""

            # 3.paging out of range of results
            res = DiscoveryApi.search("article", None, "Test", 2, 10)
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 0
            assert res.data.get("page") == 2
            assert res.data.get("pageSize") == 10
            assert res.data.get("query") == "Test"

            # 4. paging outside the allowed bounds (lower)
            res = DiscoveryApi.search("article", None, "Test", 0, 0)
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 5
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 10
            assert res.data.get("query") == "Test"

            # 5. page size above upper limit
            res = DiscoveryApi.search("article", None, "Test", 1, 100000)
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 5
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 100
            assert res.data.get("query") == "Test"

            # 6. Failed attempt at wildcard search
            with self.assertRaises(DiscoveryException):
                res = DiscoveryApi.search("article", None, "Te*t", 1, 10)

            # 7. Failed attempt at fuzzy search
            with self.assertRaises(DiscoveryException):
                res = DiscoveryApi.search("article", None, "title:Test~0.8", 1, 10)

            # 8. sort on a specific field, expect a default to "asc"
            res = DiscoveryApi.search("article", None, "Test", 1, 10, "created_date")
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 5
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 10
            assert res.data.get("query") == "Test"
            assert res.data.get("results")[0].get("created_date") < res.data.get("results")[1].get("created_date")
            assert res.data.get("sort") == "created_date"

            # 9. sort on a specific field in a specified direction
            res = DiscoveryApi.search("article", None, "Test", 1, 10, "created_date:desc")
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 5
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 10
            assert res.data.get("query") == "Test"
            assert res.data.get("results")[0].get("created_date") > res.data.get("results")[1].get("created_date")
            assert res.data.get("sort") == "created_date:desc"

            # 10. Malformed sort direction
            with self.assertRaises(DiscoveryException):
                res = DiscoveryApi.search("article", None, "Test", 1, 10, "created_date:whatever")

            # 11. non-existant sort field
            with self.assertRaises(DiscoveryException):
                res = DiscoveryApi.search("article", None, "Test", 1, 10, "some.missing.field:asc")

            # 12. with a forward slash, with and without escaping
            res = DiscoveryApi.search("article", None, '"10.test/1"', 1, 10)
            assert res.data.get("total") == 1

            res = DiscoveryApi.search("article", None, '"10.test\/1"', 1, 10)
            assert res.data.get("total") == 1

    def test_03_applications(self):
        # create an account that will own the suggestions
        acc = models.Account()
        acc.set_id("owner")
        acc.save()

        # populate the index with some suggestions owned by this owner
        for i in range(5):
            a = models.Suggestion()
            a.set_owner("owner")
            bj = a.bibjson()
            bj.title = "Test Suggestion {x}".format(x=i)
            bj.add_identifier(bj.P_ISSN, "{x}000-0000".format(x=i))
            bj.publisher = "Test Publisher {x}".format(x=i)
            bj.add_url("http://homepage.com/{x}".format(x=i), "homepage")
            a.save()

            # make sure the last updated dates are suitably different
            time.sleep(1)

        # populte the index with some which are not owned by this owner
        for i in range(5):
            a = models.Suggestion()
            a.set_owner("stranger")
            bj = a.bibjson()
            bj.title = "Test Suggestion {x}".format(x=i)
            bj.add_identifier(bj.P_ISSN, "{x}000-0000".format(x=i))
            bj.publisher = "Test Publisher {x}".format(x=i)
            a.save()

            # make sure the last updated dates are suitably different
            time.sleep(1)

        time.sleep(1)

        # now run some queries
        with self._make_and_push_test_context(acc=acc):
            # 1. a general query that should hit everything
            res = DiscoveryApi.search("application", acc, "Test", 1, 2)
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 2
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 2
            assert res.data.get("query") == "Test"

            # 2. a specific field query that should hit just one
            res = DiscoveryApi.search("application", acc, "title:\"Test Suggestion 2\"", 1, 5)
            assert res.data.get("total") == 1
            assert len(res.data.get("results")) == 1
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 5
            assert res.data.get("query") == "title:\"Test Suggestion 2\""

            # 3.paging out of range of results
            res = DiscoveryApi.search("application", acc, "Test", 2, 10)
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 0
            assert res.data.get("page") == 2
            assert res.data.get("pageSize") == 10
            assert res.data.get("query") == "Test"

            # 4. paging outside the allowed bounds (lower)
            res = DiscoveryApi.search("application", acc, "Test", 0, 0)
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 5
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 10
            assert res.data.get("query") == "Test"

            # 5. page size above upper limit
            res = DiscoveryApi.search("application", acc, "Test", 1, 100000)
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 5
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 100
            assert res.data.get("query") == "Test"

            # 6. Failed attempt at wildcard search
            with self.assertRaises(DiscoveryException):
                res = DiscoveryApi.search("application", acc, "Te*t", 1, 10)

            # 7. Failed attempt at fuzzy search
            with self.assertRaises(DiscoveryException):
                res = DiscoveryApi.search("application", acc, "title:Test~0.8", 1, 10)

            # 8. sort on a specific field, expect a default to "asc"
            res = DiscoveryApi.search("application", acc, "Test", 1, 10, "created_date")
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 5
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 10
            assert res.data.get("query") == "Test"
            assert res.data.get("results")[0].get("created_date") < res.data.get("results")[1].get("created_date")
            assert res.data.get("sort") == "created_date"

            # 9. sort on a specific field in a specified direction
            res = DiscoveryApi.search("application", acc, "Test", 1, 10, "created_date:desc")
            assert res.data.get("total") == 5
            assert len(res.data.get("results")) == 5
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 10
            assert res.data.get("query") == "Test"
            assert res.data.get("results")[0].get("created_date") > res.data.get("results")[1].get("created_date")
            assert res.data.get("sort") == "created_date:desc"

            # 10. Malformed sort direction
            with self.assertRaises(DiscoveryException):
                res = DiscoveryApi.search("application", acc, "Test", 1, 10, "created_date:whatever")

            # 11. non-existant sort field
            with self.assertRaises(DiscoveryException):
                res = DiscoveryApi.search("application", acc, "Test", 1, 10, "some.missing.field:asc")

            # 12. with a forward slash, with and without escaping (note that we have to escape the : as it has meaning for lucene)
            res = DiscoveryApi.search("application", acc, '"http\://homepage.com/1"', 1, 10)
            assert res.data.get("total") == 1

            res = DiscoveryApi.search("application", acc, '"http\:\/\/homepage.com\/1"', 1, 10)
            assert res.data.get("total") == 1

        # 13. A search with an account that isn't either of the ones in the dataset
        other = models.Account()
        other.set_id("other")
        with self._make_and_push_test_context(acc=other):
            res = DiscoveryApi.search("application", other, "Test", 1, 10, "created_date:desc")
            assert res.data.get("total") == 0

    def test_04_paging_for_link_headers(self):
        # calc_pagination takes total, page_size, requested_page
        # and returns page_count, previous_page, next_page, last_page
        # request 1 of 1 pages
        assert DiscoveryApi._calc_pagination(0, 10, 1) == (1, None, None, 1)  # 0 results still means page 1
        assert DiscoveryApi._calc_pagination(1, 10, 1) == (1, None, None, 1)
        assert DiscoveryApi._calc_pagination(2, 10, 1) == (1, None, None, 1)
        assert DiscoveryApi._calc_pagination(3, 10, 1) == (1, None, None, 1)
        assert DiscoveryApi._calc_pagination(9, 10, 1) == (1, None, None, 1)
        assert DiscoveryApi._calc_pagination(10, 10, 1) == (1, None, None, 1)

        # request 1st of 2 pages
        assert DiscoveryApi._calc_pagination(11, 10, 1) == (2, None, 2, 2)
        assert DiscoveryApi._calc_pagination(12, 10, 1) == (2, None, 2, 2)
        assert DiscoveryApi._calc_pagination(19, 10, 1) == (2, None, 2, 2)
        assert DiscoveryApi._calc_pagination(20, 10, 1) == (2, None, 2, 2)

        # request 2nd of 2 pages
        assert DiscoveryApi._calc_pagination(11, 10, 2) == (2, 1, None, 2)
        assert DiscoveryApi._calc_pagination(12, 10, 2) == (2, 1, None, 2)
        assert DiscoveryApi._calc_pagination(19, 10, 2) == (2, 1, None, 2)
        assert DiscoveryApi._calc_pagination(20, 10, 2) == (2, 1, None, 2)

        # various requests for 10s of 1000s of results
        assert DiscoveryApi._calc_pagination(9900 , 100, 1) == (99, None, 2, 99)
        assert DiscoveryApi._calc_pagination(9900 , 100, 99) == (99, 98, None, 99)

        assert DiscoveryApi._calc_pagination(9901 , 100, 1) == (100, None, 2, 100)
        assert DiscoveryApi._calc_pagination(9902 , 100, 1) == (100, None, 2, 100)
        assert DiscoveryApi._calc_pagination(10000, 100, 1) == (100, None, 2, 100)
        assert DiscoveryApi._calc_pagination(10000, 100, 2) == (100, 1, 3, 100)
        assert DiscoveryApi._calc_pagination(10000, 100, 98) == (100, 97, 99, 100)
        assert DiscoveryApi._calc_pagination(10000, 100, 99) == (100, 98, 100, 100)
        assert DiscoveryApi._calc_pagination(10000, 100, 100) == (100, 99, None, 100)

    def test_05_http_link_headers(self):
        metadata = {
            'prev': 'https://example.org/api/v1/search/articles/%2A?page=1&pageSize=10',
            'next': 'https://example.org/api/v1/search/articles/%2A?page=3&pageSize=10',
            'last': 'https://example.org/api/v1/search/articles/%2A?page=5&pageSize=10'
        }

        assert generate_link_headers(metadata) == '<https://example.org/api/v1/search/articles/%2A?page=1&pageSize=10>; rel=prev, <https://example.org/api/v1/search/articles/%2A?page=5&pageSize=10>; rel=last, <https://example.org/api/v1/search/articles/%2A?page=3&pageSize=10>; rel=next', generate_link_headers(metadata)

    def test_06_deep_paging_limit(self):
        # populate the index with some journals
        jids = []
        for i in range(10):
            j = models.Journal()
            j.set_in_doaj(True)
            bj = j.bibjson()
            bj.title = "Test Journal {x}".format(x=i)
            bj.add_identifier(bj.P_ISSN, "{x}000-0000".format(x=i))
            bj.publisher = "Test Publisher {x}".format(x=i)
            bj.add_url("http://homepage.com/{x}".format(x=i), "homepage")
            j.save()
            jids.append((j.id, j.last_updated))

        self.app_test.config["DISCOVERY_MAX_RECORDS_SIZE"] = 5

        # block until all the records are saved
        for jid, lu in jids:
            models.Journal.block(jid, lu, sleep=0.05)

        # now run some queries
        with self.app_test.test_request_context():
            # check that the first page still works
            res = DiscoveryApi.search("journal", None, "*", 1, 5)
            assert res.data.get("total") == 10
            assert len(res.data.get("results")) == 5
            assert res.data.get("page") == 1
            assert res.data.get("pageSize") == 5

            # but that the second page fails
            with self.assertRaises(DiscoveryException):
                try:
                    res = DiscoveryApi.search("journal", None, "*", 2, 5)
                except DiscoveryException as e:
                    data_dump_url = url_for("doaj.public_data_dump")
                    oai_article_url = url_for("oaipmh.oaipmh", specified="article")
                    oai_journal_url = url_for("oaipmh.oaipmh")
                    assert data_dump_url in e.message
                    assert oai_article_url in e.message
                    assert oai_journal_url in e.message
                    raise
