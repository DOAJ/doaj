from portality.api.v2.crud.common import CrudApi
from portality.api.v2.common import Api404Error, Api400Error, Api403Error
from portality.api.v2.crud import ApplicationsCrudApi
from copy import deepcopy

class ApplicationsBulkApi(CrudApi):

    API_KEY_OPTIONAL = False
    SWAG_TAG = 'Bulk API'
    SWAG_DELETE_PARAM = {
        "description": "<div class=\"search-query-docs\">List of DOAJ application IDs to be deleted. You must own all of the ids, and they must all not have entered the DOAJ workflow yet, or none of them will be processed.e.g. [4cf8b72139a749c88d043129f00e1b07, 8e896b60-35f1-4cd3-b3f9-07f7f29d8a98].</div>",
        "required": True,
        "type": "string",
        "name": "application_ids",
        "in": "body"
    }
    SWAG_APPLICATION_BODY_PARAM = {
        "description": "<div class=\"search-query-docs\">List of Application JSON objects that you would like to create. Each element of the list should comply with the schema displayed in the <a href=\"/api/v1/docs#CRUD_Applications_get_api_v1_application_application_id\"> GET (Retrieve) an application route</a>.</div>",
        "required": True,
        "type": "string",
        "name": "application_json",
        "in": "body"
    }

    @classmethod
    def create_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['parameters'].append(cls.SWAG_APPLICATION_BODY_PARAM)
        template['responses']['201'] = cls.R201_BULK
        template['responses']['400'] = cls.R400
        return cls._build_swag_response(template)

    @classmethod
    def create(cls, applications, account):
        # we run through create twice, once as a dry-run and the second time
        # as the real deal
        for a in applications:
            ApplicationsCrudApi.create(a, account, dry_run=True)

        ids = []
        for a in applications:
            n = ApplicationsCrudApi.create(a, account)
            ids.append(n.id)

        return ids

    @classmethod
    def delete_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['parameters'].append(cls.SWAG_DELETE_PARAM)
        template['responses']['204'] = cls.R204
        template['responses']['400'] = cls.R400
        return cls._build_swag_response(template)

    @classmethod
    def delete(cls, application_ids, account):
        # we run through delete twice, once as a dry-run and the second time
        # as the real deal
        for id in application_ids:
            try:
                ApplicationsCrudApi.delete(id, account, dry_run=True)
            except Api404Error as e:
                raise Api400Error("Id {x} does not exist or does not belong to this user account".format(x=id))
            except Api403Error as e:
                raise Api400Error("Id {x} is not in a state which allows it to be deleted".format(x=id))

        for id in application_ids:
            ApplicationsCrudApi.delete(id, account)
