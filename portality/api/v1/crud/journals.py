from portality.api.v1.crud.common import CrudApi


class JournalsCrudApi(CrudApi):
    @classmethod
    def __retrieve(cls, jid):
        pass
        # TODO define task anew based on new API data objects

        # exclude from response: bibjson.active
        # include in response: bibjson, id, created_date, last_updated

    @classmethod
    def retrieve_public(cls, jid):
        j = cls.__retrieve(jid)
        # return j

    @classmethod
    def retrieve_auth(cls, jid, owner):
        j = cls.__retrieve(jid)
        # check if owner arg above is the same as the journal's owner (see portality.models.Journal for owner property)
        # authenticated owners of a journal are allowed to see journals where .is_in_doaj() == False
        # if yes
        # return j
        # if not return something or define and raise a custom exception to cause 404 Not Found in the view