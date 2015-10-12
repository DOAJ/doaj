from portality import models
from portality.api.v1.crud.common import CrudApi
from portality.api.v1.data_objects.journal import OutgoingJournal
from portality.api.v1 import Api401Error, Api404Error

from copy import deepcopy


class JournalsCrudApi(CrudApi):

    @classmethod
    def retrieve_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['tags'].append('CRUD')
        template["parameters"].append(
            {
                "description": "<div class=\"search-query-docs\">DOAJ journal ID. E.g. 4cf8b72139a749c88d043129f00e1b07 .</div>",
                "required": True,
                "type": "string",
                "name": "journal_id",
                "in": "path"
            }
        )
        template['responses']['200']['schema']['title'] = 'Journal schema'
        template['responses']['200']['schema']['properties'] = OutgoingJournal().struct_to_swag()
        return template

    @classmethod
    def retrieve(cls, jid, account):
        # is the journal id valid
        j = models.Journal.pull(jid)
        if j is None:
            raise Api404Error()

        # at this point we're happy to return the journal if it's
        # meant to be seen by the public
        if j.get('admin').get('in_doaj', False):
            return OutgoingJournal.from_model(j)

        # as long as authentication (in the layer above) has been successful, and the account exists, then
        # we are good to proceed
        if account is None:
            raise Api401Error()

        # this journal's metadata is not currently published in DOAJ, so
        # we need to check ownership
        # is the current account the owner of the journal
        # if not we raise a 404 because that id does not exist for that user account.
        if j.owner != account.id:
            raise Api404Error()

        return OutgoingJournal.from_model(j)