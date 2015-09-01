from portality.api.v1.crud.common import CrudApi
from portality.api.v1 import Api401Error, Api400Error
from portality.api.v1.data_objects import ArticleDO
from portality.lib import dataobj

class ArticlesCrudApi(CrudApi):

    @classmethod
    def create(cls, data, account):
        # as long as authentication (in the layer above) has been successful, and the account exists, then
        # we are good to proceed
        if account is None:
            raise Api401Error()

        # first thing to do is a structural validation, by instantiating the data object
        try:
            ia = ArticleDO(data)
        except dataobj.DataStructureException as e:
            raise Api400Error(e.message)

        # if that works, convert it to a Suggestion object
        am = ia.to_article_model()

        # if the caller set the id, created_date, or last_updated, then we discard the data and apply our
        # own values (note that last_updated will get overwritten anyway)
        am.set_id()
        am.set_created()

        # finally save the new article, and return to the caller
        am.save()
        return am
