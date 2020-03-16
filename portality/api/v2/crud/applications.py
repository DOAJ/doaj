from portality.api.v2.crud.common import CrudApi
from portality.api.v2.common import Api401Error, Api400Error, Api404Error, Api403Error, Api409Error
from portality.api.v2.data_objects.application import IncomingApplication, OutgoingApplication
from portality.lib import seamless
from portality import models

from portality.bll import DOAJ
from portality.bll.exceptions import AuthoriseException, NoSuchObjectException
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
        "description": """<div class=\"search-query-docs\">
            Application JSON that you would like to create or update. The contents should comply with the schema displayed in the
            <a href=\"/api/v1/docs#CRUD_Applications_get_api_v1_application_application_id\"> GET (Retrieve) an application route</a>.
            Explicit documentation for the structure of this data is also <a href="https://github.com/DOAJ/doaj/blob/master/docs/system/IncomingAPIApplication.md">provided here</a>.
            Partial updates are not allowed, you have to supply the full JSON.</div>""",
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
        template['responses']['409'] = cls.R409
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
        except seamless.SeamlessException as e:
            raise Api400Error(str(e))

        # if that works, convert it to a Suggestion object
        ap = ia.to_application_model()

        # now augment the suggestion object with all the additional information it requires
        #
        # suggester name and email from the user account
        ap.set_applicant(account.name, account.email)

        # they are not allowed to set "subject"
        ap.bibjson().remove_subjects()

        # if this is an update request on an existing journal
        if ap.current_journal is not None:
            # DOAJ BLL for this request
            applicationService = DOAJ.applicationService()

            # load the update_request application either directly or by crosswalking the journal object
            vanilla_ap = None
            jlock = None
            alock = None
            try:
                vanilla_ap, jlock, alock = applicationService.update_request_for_journal(ap.current_journal, account=account)
            except AuthoriseException as e:
                if e.reason == AuthoriseException.WRONG_STATUS:
                    raise Api403Error("The application is no longer in a state in which it can be edited via the API")
                else:
                    raise Api404Error()
            except lock.Locked as e:
                raise Api409Error("The application you are requesting an update for is locked for editing by another user")

            # if we didn't find an application or journal, 404 the user
            if vanilla_ap is None:
                if jlock is not None: jlock.delete()
                if alock is not None: alock.delete()
                raise Api404Error()

            # convert the incoming application into the web form
            form = MultiDict(xwalk.SuggestionFormXWalk.obj2form(ap))        #TODO: not converted to v2 yet

            fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", form_data=form, source=vanilla_ap)
            if fc.validate():
                try:
                    save_target = not dry_run
                    fc.finalise(save_target=save_target, email_alert=False)
                    return fc.target
                except formcontext.FormContextException as e:
                    raise Api400Error(str(e))
                finally:
                    if jlock is not None: jlock.delete()
                    if alock is not None: alock.delete()
            else:
                if jlock is not None: jlock.delete()
                if alock is not None: alock.delete()
                raise Api400Error(cls._validation_message(fc))

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
                    raise Api400Error(str(e))
            else:
                raise Api400Error(cls._validation_message(fc))


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
        template['responses']['409'] = cls.R409
        return cls._build_swag_response(template)

    @classmethod
    def update(cls, id, data, account):
        # as long as authentication (in the layer above) has been successful, and the account exists, then
        # we are good to proceed
        if account is None:
            raise Api401Error()

        # next thing to do is a structural validation of the replacement data, by instantiating the object
        try:
            ia = IncomingApplication(data)
        except seamless.SeamlessException as e:
            raise Api400Error(str(e))

        # now see if there's something for us to update
        ap = models.Suggestion.pull(id)
        if ap is None:
            raise Api404Error()

        # if that works, convert it to a Suggestion object
        new_ap = ia.to_application_model()

        # now augment the suggestion object with all the additional information it requires
        #
        # suggester name and email from the user account
        new_ap.set_suggester(account.name, account.email)

        # they are not allowed to set "subject"
        new_ap.bibjson().remove_subjects()

        # DOAJ BLL for this request
        applicationService = DOAJ.applicationService()
        authService = DOAJ.authorisationService()

        # if a current_journal is specified on the incoming data
        if new_ap.current_journal is not None:
            # once an application has a current_journal specified, you can't change it
            if new_ap.current_journal != ap.current_journal:
                raise Api400Error("current_journal cannot be changed once set.  current_journal is {x}; this request tried to change it to {y}".format(x=ap.current_journal, y=new_ap.current_journal))

            # load the update_request application either directly or by crosswalking the journal object
            vanilla_ap = None
            jlock = None
            alock = None
            try:
                vanilla_ap, jlock, alock = applicationService.update_request_for_journal(new_ap.current_journal, account=account)
            except AuthoriseException as e:
                if e.reason == AuthoriseException.WRONG_STATUS:
                    raise Api403Error("The application is no longer in a state in which it can be edited via the API")
                else:
                    raise Api404Error()
            except lock.Locked as e:
                raise Api409Error("The application is locked for editing by another user - most likely your application is being reviewed by an editor")

            # if we didn't find an application or journal, 404 the user
            if vanilla_ap is None:
                if jlock is not None: jlock.delete()
                if alock is not None: alock.delete()
                raise Api404Error()

            # convert the incoming application into the web form
            form = MultiDict(xwalk.SuggestionFormXWalk.obj2form(new_ap))

            fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", form_data=form, source=vanilla_ap)
            if fc.validate():
                try:
                    fc.finalise(email_alert=False)
                    return fc.target
                except formcontext.FormContextException as e:
                    raise Api400Error(str(e))
                finally:
                    if jlock is not None: jlock.delete()
                    if alock is not None: alock.delete()
            else:
                if jlock is not None: jlock.delete()
                if alock is not None: alock.delete()
                raise Api400Error(cls._validation_message(fc))
        else:
            try:
                authService.can_edit_application(account, ap)
            except AuthoriseException as e:
                if e.reason == e.WRONG_STATUS:
                    raise Api403Error("The application is no longer in a state in which it can be edited via the API")
                else:
                    raise Api404Error()

            # convert the incoming application into the web form
            form = MultiDict(xwalk.SuggestionFormXWalk.obj2form(new_ap))

            fc = formcontext.ApplicationFormFactory.get_form_context(form_data=form, source=ap)
            if fc.validate():
                try:
                    fc.finalise(email_alert=False)
                    return fc.target
                except formcontext.FormContextException as e:
                    raise Api400Error(str(e))
            else:
                raise Api400Error(cls._validation_message(fc))

    @classmethod
    def delete_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['parameters'].append(cls.SWAG_ID_PARAM)
        template['responses']['204'] = cls.R204
        template['responses']['401'] = cls.R401
        template['responses']['403'] = cls.R403
        template['responses']['404'] = cls.R404
        template['responses']['409'] = cls.R409
        return cls._build_swag_response(template)

    @classmethod
    def delete(cls, id, account, dry_run=False):
        # as long as authentication (in the layer above) has been successful, and the account exists, then
        # we are good to proceed
        if account is None:
            raise Api401Error()

        applicationService = DOAJ.applicationService()
        authService = DOAJ.authorisationService()

        if dry_run:
            application, _ = applicationService.application(id)
            if application is not None:
                try:
                    authService.can_edit_application(account, application)
                except AuthoriseException as e:
                    if e.reason == e.WRONG_STATUS:
                        raise Api403Error()
                    raise Api404Error()
            else:
                raise Api404Error()
        else:
            try:
                applicationService.delete_application(id, account)
            except AuthoriseException as e:
                if e.reason == e.WRONG_STATUS:
                    raise Api403Error()
                raise Api404Error()
            except NoSuchObjectException as e:
                raise Api404Error()

    @classmethod
    def _validation_message(cls, fc):
        errors = fc.errors
        msg = "The following validation errors were received:\n"
        for fieldName, errorMessages in errors.items():
            fieldName = xwalk.SuggestionFormXWalk.formField2objectField(fieldName)
            msg += fieldName + " : " + "; ".join(errorMessages) + "\n"
        return msg

