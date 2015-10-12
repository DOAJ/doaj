from portality.api.v1.crud.common import CrudApi
from portality.api.v1 import Api401Error, Api400Error, Api404Error, Api403Error
from portality.api.v1.data_objects import IncomingApplication, OutgoingApplication
from portality.lib import dataobj
from datetime import datetime
from portality import models

from copy import deepcopy

class ApplicationsCrudApi(CrudApi):

    @classmethod
    def _swag_with_full_body(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['tags'].append('CRUD')
        template['responses']['200']['schema']['title'] = 'Application schema'
        template['responses']['200']['schema']['properties'] = IncomingApplication().struct_to_swag()
        return template

    @classmethod
    def create_swag(cls):
        return cls._swag_with_full_body()

    @classmethod
    def create(cls, data, account):
        # as long as authentication (in the layer above) has been successful, and the account exists, then
        # we are good to proceed
        if account is None:
            raise Api401Error()

        # first thing to do is a structural validation, but instantiating the data object
        try:
            ia = IncomingApplication(data)
        except dataobj.DataStructureException as e:
            raise Api400Error(e.message)

        # if that works, convert it to a Suggestion object
        ap = ia.to_application_model()

        # if the caller set the id, created_date or last_updated, then can the data, and apply our
        # own values (note that last_updated will get overwritten anyway)
        ap.set_id()
        ap.set_created()

        # now augment the suggestion object with all the additional information it requires
        #
        # suggester name and email from the user account
        ap.set_suggester(account.name, account.email)

        # suggested_on right now
        ap.suggested_on = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # initial application status for workflow
        ap.set_application_status('pending')

        # set the owner to the current account
        ap.set_owner(account.id)

        # they are not allowed to set "subject"
        ap.bibjson().remove_subjects()

        # finally save the new application, and return to the caller
        ap.save()
        return ap

    @classmethod
    def retrieve_swag(cls):
        return cls._swag_with_full_body()

    @classmethod
    def retrieve(cls, id, account):
        # as long as authentication (in the layer above) has been successful, and the account exists, then
        # we are good to proceed
        if account is None:
            raise Api401Error()

        # is the application id valid
        ap = models.Suggestion.pull(id)
        if ap is None:
            raise Api404Error()

        # is the current account the owner of the application
        # if not we raise a 404 because that id does not exist for that user account.
        if ap.owner != account.id:
            raise Api404Error()

        # if we get to here we're going to give the user back the application
        oa = OutgoingApplication.from_model(ap)
        return oa

    @classmethod
    def update_swag(cls):
        return cls._swag_with_full_body()

    @classmethod
    def update(cls, id, data, account):
        # as long as authentication (in the layer above) has been successful, and the account exists, then
        # we are good to proceed
        if account is None:
            raise Api401Error()

        # now see if there's something for us to update
        ap = models.Suggestion.pull(id)
        if ap is None:
            raise Api404Error()

        # is the current account the owner of the application
        # if not we raise a 404 because that id does not exist for that user account.
        if ap.owner != account.id:
            raise Api404Error()

        # now we need to determine whether the records is in an editable state, which means its application_status
        # must be from an allowed list
        if ap.application_status not in ["rejected", "submitted", "pending"]:
            raise Api403Error()

        # next thing to do is a structural validation of the replacement data, by instantiating the object
        try:
            ia = IncomingApplication(data)
        except dataobj.DataStructureException as e:
            raise Api400Error(e.message)

        # if that works, convert it to a Suggestion object bringing over everything outside the
        # incoming application from the original application
        new_ap = ia.to_application_model(ap)

        # we need to ensure that any properties of the existing application that aren't allowed to change
        # are copied over
        new_ap.set_id(id)
        new_ap.set_created(ap.created_date)
        new_ap.set_owner(ap.owner)
        new_ap.set_suggester(ap.suggester['name'], ap.suggester['email'])
        new_ap.suggested_on = ap.suggested_on
        new_ap.bibjson().set_subjects(ap.bibjson().subjects())

        # reset the status on the application
        new_ap.set_application_status('pending')

        # finally save the new application, and return to the caller
        new_ap.save()
        return new_ap

    @classmethod
    def delete_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['tags'].append('CRUD')
        template["parameters"].append(
            {
                "description": "<div class=\"search-query-docs\">DOAJ application ID. E.g. 4cf8b72139a749c88d043129f00e1b07 .</div>",
                "required": True,
                "type": "string",
                "name": "application_id",
                "in": "path"
            }
        )
        del template['responses']['200']
        template['responses']['204'] = {"description": "OK (Request succeeded), No Content"}
        return template

    @classmethod
    def delete(cls, id, account):
        # as long as authentication (in the layer above) has been successful, and the account exists, then
        # we are good to proceed
        if account is None:
            raise Api401Error()

        # now see if there's something for us to delete
        ap = models.Suggestion.pull(id)
        if ap is None:
            raise Api404Error()

        # is the current account the owner of the application
        # if not we raise a 404 because that id does not exist for that user account.
        if ap.owner != account.id:
            raise Api404Error()

        # now we need to determine whether the records is in an editable state, which means its application_status
        # must be from an allowed list
        if ap.application_status not in ["rejected", "submitted", "pending"]:
            raise Api403Error()

        # issue the delete (no record of the delete required)
        ap.delete()
