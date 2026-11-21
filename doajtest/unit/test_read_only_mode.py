"""
Read-only mode (~~ReadOnlyMode:Feature~~): the write_required decorator, and which routes it blocks.

GET is allowed through by default, so any route whose GET shows a form that leads to a write (or whose GET itself
writes) must use write_required(allowed_methods=set()); otherwise users fill in the form and only find out on
submit, or are told a change happened when SCRIPTS_READ_ONLY_MODE silently skipped it.
"""
from portality import models
from portality.app import app  # noqa - importing registers the routes
from portality.decorators import write_required
from portality.util import patch_config

from doajtest.fixtures import AccountFixtureFactory
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from doajtest.helpers import DoajTestCase, login

READ_ONLY_PAGE = b"Down for maintenance"

# write_required routes which may still be opened with GET in read-only mode, because their GET neither writes nor
# shows a form leading to a write. Any other write_required route that accepts GET must block it.
GET_ALLOWED_IN_READ_ONLY = {
    "doajservices.export_article_ris",  # builds an RIS download, writes nothing
}


def _view():
    return "view ran"


class TestReadOnlyMode(DoajTestCase):

    def setUp(self):
        super().setUp()
        self.read_only_originals = patch_config(app, {"READ_ONLY_MODE": False, "SCRIPTS_READ_ONLY_MODE": False})

    def tearDown(self):
        patch_config(app, self.read_only_originals)
        super().tearDown()

    @staticmethod
    def _set_read_only(on):
        app.config["READ_ONLY_MODE"] = on
        app.config["SCRIPTS_READ_ONLY_MODE"] = on

    @staticmethod
    def _call(view, method):
        with app.test_request_context("/", method=method):
            return view()

    def test_01_everything_runs_when_not_read_only(self):
        for decorated in (write_required()(_view), write_required(allowed_methods=set())(_view), write_required(api=True)(_view)):
            for method in ("GET", "POST", "DELETE"):
                with self.subTest(method=method):
                    assert self._call(decorated, method) == "view ran"

    def test_02_default_allows_get_but_blocks_writes(self):
        self._set_read_only(True)
        decorated = write_required()(_view)
        assert self._call(decorated, "GET") == "view ran"
        for method in ("POST", "PUT", "DELETE"):
            with self.subTest(method=method):
                resp = self._call(decorated, method)
                assert resp != "view ran"
                assert READ_ONLY_PAGE.decode() in resp

    def test_03_empty_allowed_methods_blocks_get_too(self):
        self._set_read_only(True)
        decorated = write_required(allowed_methods=set())(_view)
        for method in ("GET", "POST"):
            with self.subTest(method=method):
                resp = self._call(decorated, method)
                assert resp != "view ran"
                assert READ_ONLY_PAGE.decode() in resp

    def test_04_api_routes_get_a_503(self):
        self._set_read_only(True)
        resp = self._call(write_required(api=True)(_view), "POST")
        assert resp.status_code == 503
        assert resp.mimetype == "application/json"
        assert b"maintenance" in resp.data

    def test_05_scripts_raise_outside_a_request(self):
        self._set_read_only(True)
        decorated = write_required(script=True)(_view)
        with self.assertRaises(RuntimeError):
            decorated()

    def test_06_allowed_methods_are_recorded_on_the_view(self):
        assert write_required()(_view)._write_allowed_methods == {"GET", "HEAD", "OPTIONS"}
        assert write_required(allowed_methods=set())(_view)._write_allowed_methods == set()

    def test_07_get_capable_write_routes_block_get_in_read_only_mode(self):
        """ Guards against adding a form route with a plain write_required() """
        checked = 0
        for rule in app.url_map.iter_rules():
            view = app.view_functions.get(rule.endpoint)
            if not getattr(view, "_write_required", False) or "GET" not in rule.methods:
                continue
            checked += 1
            with self.subTest(rule=rule.rule, endpoint=rule.endpoint):
                allowed = view._write_allowed_methods
                if rule.endpoint in GET_ALLOWED_IN_READ_ONLY:
                    assert "GET" in allowed
                else:
                    assert "GET" not in allowed, (
                        f"{rule.rule} ({rule.endpoint}) accepts GET and is write_required, but read-only mode lets GET "
                        f"through - use write_required(allowed_methods=set()), or add it to GET_ALLOWED_IN_READ_ONLY "
                        f"if its GET neither writes nor leads to a write")
        assert checked > 0
        # every allowlisted endpoint should still exist, so the list doesn't go stale
        endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
        assert GET_ALLOWED_IN_READ_ONLY <= endpoints

    def test_08_forms_show_the_read_only_page_as_soon_as_they_are_opened(self):
        with app.test_client() as client:
            for path in ("/apply/", "/en/apply/", "/account/register", "/account/forgot"):
                with self.subTest(path=path, read_only=False):
                    self._set_read_only(False)
                    resp = client.get(path, follow_redirects=True)
                    assert READ_ONLY_PAGE not in resp.data
                with self.subTest(path=path, read_only=True):
                    self._set_read_only(True)
                    # /apply/ redirects to the locale-prefixed /en/apply/ first
                    resp = client.get(path, follow_redirects=True)
                    assert resp.status_code == 200
                    assert "login" not in resp.request.path
                    assert READ_ONLY_PAGE in resp.data

            # logging in to read is still possible
            resp = client.get("/account/login", follow_redirects=True)
            assert resp.status_code == 200
            assert READ_ONLY_PAGE not in resp.data

    def test_09_publisher_delete_by_get_is_refused_and_the_draft_kept(self):
        """ Regression: this GET route used to report a delete that SCRIPTS_READ_ONLY_MODE had silently skipped """
        pwd = "password123"
        acc = models.Account(**AccountFixtureFactory.make_publisher_source())
        acc.set_password(pwd)
        acc.save(blocking=True)

        draft = models.DraftApplication(**ApplicationFixtureFactory.make_application_source())
        draft.set_id(draft.makeid())
        draft.set_application_status("draft")
        draft.set_owner(acc.id)
        draft.save(blocking=True)

        with app.test_client() as client:
            resp = login(client, acc.email, pwd)
            assert resp.status_code == 200

            self._set_read_only(True)
            resp = client.get(f"/publisher/application/{draft.id}/delete")
            assert resp.status_code == 200, "should render the read-only page, not redirect to 'application deleted'"
            assert READ_ONLY_PAGE in resp.data

        self._set_read_only(False)
        assert models.DraftApplication.pull(draft.id) is not None
