import json

from doajtest import fixtures
from doajtest.helpers import DoajTestCase, patch_config
from portality.app import setup_dev_log
from portality.bll import DOAJ
from portality.core import app
from portality.models import Account

api_rate_serv = DOAJ.apiRateService()


def send_test_req(client, api_key=None):
    journal_id = '112233'
    url = f'/api/journals/{journal_id}'
    if api_key is not None:
        url += f'?api_key={api_key}'
    return client.get(url)


def assert_is_too_many_requests(resp):
    data = json.loads(resp.data)
    assert data['status'] == 'too_many_requests'
    assert resp.status_code == 429


def assert_not_too_many_requests(resp):
    data = json.loads(resp.data)
    assert data['status'] != 'too_many_requests'
    assert resp.status_code != 429


class TestApiRateLimited(DoajTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.originals = patch_config(
            app,
            {
                'RATE_LIMITS_PER_MIN_DEFAULT': 10,
                'RATE_LIMITS_PER_MIN_T2 ': 1000,
            })
        setup_dev_log()


    def setUp(self):
        super().setUp()
        self.t2_user = Account(**fixtures.accounts.PUBLISHER_SOURCE)
        self.t2_user.generate_api_key()
        self.t2_user.add_role('api_rate_t2')

        self.normal_user = Account(**fixtures.accounts.PUBLISHER_B_SOURCE)
        self.normal_user.generate_api_key()

        Account.save_all([self.normal_user, self.t2_user])
        Account.refresh()

    def send_multi_req_more_than_default_limit(self, api_key=None):
        with self.app_test.test_client() as t_client:
            for _ in range(app.config['RATE_LIMITS_PER_MIN_DEFAULT'] + 5):
                resp = send_test_req(t_client, api_key=api_key)
        return resp

    def send_one_req(self, api_key=None):
        with self.app_test.test_client() as t_client:
            resp = send_test_req(t_client, api_key=api_key)
        return resp

    def test_normal__no_api_key(self):
        resp = self.send_one_req()
        assert_not_too_many_requests(resp)

    def test_normal__normal_user(self):
        resp = self.send_one_req(api_key=self.normal_user.api_key)
        assert_not_too_many_requests(resp)

    def test_normal__t2_user(self):
        resp = self.send_one_req(api_key=self.t2_user.api_key)
        assert_not_too_many_requests(resp)

    def test_multi_req__too_many_requests__no_api_key(self):
        resp = self.send_multi_req_more_than_default_limit()
        assert_is_too_many_requests(resp)

    def test_multi_req__too_many_requests__normal_user(self):
        resp = self.send_multi_req_more_than_default_limit(api_key=self.normal_user.api_key)
        assert_is_too_many_requests(resp)

    def test_multi_req__normal__t2_user(self):
        resp = self.send_multi_req_more_than_default_limit(api_key=self.t2_user.api_key)
        assert_not_too_many_requests(resp)
