from portality.api.v1.crud.common import CrudApi
from portality.api.v1 import Api400Error, Api401Error, Api404Error
from portality.api.v1.data_objects import ArticleDO
from portality.lib import dataobj
from portality import models
from portality.article import XWalk

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

        # if that works, convert it to an Article object
        am = ia.to_article_model()

        # if the caller set the id, created_date, or last_updated, then we discard the data and apply our
        # own values (note that last_updated will get overwritten anyway)
        am.set_id()
        am.set_created()

        # finally save the new article, and return to the caller
        am.save()
        return am

    @classmethod
    def retrieve(cls, id, account):
        # as long as authentication (in the layer above) has been successful, and the account exists, then
        # we are good to proceed
        if account is None:
            raise Api401Error()

        # is the article id valid
        ar = models.Article.pull(id)
        if ar is None:
            raise Api404Error()

        # Check we're allowed to retrieve this article
        if not XWalk.is_legitimate_owner(ar, account):
            raise Api401Error()

        # Return the article
        oa = ArticleDO.from_model(ar)
        return oa

    @classmethod
    def update(cls, id, data, account):
        # as long as authentication (in the layer above) has been successful, and the account exists, then
        # we are good to proceed
        if account is None:
            raise Api401Error()

        # now see if there's something for us to delete
        ar = models.Article.pull(id)
        if ar is None:
            raise Api404Error()

        # Check we're allowed to retrieve this article
        if not XWalk.is_legitimate_owner(ar, account):
            raise Api401Error()

        # Continue on to updating it...

    @classmethod
    def delete(cls, id, account):
        # as long as authentication (in the layer above) has been successful, and the account exists, then
        # we are good to proceed
        if account is None:
            raise Api401Error()

        # now see if there's something for us to delete
        ar = models.Article.pull(id)
        if ar is None:
            raise Api404Error()

        # Check we're allowed to retrieve this article
        if not XWalk.is_legitimate_owner(ar, account):
            raise Api401Error()

        # issue the delete (no record of the delete required)
        ar.delete()
