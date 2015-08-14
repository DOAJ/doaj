from portality.api.v1.crud.common import CrudApi
from portality.api.v1 import Api401Error, Api400Error
from portality.api.v1.data_objects import IncomingApplication
from portality.lib import dataobj
from datetime import datetime

class ApplicationsCrudApi(CrudApi):

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

        # finally save the new application, and return to the caller
        ap.save()
        return ap