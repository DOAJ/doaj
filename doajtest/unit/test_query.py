import pytest
from elasticsearch import RequestError

from portality import models

from doajtest.fixtures import AccountFixtureFactory, ArticleFixtureFactory, EditorGroupFixtureFactory, \
    ApplicationFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase, deep_sort

from portality.bll.services.query import QueryService, Query
from portality.bll import exceptions

QUERY_ROUTE = {
    "query": {
        "article": {
            "auth": False,
            "role": None,
            "query_filters": ["only_in_doaj"],
            "result_filters": ["public_result_filter"],
            "dao": "portality.models.Article"
        },
        "journal": {
            "auth": False,
            "role": None,
            "query_filters": ["only_in_doaj"],
            "result_filters": ["public_result_filter"],
            "dao": "portality.models.Journal"
        }
    },
    "publisher_query": {
        "journal": {
            "auth": True,
            "role": "publisher",
            "query_filters": ["owner", "only_in_doaj"],
            "result_filters": ["publisher_result_filter"],
            "dao": "portality.models.Journal"
        }
    },
    "admin_query": {
        "journal": {
            "auth": True,
            "role": "admin",
            "dao": "portality.models.Journal"
        },
        "suggestion": {
            "auth": True,
            "role": "admin",
            "dao": "portality.models.Application"
        },
    },
    "api_query": {
        "article": {
            "auth": False,
            "role": None,
            "query_filters": ["only_in_doaj", "public_source"],
            "result_filters": ["public_result_filter"],
            "dao": "portality.models.Article",
            "page_size": 1
        },
        "journal": {
            "auth": False,
            "role": None,
            "query_filters": ["only_in_doaj", "public_source"],
            "dao": "portality.models.Journal"
        },
        "suggestion": {
            "auth": True,
            "role": None,
            "query_filters": ["owner", "private_source"],
            "dao": "portality.models.Suggestion"
        }
    },
    "editor_query": {
        "journal": {
            "auth": True,
            "role": "editor",
            "dao": "portality.models.Journal"
        },
        "suggestion": {
            "auth": True,
            "role": "editor",
            "dao": "portality.models.Application"
        }
    },
    "associate_query": {
        "journal": {
            "auth": True,
            "role": "associate_editor",
            "dao": "portality.models.Journal"
        },
        "suggestion": {
            "auth": True,
            "role": "associate_editor",
            "dao": "portality.models.Application"
        }
    }
}

SEARCH_ALL_QUERY_ROUTE = {
    "query": {
        "journal": {
            "auth": False,
            "role": None,
            "query_filters": ["search_all_meta"],
            "dao": "portality.models.Journal"
        }
    },
    "editor_query": {
        "journal": {
            "auth": True,
            "role": "editor",
            "query_filters": ["search_all_meta"],
            "dao": "portality.models.Journal"
        },
        "suggestion": {
            "auth": False,
            "role": "editor",
            "query_filters": ["search_all_meta"],
            "dao": "portality.models.Application"
        }
    },
    "associate_query": {
        "journal": {
            "auth": False,
            "role": "associate_editor",
            "query_filters": ["search_all_meta"],
            "dao": "portality.models.Journal"
        },
        "suggestion": {
            "auth": False,
            "role": "associate_editor",
            "query_filters": ["search_all_meta"],
            "dao": "portality.models.Application"
        }
    }
}

QUERY_FILTERS = {
    "non_public_fields_validator" : "portality.lib.query_filters.non_public_fields_validator",

    # query filters
    "only_in_doaj" : "portality.lib.query_filters.only_in_doaj",
    "owner" : "portality.lib.query_filters.owner",
    "associate" : "portality.lib.query_filters.associate",
    "editor" : "portality.lib.query_filters.editor",

    # result filters
    "public_result_filter" : "portality.lib.query_filters.public_result_filter",

    # source filter
    "public_source": "portality.lib.query_filters.public_source",

    # search on all meta field
    "search_all_meta" : "portality.lib.query_filters.search_all_meta",
}

MATCH_ALL_RAW_QUERY = {"query": {"match_all": {}}}


def raw_query(query):
    return {'query': {'query_string': {'query': query, 'default_operator': 'AND'}}, 'size': 0, 'track_total_hits': True}


def without_keys(d, keys):
    return {x: d[x] for x in d if x not in keys}


