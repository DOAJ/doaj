import base64
from unittest.mock import patch

from elasticsearch.exceptions import SerializationError

from doajtest.helpers import DoajTestCase
from portality.view import status as status_view


def basic_auth(username, password):
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


class TestStatusPing(DoajTestCase):
    """ /_status/ping is unauthenticated and reports whether the search cluster answers a ping """

    def test_01_ping_ok(self):
        with patch.object(status_view.es_connection, "ping", return_value=True), \
                self.app_test.test_client() as t_client:
            resp = t_client.get("/_status/ping")
        assert resp.status_code == 200, resp.status_code
        assert resp.data == b"OK"
        assert resp.headers["Cache-Control"] == "no-store"

    def test_02_ping_search_unreachable(self):
        with patch.object(status_view.es_connection, "ping", return_value=False), \
                self.app_test.test_client() as t_client:
            resp = t_client.get("/_status/ping")
        assert resp.status_code == 503, resp.status_code

    def test_03_ping_search_error(self):
        with patch.object(status_view.es_connection, "ping", side_effect=SerializationError("boom")), \
                self.app_test.test_client() as t_client:
            resp = t_client.get("/_status/ping")
        assert resp.status_code == 503, resp.status_code


class TestStatusAuth(DoajTestCase):
    """ /_status/ and /_status/stats require basic auth, and refuse everything if credentials aren't configured """

    @classmethod
    def create_app_patch(cls):
        return super().create_app_patch() | {
            "STATUS_BASIC_AUTH_USERNAME": "monitor",
            "STATUS_BASIC_AUTH_PASSWORD": "s3cret",
        }

    def test_01_stats_requires_auth(self):
        with self.app_test.test_client() as t_client:
            resp = t_client.get("/_status/stats")
        assert resp.status_code == 401, resp.status_code
        assert resp.headers["WWW-Authenticate"].startswith("Basic")

    def test_02_stats_wrong_credentials(self):
        with self.app_test.test_client() as t_client:
            resp = t_client.get("/_status/stats", headers=basic_auth("monitor", "wrong"))
        assert resp.status_code == 401, resp.status_code

    def test_03_stats_correct_credentials(self):
        with self.app_test.test_client() as t_client:
            resp = t_client.get("/_status/stats", headers=basic_auth("monitor", "s3cret"))
        assert resp.status_code == 200, resp.status_code
        assert "writable" in resp.get_json()

    def test_04_status_requires_auth(self):
        with self.app_test.test_client() as t_client:
            resp = t_client.get("/_status/")
        assert resp.status_code == 401, resp.status_code

    def test_05_ping_needs_no_auth(self):
        with patch.object(status_view.es_connection, "ping", return_value=True), \
                self.app_test.test_client() as t_client:
            resp = t_client.get("/_status/ping")
        assert resp.status_code == 200, resp.status_code

    def test_06_refuses_all_when_unconfigured(self):
        with patch.dict(self.app_test.config, {"STATUS_BASIC_AUTH_USERNAME": None,
                                               "STATUS_BASIC_AUTH_PASSWORD": None}), \
                self.app_test.test_client() as t_client:
            assert t_client.get("/_status/stats").status_code == 401
            assert t_client.get("/_status/stats", headers=basic_auth("", "")).status_code == 401
            assert t_client.get("/_status/stats", headers=basic_auth("None", "None")).status_code == 401

    def test_07_status_passes_credentials_to_app_machines(self):
        with patch.object(status_view.requests, "get", side_effect=RuntimeError("stop here")) as mock_get, \
                patch.dict(self.app_test.config, {"APP_MACHINES_INTERNAL_IPS": ["localhost:5050"]}), \
                self.app_test.test_client() as t_client:
            try:
                t_client.get("/_status/", headers=basic_auth("monitor", "s3cret"))
            except RuntimeError:
                pass
        assert mock_get.call_args.kwargs["auth"] == ("monitor", "s3cret"), mock_get.call_args

    def test_08_unreachable_app_machine_reported_not_500(self):
        # port 1 refuses connections, like a down app machine; the page must report it rather than crash
        with patch.dict(self.app_test.config, {"APP_MACHINES_INTERNAL_IPS": ["localhost:1"]}), \
                self.app_test.test_client() as t_client:
            resp = t_client.get("/_status/", headers=basic_auth("monitor", "s3cret"))
        assert resp.status_code == 200, resp.status_code
        res = resp.get_json()
        assert res["stable"] is False
        assert "1 APPS UNREACHABLE" in res["notes"], res["notes"]
        # a healthy search cluster must not flip stable back to True
        assert "indexes stable" in res["notes"], res["notes"]

    def test_09_string_and_dict_es_hosts(self):
        es_url = self.app_test.config["ELASTICSEARCH_HOSTS"][0]
        es_url = es_url if isinstance(es_url, str) else f"http://{es_url['host']}:{es_url['port']}"
        host, port = es_url.split("://")[1].rstrip("/").split(":")
        for hosts in ([es_url], [{"host": host, "port": int(port)}]):
            with patch.dict(self.app_test.config, {"ELASTICSEARCH_HOSTS": hosts, "APP_MACHINES_INTERNAL_IPS": []}), \
                    self.app_test.test_client() as t_client:
                res = t_client.get("/_status/", headers=basic_auth("monitor", "s3cret")).get_json()
            assert res["ping"]["indices"] == {es_url.rstrip("/"): 200}, (hosts, res["ping"]["indices"])
            assert "indexes stable" in res["notes"], res["notes"]

    def test_10_unreachable_search_cluster_reported_not_500(self):
        with patch.dict(self.app_test.config, {"ELASTICSEARCH_HOSTS": ["http://localhost:1"],
                                               "APP_MACHINES_INTERNAL_IPS": []}), \
                self.app_test.test_client() as t_client:
            resp = t_client.get("/_status/", headers=basic_auth("monitor", "s3cret"))
        assert resp.status_code == 200, resp.status_code
        res = resp.get_json()
        assert res["stable"] is False
        assert "1 INDEXES UNREACHABLE" in res["notes"] and "CLUSTER UNSTABLE" in res["notes"], res["notes"]
