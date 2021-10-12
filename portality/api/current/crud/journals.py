# ~~APICrudJournals:Feature->APICrud:Feature~~
from portality import models
from portality.api.current.crud.common import CrudApi
from portality.api.current.data_objects.journal import OutgoingJournal, JOURNAL_STRUCT
from portality.api.common import Api400Error, Api401Error, Api404Error

from copy import deepcopy


class JournalsCrudApi(CrudApi):

    API_KEY_OPTIONAL = True

    # ~~->Swagger:Feature~~
    # ~~->API:Documentation~~
    SWAG_TAG = 'CRUD Journals'
    SWAG_ID_PARAM = {
        "description": "<div class=\"search-query-docs\">DOAJ journal ID. E.g. 4cf8b72139a749c88d043129f00e1b07 .</div>",
        "required": True,
        "type": "string",
        "name": "journal_id",
        "in": "path"
    }

    @classmethod
    def retrieve_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template["parameters"].append(cls.SWAG_ID_PARAM)
        template['responses']['200'] = cls.R200
        template['responses']['200']['schema'] = OutgoingJournal().struct_to_swag(schema_title='Journal schema',
                                                                                  struct=JOURNAL_STRUCT)
        template['responses']['200']['description'] = 'Detailed documentation on the response format is available <a ' \
                                                      'href="https://doaj.github.io/doaj-docs/master/data_models/OutgoingAPIJournal">here</a> '
        template['responses']['404'] = cls.R404
        return cls._build_swag_response(template, api_key_override=False)

    @classmethod
    def retrieve(cls, jid, account):
        # is the journal id valid
        try:
            j = models.Journal.pull(jid)    # ~~->Journal:Model~~
        except Exception as e:
            raise Api400Error(str(e))
        if j is None:
            raise Api404Error()

        # at this point we're happy to return the journal if it's
        # meant to be seen by the public
        if j.is_in_doaj():
            return OutgoingJournal.from_model(j)    # ~~->APIOutgoingJournal:Model~~

        # if the journal is not Public then it doesn't matter who asks for it, it can't be retrieved
        raise Api404Error()
