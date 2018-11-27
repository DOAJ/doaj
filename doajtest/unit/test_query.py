from portality import models

from doajtest.fixtures import AccountFixtureFactory, ArticleFixtureFactory
from doajtest.helpers import DoajTestCase

from portality.bll.services.query import QueryService, Query
from portality.bll import exceptions

QUERY_ROUTE = {
    "query" : {
        "article" : {
            "auth" : False,
            "role" : None,
            "query_filters" : ["only_in_doaj"],
            "result_filters" : ["public_result_filter"],
            "dao" : "portality.models.Article"
        }
    },
    "publisher_query" : {
        "journal" : {
            "auth" : True,
            "role" : "publisher",
            "query_filters" : ["owner", "only_in_doaj"],
            "result_filters" : ["publisher_result_filter"],
            "dao" : "portality.models.Journal"
        }
    },
    "admin_query" : {
        "journal" : {
            "auth" : True,
            "role" : "admin",
            "dao" : "portality.models.Journal"
        }
    },
    "api_query" : {
        "journal" : {
            "auth" : False,
            "role" : None,
            "query_filters" : ["only_in_doaj", "public_source"],
            "dao" : "portality.models.Journal"
        }
    }
}

QUERY_FILTERS = {
    # query filters
    "only_in_doaj" : "portality.lib.query_filters.only_in_doaj",
    "owner" : "portality.lib.query_filters.owner",

    # result filters
    "public_result_filter" : "portality.lib.query_filters.public_result_filter",

    # source filter
    "public_source": "portality.lib.query_filters.public_source"
}

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

    def test_01_auth(self):
        with self.app_test.test_client() as t_client:
            response = t_client.get('/query/journal')  # not in the settings above
            assert response.status_code == 403, response.status_code

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

    def test_02_query_gen(self):
        q = Query()
        assert q.as_dict() == {"query": {"match_all": {}}}, q.as_dict()
        q.convert_to_filtered()
        assert q.as_dict() == {'query': {'filtered': {'filter': {}, 'query': {'match_all': {}}}}}, q.as_dict()

        q = Query(filtered=True)
        assert q.as_dict() == {"query": {"match_all": {}}}, q.as_dict()
        q.convert_to_filtered()
        assert q.as_dict() == {"query": {"match_all": {}}}  # unchanged due to filtered=True asserting it's already filtered

        q = Query()
        q.add_must({"term": {"admin.in_doaj": True}})
        assert q.as_dict() == {'query': {'filtered': {'filter': {'bool': {'must': [{'term': {'admin.in_doaj': True}}]}}, 'query': {'match_all': {}}}}}, q.as_dict()

        q = Query()
        q.clear_match_all()
        assert q.as_dict() == {'query': {}}, q.as_dict()

        q = Query()
        q.add_include("last_updated")
        assert q.as_dict() == {"query": {"match_all": {}},"_source": {"include": ["last_updated"]}}, q.as_dict()

        q = Query()
        q.add_include(["last_updated", "id"])
        assert q.as_dict() == {"query": {"match_all": {}},"_source": {"include": ["last_updated", "id"]}}, q.as_dict()


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

        assert q.as_dict() == {"query": {"match_all": {}}}, q.as_dict()
        qsvc._pre_filter_search_query(cfg, q)
        assert q.as_dict() == {'query': {'filtered': {'filter': {'bool': {'must': [{'term': {'admin.in_doaj': True}}]}}}}}, q.as_dict()

    def test_05_post_filter_search_results(self):
        # The config above says that the public_result_filter should run on the results. That should delete admin.publisher_record_id.
        # We take a fake result set with the secret info in, run the results filters and expect to have the data cleaned.
        # We are testing that the mechanism that runs post filters works, the idea is not to test public_result_filter specifically.
        qsvc = QueryService()
        cfg = qsvc._get_config_for_search('query', 'article', account=None)

        res = {
          "hits": {
            "hits": [
              { "_type": "article", "_source": { "admin": { "seal": False, "publisher_record_id" : "some_identifier"}, "bibjson": {}}},
              { "_type": "article", "_source": { "admin": { "seal": False, "publisher_record_id" : "some_identifier"}, "bibjson": {}}},
              { "_type": "article", "_source": { "admin": { "seal": False, "publisher_record_id" : "some_identifier"}, "bibjson": {}}}
            ],
            "total": 3
          }
        }

        res = qsvc._post_filter_search_results(cfg, res)

        assert res == {
          "hits": {
            "hits": [
              { "_type": "article", "_source": { "admin": { "seal": False }, "bibjson": {}}},
              { "_type": "article", "_source": { "admin": { "seal": False }, "bibjson": {}}},
              { "_type": "article", "_source": { "admin": { "seal": False }, "bibjson": {}}}
            ],
            "total": 3
          }
        }

    def test_06_get_query(self):
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
        expected_result = {'query':
                    {'filtered': {
                        'filter': {'bool': {'must': [{'term': {'admin.in_doaj': True}}]}},
                        'query': {'query_string': {'query': '*', 'default_operator': 'AND'}}}
                    },
                    '_source': {'include': ['last_updated', 'admin.ticked', 'created_date', 'admin.seal', 'id', 'bibjson']},
                    'from': 0, 'size': 100}
        q_but_source = without_keys(query.as_dict(), ['_source'])
        r_but_source = without_keys(expected_result, ['_source'])
        assert q_but_source == r_but_source, q_but_source
        assert len(query.as_dict().get('_source', {}).get('include',[])) == len(expected_result['_source']['include'])
        assert query.as_dict().get('_source', []).get('include',[]).sort() == expected_result['_source']['include'].sort()

    def test_07_get_dao_klass(self):
        qsvc = QueryService()
        cfg = qsvc._get_config_for_search('query', 'article', account=None)
        dao_klass = qsvc._get_dao_klass(cfg)
        assert isinstance(dao_klass, models.Article) == True

    def test_08_search(self):
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
        assert res['hits']['total'] == 3, res['hits']['total']

        for hit in res['hits']['hits']:
            am = models.Article(**hit)
            assert am.publisher_record_id() is None, am.publisher_record_id()
