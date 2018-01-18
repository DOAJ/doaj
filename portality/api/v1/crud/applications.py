from portality.api.v1.crud.common import CrudApi
from portality.api.v1 import Api401Error, Api400Error, Api404Error, Api403Error, Api409Error
from portality.api.v1.data_objects import IncomingApplication, OutgoingApplication
from portality.lib import dataobj
from datetime import datetime
from portality import models

from portality.bll import DOAJ
from portality.bll.exceptions import AuthoriseException
from portality import lock
from portality.formcontext import formcontext, xwalk
from werkzeug.datastructures import MultiDict

from copy import deepcopy

class ApplicationsCrudApi(CrudApi):

    API_KEY_OPTIONAL = False
    SWAG_TAG = 'CRUD Applications'
    SWAG_ID_PARAM = {
        "description": "<div class=\"search-query-docs\">DOAJ application ID. E.g. 4cf8b72139a749c88d043129f00e1b07 .</div>",
        "required": True,
        "type": "string",
        "name": "application_id",
        "in": "path"
    }
    SWAG_APPLICATION_BODY_PARAM = {
        "description": "<div class=\"search-query-docs\">Application JSON that you would like to create or update. The contents should comply with the schema displayed in the <a href=\"/api/v1/docs#CRUD_Applications_get_api_v1_application_application_id\"> GET (Retrieve) an application route</a>. Partial updates are not allowed, you have to supply the full JSON.</div>",
        "required": True,
        "type": "string",
        "name": "application_json",
        "in": "body"
    }

    @classmethod
    def create_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['parameters'].append(cls.SWAG_APPLICATION_BODY_PARAM)
        template['responses']['201'] = cls.R201
        template['responses']['400'] = cls.R400
        template['responses']['401'] = cls.R401
        return cls._build_swag_response(template)

    @classmethod
    def create(cls, data, account, dry_run=False):
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

        # now augment the suggestion object with all the additional information it requires
        #
        # suggester name and email from the user account
        ap.set_suggester(account.name, account.email)

        # they are not allowed to set "subject"
        ap.bibjson().remove_subjects()

        # if this is an update request on an existing journal
        if ap.current_journal is not None:
            # DOAJ BLL for this request
            dbl = DOAJ()

            # load the update_request application either directly or by crosswalking the journal object
            vanilla_ap = None
            jlock = None
            alock = None
            try:
                vanilla_ap, jlock, alock = dbl.update_request_for_journal(ap.current_journal, account=account)
            except AuthoriseException as e:
                if e.reason == AuthoriseException.WRONG_STATUS:
                    raise Api403Error()
                else:
                    raise Api404Error()
            except lock.Locked as e:
                raise Api409Error()

            # if we didn't find an application or journal, 404 the user
            if vanilla_ap is None:
                if jlock is not None: jlock.delete()
                if alock is not None: alock.delete()
                raise Api404Error()

            # convert the incoming application into the web form
            form = MultiDict(xwalk.SuggestionFormXWalk.obj2form(ap))

            fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", form_data=form, source=vanilla_ap)
            if fc.validate():
                try:
                    save_target = not dry_run
                    fc.finalise(save_target=save_target, email_alert=False)
                    return fc.target
                except formcontext.FormContextException as e:
                    raise Api400Error()
                finally:
                    if jlock is not None: jlock.delete()
                    if alock is not None: alock.delete()
            else:
                if jlock is not None: jlock.delete()
                if alock is not None: alock.delete()
                raise Api400Error()

        # otherwise, this is a brand-new application
        else:
            # convert the incoming application into the web form
            form = MultiDict(xwalk.SuggestionFormXWalk.obj2form(ap))

            # create a template that will hold all the values we want to persist across the form submission
            template = models.Suggestion()
            template.set_owner(account.id)

            fc = formcontext.ApplicationFormFactory.get_form_context(form_data=form, source=template)
            if fc.validate():
                try:
                    save_target = not dry_run
                    fc.finalise(save_target=save_target, email_alert=False)
                    return fc.target
                except formcontext.FormContextException as e:
                    raise Api400Error()
            else:
                raise Api400Error()


    @classmethod
    def retrieve_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['parameters'].append(cls.SWAG_ID_PARAM)
        template['responses']['200'] = cls.R200
        template['responses']['200']['schema'] = IncomingApplication().struct_to_swag(schema_title='Application schema')
        template['responses']['401'] = cls.R401
        template['responses']['404'] = cls.R404
        return cls._build_swag_response(template)

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
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['parameters'].append(cls.SWAG_ID_PARAM)
        template['parameters'].append(cls.SWAG_APPLICATION_BODY_PARAM)
        template['responses']['204'] = cls.R204
        template['responses']['400'] = cls.R400
        template['responses']['401'] = cls.R401
        template['responses']['403'] = cls.R403
        template['responses']['404'] = cls.R404
        return cls._build_swag_response(template)

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
        template['parameters'].append(cls.SWAG_ID_PARAM)
        template['responses']['204'] = cls.R204
        template['responses']['401'] = cls.R401
        template['responses']['403'] = cls.R403
        template['responses']['404'] = cls.R404
        return cls._build_swag_response(template)

    @classmethod
    def delete(cls, id, account, dry_run=False):
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
        if not dry_run:
            ap.delete()