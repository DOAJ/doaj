from portality.api.v1.common import Api


class JournalsCrudApi(Api):
    @classmethod
    def __retrieve_journal(cls, jid):
        pass
        # fetch the journal from Elasticsearch, make a copy of journal.data
        # remove keys that are never to be returned through the API, regardless
        # if the requester is authenticated or not
        # return the resulting new dict

        # remove these keys: bibjson.active
        # remove everything except bibjson, id, created_date, last_updated

    @classmethod
    def retrieve_public_journal(cls, jid):
        j = cls.__retrieve_journal(jid)
        # return j

    @classmethod
    def retrieve_auth_journal(cls, jid, owner):
        j = cls.__retrieve_journal(jid)
        # check if owner arg above is the same as the journal's owner (see portality.models.Journal for owner property)
        # authenticated owners of a journal are allowed to see journals where .is_in_doaj() == False
        # if yes
        # return j
        # if not return something to cause 404 Not Found in the view