class TestQuery(DoajTestCase):

    def setUp(self):
        super(TestQuery, self).setUp()
        self.OLD_QUERY_ROUTE = self.app_test.config.get('QUERY_ROUTE')
        self.app_test.config['QUERY_ROUTE'] = QUERY_ROUTE

        self.OLD_QUERY_FILTERS = self.app_test.config.get('QUERY_FILTERS')
        self.app_test.config['QUERY_FILTERS'] = QUERY_FILTERS

    def tearDown(self):
        super(TestQuery, self).tearDown()
        self.app_test.config['QUERY_ROUTE'] = self.OLD_QUERY_ROUTE
        self.app_test.config['QUERY_FILTERS'] = self.OLD_QUERY_FILTERS

    def get_application_with_notes(self):
        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)
        app.add_note("application test", "2015-01-01T00:00:00Z")
        app.save()
        return app

    def get_journal_with_notes(self):
        j = models.Journal()
        j.set_id("aabbccdd")
        j.set_created("2010-01-01T00:00:00Z")
        j.set_last_updated("2012-01-01T00:00:00Z")
        j.set_last_manual_update("2014-01-01T00:00:00Z")
        j.set_owner("rama")
        j.set_editor_group("worldwide")
        j.set_editor("eddie")
        j.add_contact("rama", "rama@email.com")
        j.add_note("testing", "2015-01-01T00:00:00Z")
        j.set_bibjson({"title": "test"})
        j.save()
        return j

    def test_01_auth(self):
        with self.app_test.test_client() as t_client:
            response = t_client.get('/query/journal')
            assert response.status_code == 200, response.status_code

            # theoretically should be a 404, but the code checks QUERY_ROUTE config first, so auth checks go first
            response = t_client.get('/query/nonexistent')
            assert response.status_code == 403, response.status_code

            response = t_client.get('/query/article')
            assert response.status_code == 200, response.status_code

            response = t_client.get('/publisher_query/journal')
            assert response.status_code == 403, response.status_code

            # These don't work for some reason, the logging in bit with the context doesn't work so they're all 403 Forbidden.
            # a publisher logs in
            # pub = models.Account(**AccountFixtureFactory.make_publisher_source())
            # ctx = self._make_and_push_test_context(acc=pub, path='/publisher_query/journal')
            # response = t_client.get('/publisher_query/journal')
            # assert response.status_code == 200, response.status_code
            #
            # response = t_client.get('/admin_query/journal')
            # assert response.status_code == 403, response.status_code
            # ctx.pop()

            # a managing editor logs in
            # maned = models.Account(**AccountFixtureFactory.make_managing_editor_source())
            # with self._make_and_push_test_context(acc=maned):
            #     response = t_client.get('/admin_query/journal')
            #     assert response.status_code == 200, response.status_code

    def test_01b_query_400_errors(self):
        """Test that query endpoint returns proper 400 errors with correct template"""
        with self.app_test.test_client() as t_client:
            # Test with invalid JSON in source parameter (triggers abort(400) on line 37 of query.py)
            # This simulates the user's reported issue with malformed query strings
            response = t_client.get('/query/journal/_search?source=invalid_json_here')
            assert response.status_code == 400, response.status_code
            # Verify it renders the 400 template, not a template error
            assert b'400' in response.data and b'bad request' in response.data.lower()

            # Test with another invalid JSON example (like the user's URL with asterisks)
            response = t_client.get('/query/journal/_search?source={"query":{"query_string":{"query":"Darwin,*%20Bonaparte*"}}}INVALID')
            assert response.status_code == 400, response.status_code
            assert b'400' in response.data and b'bad request' in response.data.lower()

    def test_02_query_gen(self):
        q = Query()
        q.add_must({"term": {"admin.in_doaj": True}})
        assert q.as_dict() == {
            'track_total_hits' : True,
            'query': {
                'bool': {
                    'must': [
                        {"match_all" : {}},
                        {'term': {'admin.in_doaj': True}}
                    ]
                }
            }
        },q.as_dict()

        q = Query()
        q.clear_match_all()
        assert q.as_dict() == {'track_total_hits' : True, 'query': {}}, q.as_dict()

        q = Query()
        q.add_include("last_updated")
        assert q.as_dict() == {'track_total_hits': True, "query": {"match_all": {}},
                               "_source": {"includes": ["last_updated"]}}, q.as_dict()

        q = Query()
        q.add_include(["last_updated", "id"])
        assert sorted(q.as_dict()) == sorted({'track_total_hits': True, "query": {"match_all": {}},
                                              "_source": {"includes": ["last_updated", "id"]}}) or sorted(
            q.as_dict()) == sorted(
            {"query": {"match_all": {}}, "_source": {"include": ["last_updated", "id"]}}), sorted(q.as_dict())

    def test_03_query_svc_get_config(self):
        qsvc = QueryService()
        cfg = qsvc._get_config_for_search('query', 'article', account=None)
        assert cfg == {
            "auth" : False,
            "role" : None,
            "query_filters" : ["only_in_doaj"],
            "result_filters" : ["public_result_filter"],
            "dao" : "portality.models.Article"
        }, cfg

        with self.assertRaises(exceptions.AuthoriseException):
            cfg = qsvc._get_config_for_search('query_nonexistent', 'article', account=None)

        with self.assertRaises(exceptions.AuthoriseException):
            cfg = qsvc._get_config_for_search('query', 'article_nonexistent', account=None)

        with self.assertRaises(exceptions.AuthoriseException):  # because account is None and auth is required
            cfg = qsvc._get_config_for_search('publisher_query', 'journal', account=None)

        pub = models.Account(**AccountFixtureFactory.make_publisher_source())
        cfg = qsvc._get_config_for_search('publisher_query', 'journal', account=pub)
        assert cfg == {
            "auth" : True,
            "role" : "publisher",
            "query_filters" : ["owner", "only_in_doaj"],
            "result_filters" : ["publisher_result_filter"],
            "dao" : "portality.models.Journal"
        }

        with self.assertRaises(exceptions.AuthoriseException):  # because account is a publisher and an 'admin' role is needed
            cfg = qsvc._get_config_for_search('admin_query', 'journal', account=pub)

        maned = models.Account(**AccountFixtureFactory.make_managing_editor_source())
        cfg = qsvc._get_config_for_search('admin_query', 'journal', account=maned)
        assert cfg == {
            "auth" : True,
            "role" : "admin",
            "dao" : "portality.models.Journal"
        }

    def test_04_pre_filter_search_query(self):
        q = Query()
        qsvc = QueryService()
        cfg = qsvc._get_config_for_search('query', 'article', account=None)

        assert q.as_dict() == {"track_total_hits" : True, "query": {"match_all": {}}}, q.as_dict()
        qsvc._pre_filter_search_query(cfg, q)
        assert q.as_dict() == {
            "track_total_hits": True,
            'query': {
                'bool': {
                    'filter': [
                        {'term': {'admin.in_doaj': True}}
                    ]
                }
            }
        }, q.as_dict()

    def test_05_post_filter_search_results(self):
        # The config above says that the public_result_filter should run on the results. That should delete admin.publisher_record_id.
        # We take a fake result set with the secret info in, run the results filters and expect to have the data cleaned.
        # We are testing that the mechanism that runs post filters works, the idea is not to test public_result_filter specifically.
        qsvc = QueryService()
        cfg = qsvc._get_config_for_search('query', 'article', account=None)

        res = {
          "hits": {
            "hits": [
              { "_type": "article", "_source": { "admin": {"publisher_record_id" : "some_identifier"}, "bibjson": {}}},
              { "_type": "article", "_source": { "admin": {"publisher_record_id" : "some_identifier"}, "bibjson": {}}},
              { "_type": "article", "_source": { "admin": {"publisher_record_id" : "some_identifier"}, "bibjson": {}}}
            ],
            "total": 3
          }
        }

        res = qsvc._post_filter_search_results(cfg, res)

        assert res == {
          "hits": {
            "hits": [
              { "_type": "article", "_source": { "admin": {}, "bibjson": {}}},
              { "_type": "article", "_source": { "admin": {}, "bibjson": {}}},
              { "_type": "article", "_source": { "admin": {}, "bibjson": {}}}
            ],
            "total": 3
          }
        }

    def test_06_post_filter_search_results_unpacked(self):
        # The config above says that the public_result_filter should run on the results. That should delete admin.publisher_record_id.
        # We take a fake result set with the secret info in, run the results filters and expect to have the data cleaned.
        # We are testing that the mechanism that runs post filters works, the idea is not to test public_result_filter specifically.
        qsvc = QueryService()
        cfg = qsvc._get_config_for_search('query', 'article', account=None)

        res1 = { "admin": {"publisher_record_id" : "some_identifier"}, "bibjson": {}}
        res2 = { "admin": {"publisher_record_id" : "some_identifier"}, "bibjson": {}}
        res3 = { "admin": {"publisher_record_id" : "some_identifier"}, "bibjson": {}}

        res1 = qsvc._post_filter_search_results(cfg, res1, unpacked=True)
        assert res1 == { "admin": {}, "bibjson": {}}

        res2 = qsvc._post_filter_search_results(cfg, res2, unpacked=True)
        assert res2 == { "admin": {}, "bibjson": {}}

        res3 = qsvc._post_filter_search_results(cfg, res3, unpacked=True)
        assert res1 == { "admin": {}, "bibjson": {}}

    def test_07_get_query(self):
        # q = Query()
        raw_query = {
            "query" : {
                "query_string" : {
                    "query" : '*',
                    "default_operator": "AND"
                }
            },
            "from" : 0,
            "size" : 100
        }
        qsvc = QueryService()
        cfg = qsvc._get_config_for_search('api_query', 'journal', account=None)

        # assert q.as_dict() == {"query": {"match_all": {}}}, q.as_dict()
        query = qsvc._get_query(cfg, raw_query)
        expected_result = {
            'query': {
                'bool': {
                    'must': [
                        {'query_string': {'query': '*', 'default_operator': 'AND'}}
                    ],
                    "filter" : [
                        {'term': {'admin.in_doaj': True}}
                    ]
                }
            },
            '_source': {'includes': ['last_updated', 'admin.ticked', 'created_date', 'id', 'bibjson']},
            'from': 0, 'size': 100
        }
        q_but_source = without_keys(query.as_dict(), ['_source'])
        r_but_source = without_keys(expected_result, ['_source'])
        query_sorted = deep_sort(query.as_dict())
        expected_result_sorted = deep_sort(expected_result)
        assert query_sorted == expected_result_sorted, query_sorted

    def test_08_get_dao_klass(self):
        qsvc = QueryService()
        cfg = qsvc._get_config_for_search('query', 'article', account=None)
        dao_klass = qsvc._get_dao_klass(cfg)
        self.assertIs(dao_klass, models.Article)

    def test_09_search(self):
        # Just bringing it all together. Make 4 articles: 3 in DOAJ, 1 not in DOAJ
        # We then expect pre-filters to run on the query, ensuring we only get the 3 in DOAJ articles.
        # We also expect the post-filters to run on the results, ensuring non-public data is deleted from the admin section.
        qsvc = QueryService()

        articles = []
        for i in range(0, 3):
            articles.append(models.Article(**ArticleFixtureFactory.make_article_source(with_id=False)))
            assert articles[-1].publisher_record_id() == 'some_identifier'
            articles[-1].save(blocking=True)
        articles.append(models.Article(**ArticleFixtureFactory.make_article_source(with_id=False, in_doaj=False)))
        articles[-1].save(blocking=True)

        res = qsvc.search('query', 'article', {"query": {"match_all": {}}}, account=None, additional_parameters={})
        assert res['hits']['total']["value"] == 3, res['hits']['total']["value"]

        for hit in res['hits']['hits']:
            am = models.Article(**hit)
            assert am.publisher_record_id() is None, am.publisher_record_id()

    def test_10_scroll(self):
        # Just bringing it all together. Make 4 articles: 3 in DOAJ, 1 not in DOAJ
        # We then expect pre-filters to run on the query, ensuring we only get the 3 in DOAJ articles.
        # We also expect the post-filters to run on the results, ensuring non-public data is deleted from the admin section.
        qsvc = QueryService()

        articles = []
        for i in range(0, 3):
            articles.append(models.Article(**ArticleFixtureFactory.make_article_source(with_id=False)))
            assert articles[-1].publisher_record_id() == 'some_identifier'
            articles[-1].save(blocking=True)
        articles.append(models.Article(**ArticleFixtureFactory.make_article_source(with_id=False, in_doaj=False)))
        articles[-1].save(blocking=True)
        q = {"query": {"match_all": {}}}
        for res in qsvc.scroll('api_query', 'article', q, None, None):
            am = models.Article(**res)
            assert am.publisher_record_id() is None, am.publisher_record_id()

    def test_public_query_notes(self):

        self.app_test.config['QUERY_ROUTE'] = SEARCH_ALL_QUERY_ROUTE

        self.get_journal_with_notes()

        qsvc = QueryService()

        res = qsvc.search('query', 'journal', {'query': {'query_string': {'query': 'testing',
                            'default_operator': 'AND'}}, 'size': 0, 'aggs': {'country_publisher':
                            {'terms': {'field': 'index.country.exact', 'size': 100, 'order': {'_count': 'desc'}}}},
                                               'track_total_hits': True}, account=None, additional_parameters={})
        assert res['hits']['total']["value"] == 0, res['hits']['total']["value"]

    def test_admin_query_notes(self):

        self.get_journal_with_notes()

        maned = models.Account(**AccountFixtureFactory.make_managing_editor_source())
        maned.save(blocking=True)
        qsvc = QueryService()

        res = qsvc.search('admin_query', 'journal', {'query': {'query_string': {'query': 'testing',
                            'default_operator': 'AND'}}, 'size': 0, 'aggs': {'country_publisher':
                            {'terms': {'field': 'index.country.exact', 'size': 100, 'order': {'_count': 'desc'}}}},
                                               'track_total_hits': True}, account=maned, additional_parameters={})
        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

    def test_editor_query_notes(self):

        self.app_test.config['QUERY_ROUTE'] = SEARCH_ALL_QUERY_ROUTE

        self.get_journal_with_notes()

        editor = models.Account(**AccountFixtureFactory.make_editor_source())
        editor.save(blocking=True)

        eg_source = EditorGroupFixtureFactory.make_editor_group_source(maned=editor.id)
        eg = models.EditorGroup(**eg_source)
        eg.save(blocking=True)

        qsvc = QueryService()

        res = qsvc.search('editor_query', 'journal', {'query': {'query_string': {'query': 'testing',
                            'default_operator': 'AND'}}, 'size': 0, 'aggs': {'country_publisher':
                            {'terms': {'field': 'index.country.exact', 'size': 100, 'order': {'_count': 'desc'}}}},
                                               'track_total_hits': True}, account=editor, additional_parameters={})
        assert res['hits']['total']["value"] == 0, res['hits']['total']["value"]

    def test_associate_editor_query_notes(self):

        self.app_test.config['QUERY_ROUTE'] = SEARCH_ALL_QUERY_ROUTE

        self.get_journal_with_notes()

        associate = models.Account(**AccountFixtureFactory.make_assed1_source())
        associate.save(blocking=True)

        eg_source = EditorGroupFixtureFactory.make_editor_group_source(maned=associate.id)
        eg = models.EditorGroup(**eg_source)
        eg.save(blocking=True)

        qsvc = QueryService()

        res = qsvc.search('associate_query', 'journal', {'query': {'query_string': {'query': 'testing',
                            'default_operator': 'AND'}}, 'size': 0, 'aggs': {'country_publisher':
                            {'terms': {'field': 'index.country.exact', 'size': 100, 'order': {'_count': 'desc'}}}},
                                               'track_total_hits': True}, account=associate, additional_parameters={})
        assert res['hits']['total']["value"] == 0, res['hits']['total']["value"]

    def test_associate_editor_application_query_notes(self):

        self.app_test.config['QUERY_ROUTE'] = SEARCH_ALL_QUERY_ROUTE

        app = self.get_application_with_notes()

        associate = models.Account(**AccountFixtureFactory.make_assed1_source())
        associate.save(blocking=True)

        eg_source = EditorGroupFixtureFactory.make_editor_group_source(maned=associate.id)
        eg = models.EditorGroup(**eg_source)
        eg.set_name(app.editor_group)
        eg.save(blocking=True)

        qsvc = QueryService()

        res = qsvc.search('associate_query', 'suggestion', {'query': {'query_string': {'query': 'application test',
                            'default_operator': 'AND'}}, 'size': 0, 'aggs': {'country_publisher':
                            {'terms': {'field': 'index.country.exact', 'size': 100, 'order': {'_count': 'desc'}}}},
                                               'track_total_hits': True}, account=associate, additional_parameters={})
        assert res['hits']['total']["value"] == 0, res['hits']['total']["value"]

    def test_editor_application_query_notes(self):

        self.app_test.config['QUERY_ROUTE'] = SEARCH_ALL_QUERY_ROUTE

        app = self.get_application_with_notes()

        editor = models.Account(**AccountFixtureFactory.make_editor_source())
        editor.save(blocking=True)

        eg_source = EditorGroupFixtureFactory.make_editor_group_source(maned=editor.id)
        eg = models.EditorGroup(**eg_source)
        eg.set_name(app.editor_group)
        eg.save(blocking=True)

        qsvc = QueryService()

        res = qsvc.search('editor_query', 'suggestion', {'query': {'query_string': {'query': 'application test',
                            'default_operator': 'AND'}}, 'size': 0, 'aggs': {'country_publisher':
                            {'terms': {'field': 'index.country.exact', 'size': 100, 'order': {'_count': 'desc'}}}},
                                               'track_total_hits': True}, account=editor, additional_parameters={})
        assert res['hits']['total']["value"] == 0, res['hits']['total']["value"]

    def test_admin_application_query_notes(self):

        app = self.get_application_with_notes()

        med = models.Account(**AccountFixtureFactory.make_managing_editor_source())
        med.save(blocking=True)

        eg_source = EditorGroupFixtureFactory.make_editor_group_source(maned=med.id)
        eg = models.EditorGroup(**eg_source)
        eg.set_name(app.editor_group)
        eg.save(blocking=True)

        qsvc = QueryService()

        res = qsvc.search('admin_query', 'suggestion', {'query': {'query_string': {'query': 'application test',
                            'default_operator': 'AND'}}, 'size': 0, 'aggs': {'country_publisher':
                            {'terms': {'field': 'index.country.exact', 'size': 100, 'order': {'_count': 'desc'}}}},
                                               'track_total_hits': True}, account=med, additional_parameters={})
        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

    def test_journal_article_query_notes(self):

        self.app_test.config['QUERY_ROUTE'] = self.OLD_QUERY_ROUTE

        self.app_test.config['QUERY_FILTERS'] = self.OLD_QUERY_FILTERS

        self.article11 = models.Article(
            **ArticleFixtureFactory.make_article_source(pissn="1111-1111", eissn="2222-2222", doi="10.0000/article-11",
                                                        fulltext="https://www.article11.com"))
        self.article11.save(blocking=True)

        self.get_journal_with_notes()

        qsvc = QueryService()

        res = qsvc.search('query', 'journal,article', {'query': {'query_string':
                            {'query': 'application test','default_operator': 'AND'}},
                            'size': 0, 'track_total_hits': True}, account=None, additional_parameters={"ref":"fqw"})
        assert res['hits']['total']["value"] == 0, res['hits']['total']["value"]

    def test_article_query_ascci_folding(self):
        self.article12 = models.Article(
            **ArticleFixtureFactory.make_article_with_data({"bibjson": {"title": "I can’t really think in English"}}))
        self.article12.save(blocking=True)
        qsvc = QueryService()

        res = qsvc.search('query', 'article', MATCH_ALL_RAW_QUERY, account=None,
                          additional_parameters={})
        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

        res = qsvc.search('query', 'article', raw_query("I can't really think in English"),
                          account=None, additional_parameters={"ref": "fqw"})

        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

        res = qsvc.search('query', 'article', raw_query("I can’t really think in English"),
                          account=None, additional_parameters={"ref": "fqw"})

        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

    def test_journal_query_ascii_folding(self):
        self.journal = models.Journal(**JournalFixtureFactory.make_journal_with_data(title="I can’t really think in English"))
        self.journal.save(blocking=True)
        qsvc = QueryService()

        res = qsvc.search('query', 'journal', MATCH_ALL_RAW_QUERY, account=None,
                          additional_parameters={})
        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

        res = qsvc.search('query', 'journal', raw_query("I can't really think in English"),
                          account=None, additional_parameters={"ref": "fqw"})

        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

        res = qsvc.search('query', 'journal', raw_query("I can’t really think in English"),
                          account=None, additional_parameters={"ref": "fqw"})

        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

    def test_article_query_ascci_folding_data(self):
        self.article12 = models.Article(
            **ArticleFixtureFactory.make_article_with_data(title="Kadınlarının sağlık",
                                                           publisher_name="Ankara Üniversitesi",
                                                           abstract="Araştırma grubunu", country="Türkiye",
                                                           author="Sultan  GÜÇLÜ"))
        self.article12.save(blocking=True)
        qsvc = QueryService()

        res = qsvc.search('query', 'article', MATCH_ALL_RAW_QUERY, account=None,
                          additional_parameters={})
        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

        # check for title
        res = qsvc.search('query', 'article', raw_query("Kadinlarinin saglik"), account=None,
                          additional_parameters={"ref": "fqw"})

        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

        # echeck for publisher
        res = qsvc.search('query', 'article', raw_query("Ankara Universitesi"), account=None,
                          additional_parameters={"ref": "fqw"})

        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

        # check for abstract
        res = qsvc.search('query', 'article', raw_query("Arastırma grubunu"), account=None,
                          additional_parameters={"ref": "fqw"})

        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

        # check for country
        res = qsvc.search('query', 'article', raw_query("Turkiye"), account=None,
                          additional_parameters={"ref": "fqw"})

        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

        # check for author
        res = qsvc.search('query', 'article', raw_query("Sultan GUCLU"), account=None,
                          additional_parameters={"ref": "fqw"})

        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

    def test_journal_query_ascii_folding_data(self):
        self.journal = models.Journal(**JournalFixtureFactory
                                      .make_journal_with_data(title="Kadınlarının sağlık",
                                                              publisher_name="Ankara Üniversitesi",
                                                              country="Türkiye",
                                                              alternative_title="Dirasat: Shariía and Law Sciences"))
        self.journal.save(blocking=True)
        qsvc = QueryService()

        # check if journal exist
        res = qsvc.search('query', 'journal', MATCH_ALL_RAW_QUERY, account=None,
                          additional_parameters={})
        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

        # check for title search
        res = qsvc.search('query', 'journal', raw_query("Kadinlarinin saglik"), account=None,
                          additional_parameters={"ref": "fqw"})

        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

        # check for publisher name
        res = qsvc.search('query', 'journal', raw_query("Ankara Universitesi"), account=None,
                          additional_parameters={"ref": "fqw"})

        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

        # check for country
        res = qsvc.search('query', 'journal', raw_query("Turkiye"), account=None,
                          additional_parameters={"ref": "fqw"})

        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

        # check alternative title
        res = qsvc.search('query', 'journal', raw_query("Shariia"),
                          account=None, additional_parameters={})

        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

    def test_application_query_ascii_folding_data(self):
        acc = models.Account(**AccountFixtureFactory.make_managing_editor_source())
        application = models.Application(**ApplicationFixtureFactory
                                      .make_application_with_data(title="Kadınlarının sağlık",
                                                              publisher_name="Ankara Üniversitesi",
                                                              country="Türkiye", ))
        application.save(blocking=True)
        qsvc = QueryService()

        # check if journal exist
        res = qsvc.search('editor_query', 'suggestion', MATCH_ALL_RAW_QUERY, account=acc,
                          additional_parameters={})
        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

        # check for title search
        res = qsvc.search('editor_query', 'suggestion', raw_query("Kadinlarinin saglik"), account=acc,
                          additional_parameters={"ref": "fqw"})

        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

        # check for publisher name
        res = qsvc.search('editor_query', 'suggestion', raw_query("Ankara Universitesi"), account=acc,
                          additional_parameters={"ref": "fqw"})

        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

        # check for country
        res = qsvc.search('editor_query', 'suggestion', raw_query("Turkiye"), account=acc,
                          additional_parameters={"ref": "fqw"})

        assert res['hits']['total']["value"] == 1, res['hits']['total']["value"]

    def test_search__invalid_from(self):
        acc = models.Account(**AccountFixtureFactory.make_managing_editor_source())
        acc.save(blocking=True)
        query = {'query': {'bool': {'must': [{'term': {'es_type.exact': 'journal'}}],
                                    'filter': [{'term': {'admin.in_doaj': True}}]}},
                 'size': '10', 'from': '@@PQF0l',
                 'sort': [{'_score': {'order': 'desc'}}],
                 'track_total_hits': 'true'}
        with pytest.raises(RequestError):
            QueryService().search('admin_query', 'journal', query, account=acc, additional_parameters={})