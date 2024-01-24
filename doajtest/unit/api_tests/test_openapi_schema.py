import json

import openapi_spec_validator

from doajtest.helpers import DoajTestCase
from portality.util import url_for


class TestDoajOpenapiSchema(DoajTestCase):

    def test_validate(self):
        with self.app_test.test_client() as t_client:
            resp = t_client.get(url_for('api.api_spec'))
            api_json = json.loads(resp.data)
        openapi_spec_validator.validate(api_json)
