import json
from collections import namedtuple
from unittest import TestCase
from unittest.mock import patch, MagicMock

from portality.lib import plausible

FakeResp = namedtuple('FakeResp', ['status_code'])


class TestLibPlausible(TestCase):
    def _create_assert_send_event_post_called(self, expected_goal):
        def _fn(*args, **kwargs):
            args[0].endswith('/api/event/')
            input_json = kwargs.get('json', {})
            assert input_json.get('name') == expected_goal
            assert 'url' in input_json
            assert 'domain' in input_json

        return _fn

    def _create_side_effect_post_resp(self, return_value, assert_input_fn_list=None):
        def _fn(*args, **kwargs):
            for assert_input_fn in assert_input_fn_list:
                assert_input_fn(*args, **kwargs)
            return return_value

        return _fn

    @patch.object(plausible.requests, 'post')
    def test_send_event__without_props_payload(self, post_mock: MagicMock):
        # prepare test data
        input_goal = 'test_goal'
        input_fake_resp = FakeResp(200)
        post_mock.side_effect = self._create_side_effect_post_resp(
            input_fake_resp,
            assert_input_fn_list=[
                self._create_assert_send_event_post_called(input_goal),
            ]
        )

        def input_on_completed(_resp):
            self.assertEqual(_resp, input_fake_resp)

        # tigger send_event
        plausible.send_event(input_goal, on_completed=input_on_completed)

    @patch.object(plausible.requests, 'post')
    def test_send_event__with_props_payload(self, post_mock: MagicMock):
        # prepare test data
        input_goal = 'test_goal'
        input_props_payload = {
            'aa': 'hihi',
            'bb': 'ggg',
        }
        input_fake_resp = FakeResp(200)

        def _assert_input(*args, **kwargs):
            input_json = kwargs.get('json', {})
            assert 'props' in input_json
            assert json.loads(input_json['props']) == input_props_payload

        post_mock.side_effect = self._create_side_effect_post_resp(
            input_fake_resp,
            assert_input_fn_list=[
                self._create_assert_send_event_post_called(input_goal),
                _assert_input,
            ]
        )

        def input_on_completed(_resp):
            self.assertEqual(_resp, input_fake_resp)

        # tigger send_event
        plausible.send_event(input_goal, on_completed=input_on_completed, **input_props_payload)
