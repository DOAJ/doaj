from portality.api.v1.common import Api


class CrudApi(Api):
    SWAG_TEMPLATE = {
        "responses": {
            "200": {
                "schema": {}
            },
            "400": {
                "description": "Bad Request"
            }
        },
        "parameters": [],
        "tags": []
    }