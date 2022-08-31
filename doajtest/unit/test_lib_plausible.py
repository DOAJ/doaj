import json
from collections import namedtuple
from unittest import TestCase
from unittest.mock import patch, MagicMock

import requests

from portality.lib import plausible

FakeResp = namedtuple('FakeResp', ['status_code'])


class TestLibPlausible(TestCase):
    def _assert_send_event_post_called(self, post_mock, expected_goal):
        post_mock.call_args.args[0].endswith('/api/event/')
        input_json = post_mock.call_args.kwargs.get('json', {})
        self.assertEqual(input_json.get('name'), expected_goal)
        self.assertIn('url', input_json)
        self.assertIn('domain', input_json)

    @patch.object(plausible.requests, 'post')
    def test_send_event__without_props_payload(self, post_mock: MagicMock):
        # prepare test data
        input_goal = 'test_goal'
        input_fake_resp = FakeResp(200)
        post_mock.return_value = input_fake_resp

        def input_on_completed(_resp):
            self.assertEqual(_resp, input_fake_resp)

        # tigger send_event
        plausible.send_event(input_goal, on_completed=input_on_completed)

        self._assert_send_event_post_called(post_mock, input_goal)

    @patch.object(plausible.requests, 'post')
    def test_send_event__with_props_payload(self, post_mock: MagicMock):
        # prepare test data
        input_goal = 'test_goal'
        input_props_payload = {
            'aa': 'hihi',
            'bb': 'ggg',
        }
        input_fake_resp = FakeResp(200)
        post_mock.return_value = input_fake_resp

        def input_on_completed(_resp):
            self.assertEqual(_resp, input_fake_resp)

        # tigger send_event
        plausible.send_event(input_goal, on_completed=input_on_completed, **input_props_payload)

        # assert
        self._assert_send_event_post_called(post_mock, input_goal)
        result_json = post_mock.call_args.kwargs.get('json', {})
        self.assertIn('props', result_json)
        self.assertEqual(json.loads(result_json['props']),
                         input_props_payload)
