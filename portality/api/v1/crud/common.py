from portality.api.v1.common import Api, ERROR_TEMPLATE, CREATED_TEMPLATE

from copy import deepcopy


class CrudApi(Api):
    SWAG_TEMPLATE = {
        "responses": {},
        "parameters": [],
        "tags": []
    }
    R200 = {"schema": {}}
    R201 = {"schema": {"properties": CREATED_TEMPLATE, "description": "Resource created successfully, response contains the new resource ID and location."}}
    R204 = {"description": "OK (Request succeeded), No Content"}
    R400 = {"schema": {"properties": ERROR_TEMPLATE}, "description": "Bad Request. Your request body was missing a required field, or the data in one of the fields did not match the schema above (e.g. string of latin letters in an integer field). See the \"error\" part of the response for details."}
    R401 = {"schema": {"properties": ERROR_TEMPLATE}, "description": "Access to this route/resource requires authentication, but you did not provide any credentials."}
    R403 = {"schema": {"properties": ERROR_TEMPLATE}, "description": "Access to this route/resource requires authentication, and you provided the wrong credentials. This includes situations where you are authenticated successfully via your API key, but you are not the owner of a specific resource and are therefore barred from updating/deleting it."}
    R404 = {"schema": {"properties": ERROR_TEMPLATE}, "description": "Resource not found"}

    SWAG_API_KEY_REQ_PARAM = {
        "description": "<div class=\"search-query-docs\"> Go to the top right of the page and click your username. If you have generated an API key already, it will appear under your name. If not, click the Generate API Key button. Accounts are not available to the public. <a href=\"#intro_auth\">More details</a></div>",
        "required": True,
        "type": "string",
        "name": "api_key",
        "in": "query"
    }

    @classmethod
    @property
    def SWAG_TAG(cls):
        raise RuntimeError('You must override this class constant in every subclass.')

    @classmethod
    def _add_swag_tag(cls, template):
        template['tags'].append(cls.SWAG_TAG)
        return template

    @classmethod
    def _add_api_key(cls, template, optional=False):
        api_key_param = deepcopy(cls.SWAG_API_KEY_REQ_PARAM)
        if optional:
            api_key_param['required'] = False
            api_key_param['description'] = "<div class=\"search-query-docs\"><em>Note this parameter is optional for this route - you could, but don't have to supply a key. Doing so grants you access to records of yours that are not public, in addition to all public records.</em> Go to the top right of the page and click your username. If you have generated an API key already, it will appear under your name. If not, click the Generate API Key button. Accounts are not available to the public. <a href=\"#intro_auth\">More details</a></div>"
        template["parameters"].insert(0, api_key_param)
        return template

    @classmethod
    def _build_swag_response(cls, template):
        cls._add_swag_tag(template)
        if hasattr(cls, 'API_KEY_CAN_BE_OPTIONAL'):
            cls._add_api_key(template, optional=cls.API_KEY_CAN_BE_OPTIONAL)
        return template