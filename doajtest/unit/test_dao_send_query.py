from unittest import TestCase
from unittest.mock import patch, MagicMock

from elasticsearch.exceptions import RequestError, TransportError, ConnectionTimeout, NotFoundError

from doajtest.helpers import DoajTestCase
from portality import dao, models
from portality.bll.services.query import QueryService, Query
from portality.core import app

PARSE_ERROR_INFO = {"error": {"root_cause": [{"type": "parse_exception", "reason": "Encountered \" \"]\" \"] \"\""}],
                              "type": "search_phase_execution_exception"}, "status": 400}
MAPPING_MISSING_INFO = {"error": {"root_cause": [{"type": "query_shard_exception",
                                                  "reason": "No mapping found for [relevant] in order to sort on"}]}}


class TestSendQueryRetries(DoajTestCase):
    """ dao.send_query must not retry requests that ES rejected as bad (4xx), but should still retry transient errors.
    The DAO's ES client is mocked, so these tests check send_query's retry behaviour rather than ES itself. """

    def setUp(self):
        super().setUp()
        self.es_patch = patch.object(dao, "ES")
        self.sleep_patch = patch.object(dao.time, "sleep")
        # the test config sets ES_RETRY_HARD_LIMIT to 0 (no retries); restore the production default for these tests
        self.config_patch = patch.dict(self.app_test.config, {"ES_RETRY_HARD_LIMIT": 1000})
        self.es = self.es_patch.start()
        self.sleep = self.sleep_patch.start()
        self.config_patch.start()

    def tearDown(self):
        self.es_patch.stop()
        self.sleep_patch.stop()
        self.config_patch.stop()
        super().tearDown()

    def test_01_query_parse_error_not_retried(self):
        self.es.search.side_effect = RequestError(400, "search_phase_execution_exception", PARSE_ERROR_INFO)
        with self.assertRaises(RequestError):
            models.Article.send_query({"query": {"query_string": {"query": "[foo]"}}})
        assert self.es.search.call_count == 1
        self.sleep.assert_not_called()

    def test_02_other_client_errors_not_retried(self):
        self.es.search.side_effect = NotFoundError(404, "index_not_found_exception", {"status": 404})
        with self.assertRaises(NotFoundError):
            models.Article.send_query({"query": {"match_all": {}}})
        assert self.es.search.call_count == 1

    def test_03_mapping_missing_still_raised_immediately(self):
        self.es.search.side_effect = RequestError(400, "search_phase_execution_exception", MAPPING_MISSING_INFO)
        with self.assertRaises(dao.ESMappingMissingError):
            models.Article.send_query({"query": {"match_all": {}}})
        assert self.es.search.call_count == 1

    def test_04_server_error_retried_up_to_limit(self):
        self.es.search.side_effect = TransportError(503, "search_phase_execution_exception", {"status": 503})
        with self.assertRaises(TransportError):
            models.Article.send_query({"query": {"match_all": {}}}, retry=3)
        assert self.es.search.call_count == 3

    def test_05_too_many_requests_retried(self):
        self.es.search.side_effect = [TransportError(429, "es_rejected_execution_exception", {"status": 429}),
                                      {"hits": {"hits": []}}]
        assert models.Article.send_query({"query": {"match_all": {}}}) == {"hits": {"hits": []}}
        assert self.es.search.call_count == 2

    def test_06_timeout_retried(self):
        self.es.search.side_effect = [ConnectionTimeout("TIMEOUT", "timed out", None), {"hits": {"hits": []}}]
        assert models.Article.send_query({"query": {"match_all": {}}}) == {"hits": {"hits": []}}
        assert self.es.search.call_count == 2

    def test_07_query_passes_send_kwargs(self):
        self.es.search.return_value = {"hits": {"hits": []}}
        models.Article.query(q={"query": {"match_all": {}}}, send_kwargs={"request_cache": True})
        assert self.es.search.call_args.kwargs["request_cache"] is True


class TestQueryServiceSendKwargs(TestCase):
    """ QueryService.search should retry sparingly, and use the ES request cache only on routes configured for it """

    def _search_with_cfg(self, cfg):
        dao_klass = MagicMock()
        dao_klass.query.return_value = {"hits": {"hits": [], "total": {"value": 0}}}
        qsvc = QueryService()
        with patch.object(qsvc, "_get_config_for_search", return_value=cfg), \
                patch.object(qsvc, "_get_dao_klass", return_value=dao_klass), \
                patch.object(qsvc, "_get_query", return_value=Query({"query": {"match_all": {}}})):
            qsvc.search("query", "article", {"query": {"match_all": {}}}, account=None, additional_parameters={})
        return dao_klass.query.call_args.kwargs["send_kwargs"]

    def test_01_request_cache_enabled_by_route(self):
        send_kwargs = self._search_with_cfg({"request_cache": True})
        assert send_kwargs == {"retry": app.config.get("QUERY_SERVICE_ES_RETRIES", 3), "request_cache": True}

    def test_02_request_cache_off_by_default(self):
        send_kwargs = self._search_with_cfg({})
        assert "request_cache" not in send_kwargs
        assert send_kwargs["retry"] == app.config.get("QUERY_SERVICE_ES_RETRIES", 3)
