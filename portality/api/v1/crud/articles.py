from portality.api.v1.crud.common import CrudApi
from portality.api.v1 import Api400Error, Api401Error, Api403Error, Api404Error
from portality.api.v1.data_objects import IncomingArticleDO, OutgoingArticleDO
from portality.lib import dataobj
from portality import models
from portality.article import XWalk

class ArticlesCrudApi(CrudApi):

    @classmethod
    def __handle_journal_info(cls, am):
        # handle journal info - first save fields users ARE allowed to update into temporary vars
        number = am.bibjson().number
        volume = am.bibjson().volume
        start_page = am.bibjson().start_page
        end_page = am.bibjson().end_page
        am.bibjson().remove_journal_metadata()  # then destroy all journal metadata
        if not am.add_journal_metadata():  # overwrite journal part of metadata and in_doaj setting
            raise Api400Error("No journal found to attach article to. Each article in DOAJ must belong to a journal and the (E)ISSNs provided in the bibjson.identifiers section of this article record do not match any DOAJ journal.")
        # restore the user's data
        am.bibjson().number = number
        am.bibjson().volume = volume
        am.bibjson().start_page = start_page
        am.bibjson().end_page = end_page
        return am

    @classmethod
    def create(cls, data, account):
        # as long as authentication (in the layer above) has been successful, and the account exists, then
        # we are good to proceed
        if account is None:
            raise Api401Error()

        # first thing to do is a structural validation, by instantiating the data object
        try:
            ia = IncomingArticleDO(data)
        except dataobj.DataStructureException as e:
            raise Api400Error(e.message)

        # if that works, convert it to an Article object
        am = ia.to_article_model()

        # Check we are allowed to create an article for this journal
        if not XWalk.is_legitimate_owner(am, account.id):
            raise Api404Error()                 # not found for this account

        # if the caller set the id, created_date, or last_updated, then we discard the data and apply our
        # own values (note that last_updated will get overwritten anyway)
        am.set_id()
        am.set_created()

        # not allowed to set subjects
        am.bibjson().remove_subjects()
        am = cls.__handle_journal_info(am)

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
        if not XWalk.is_legitimate_owner(ar, account.id):
            raise Api404Error()                 # not found for this account

        # Return the article
        oa = OutgoingArticleDO.from_model(ar)
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

        # Check we're allowed to edit this article
        if not XWalk.is_legitimate_owner(ar, account.id):
            raise Api404Error()                 # not found for this account

        # next thing to do is a structural validation of the replacement data, by instantiating the object
        try:
            ia = IncomingArticleDO(data)
        except dataobj.DataStructureException as e:
            raise Api400Error(e.message)

        # if that works, convert it to an Article object bringing over everything outside the
        # incoming article from the original article
        new_ar = ia.to_article_model(ar)

        # we need to ensure that any properties of the existing article that aren't allowed to change
        # are copied over
        new_ar.set_id(id)
        new_ar.set_created(ar.created_date)
        new_ar.bibjson().set_subjects(ar.bibjson().subjects())
        new_ar = cls.__handle_journal_info(new_ar)

        # finally save the new article, and return to the caller
        new_ar.save()
        return new_ar

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
        if not XWalk.is_legitimate_owner(ar, account.id):
            raise Api404Error()                 # not found for this account

        # issue the delete (no record of the delete required)
        ar.delete()
