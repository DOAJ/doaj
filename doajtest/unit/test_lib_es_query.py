from unittest import TestCase
import portality.lib.es_query_http as es_query_lib


class TestLibESQuery(TestCase):

    def setUp(self):
        super(TestLibESQuery, self).setUp()

        self.test_query = {
            "query": {
                "filtered": {
                    "filter": {
                        "missing": {"field": "bibjson.title"}
                    },
                    "query": {
                        "match_all": {}
                    }
                }
            },
            "size": 0,
            "from": 10,
            "aggregations": {
                "in_doaj": {
                    "terms": {
                        "field": "admin.in_doaj"
                    }
                }
            }
        }

    def tearDown(self):
        super(TestLibESQuery, self).tearDown()

    def test_01_remove_toplevel_fields(self):
        """ Check that we can remove a top-level field from a query for ES """

        no_agg = es_query_lib.remove_fields(self.test_query, ['aggregations'])

        assert no_agg == {
            "query": {
                "filtered": {
                    "filter": {
                        "missing": {"field": "bibjson.title"}
                    },
                    "query": {
                        "match_all": {}
                    }
                }
            },
            "size": 0,
            "from": 10
        }

    def test_02_doesnt_remove_nested_field(self):
        """ We don't remove a nested field from a query """

        unchanged = es_query_lib.remove_fields(self.test_query, ['terms'])

        assert unchanged == self.test_query

    def test_03_remove_restrictions(self):
        """ Remove the size and from from a query """
        no_size = es_query_lib.remove_search_limits(self.test_query)

        assert no_size == {
            "query": {
                "filtered": {
                    "filter": {
                        "missing": {"field": "bibjson.title"}
                    },
                    "query": {
                        "match_all": {}
                    }
                }
            },
            "aggregations": {
                "in_doaj": {
                    "terms": {
                        "field": "admin.in_doaj"
                    }
                }
            }
        }
