# ~~APICrudArticles:Feature->APICrud:Feature~~
import json

from portality.api.current.crud.common import CrudApi
from portality.api.current import Api400Error, Api401Error, Api403Error, Api404Error, Api500Error
from portality.api.current.data_objects.article import IncomingArticleDO, OutgoingArticleDO
from portality.core import app
from portality.lib import dataobj
from portality import models, app_email
from portality.bll.doaj import DOAJ
from portality.bll.exceptions import ArticleMergeConflict, ArticleNotAcceptable, DuplicateArticleException, \
    IngestException
from copy import deepcopy

class ArticlesCrudApi(CrudApi):

    API_KEY_OPTIONAL = False

    # ~~->Swagger:Feature~~
    # ~~->API:Documentation~~
    SWAG_TAG = 'CRUD Articles'
    SWAG_ID_PARAM = {
        "description": "<div class=\"search-query-docs\">DOAJ article ID. E.g. 4cf8b72139a749c88d043129f00e1b07 .</div>",
        "required": True,
        "type": "string",
        "name": "article_id",
        "in": "path"
    }
    SWAG_ARTICLE_BODY_PARAM = {
        "description": """<div class=\"search-query-docs\">
            Article JSON that you would like to create or update. The contents should comply with the schema displayed
            in the <a href=\"/api/docs#CRUD_Articles_get_api_articles_article_id\"> GET (Retrieve) an article route</a>.
            Explicit documentation for the structure of this data is also <a href="https://doaj.github.io/doaj-docs/master/data_models/IncomingAPIArticle">provided here</a>.
            Partial updates are not allowed, you have to supply the full JSON.</div>""",
        "required": True,
        "schema": {"type" : "string"},
        "name": "article_json",
        "in": "body"
    }

    @classmethod
    def __handle_journal_info(cls, am):
        # handle journal info - first save fields users ARE allowed to update into temporary vars
        number = am.bibjson().number
        volume = am.bibjson().volume
        start_page = am.bibjson().start_page
        end_page = am.bibjson().end_page
        am.bibjson().remove_journal_metadata()  # then destroy all journal metadata

        try:
            am.add_journal_metadata()  # overwrite journal part of metadata and in_doaj setting
        except models.NoJournalException as e:
            raise Api400Error("No journal found to attach article to. Each article in DOAJ must belong to a journal and the (E)ISSNs provided in the bibjson.identifiers section of this article record do not match any DOAJ journal.")

        # restore the user's data
        am.bibjson().number = number
        am.bibjson().volume = volume
        am.bibjson().start_page = start_page
        am.bibjson().end_page = end_page
        return am

    @classmethod
    def create_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['parameters'].append(cls.SWAG_ARTICLE_BODY_PARAM)
        template['responses']['201'] = cls.R201
        template['responses']['400'] = cls.R400
        template['responses']['401'] = cls.R401
        template['responses']['403'] = cls.R403
        return cls._build_swag_response(template)

    @classmethod
    def create(cls, data, account):
        # as long as authentication (in the layer above) has been successful, and the account exists, then
        # we are good to proceed
        if account is None:
            raise Api401Error()

        # convert the data into a suitable article model (raises Api400Error if doesn't conform to struct)
        am = cls.prep_article(data, account)

        # ~~-> Article:Service~~
        articleService = DOAJ.articleService()
        try:
            result = articleService.create_article(am, account, add_journal_info=True)
        except ArticleMergeConflict as e:
            raise Api400Error(str(e))
        except ArticleNotAcceptable as e:
            raise Api400Error(str(e))
        except DuplicateArticleException as e:
            raise Api403Error(str(e))
        except IngestException as e:
            raise Api400Error(str(e))


        # Check we are allowed to create an article for this journal
        if result.get("fail", 0) == 1:
            raise Api403Error("It is not possible to create an article for this journal. Have you included in the upload an ISSN which is not associated with any journal in your account? ISSNs must match exactly the ISSNs against the journal record.")

        return am


    @classmethod
    def prep_article(cls, data, account):
        # first thing to do is a structural validation, by instantiating the data object
        try:
            ia = IncomingArticleDO(data)
        except dataobj.DataStructureException as e:
            raise Api400Error(str(e))
        except dataobj.ScriptTagFoundException as e:
            # ~~->Email:ExternalService~~
            email_data = {"article": data, "account": account.__dict__}
            jdata = json.dumps(email_data, indent=4)
            # send warning email about the service tag in article metadata detected
            try:
                to = app.config.get('SCRIPT_TAG_DETECTED_EMAIL_RECIPIENTS')
                fro = app.config.get("SYSTEM_EMAIL_FROM", "feedback@doaj.org")
                subject = app.config.get("SERVICE_NAME", "") + " - script tag detected in application metadata"
                es_type="article"
                app_email.send_mail(to=to,
                                     fro=fro,
                                     subject=subject,
                                     template_name="email/script_tag_detected.jinja2",
                                     es_type=es_type,
                                     data=jdata)
            except app_email.EmailException:
                app.logger.exception('Error sending script tag detection email - ' + jdata)
            raise Api400Error(str(e))

        # if that works, convert it to an Article object
        am = ia.to_article_model()

        # the user may have supplied metadata in the model for id and created_date
        # and we want to can that data.  If this is a truly new article its fine for
        # us to assign a new id here, and if it's a duplicate, it will get attached
        # to its duplicate id anyway.
        am.set_id()
        am.set_created()

        # not allowed to set subjects
        am.bibjson().remove_subjects()

        # get the journal information set straight
        am = cls.__handle_journal_info(am)

        return am


    @classmethod
    def retrieve_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['parameters'].append(cls.SWAG_ID_PARAM)
        template['responses']['200'] = cls.R200
        template['responses']['200']['schema'] = IncomingArticleDO().struct_to_swag(schema_title='Article schema')
        template['responses']['401'] = cls.R401
        template['responses']['404'] = cls.R404
        template['responses']['500'] = cls.R500
        return cls._build_swag_response(template, api_key_optional_override=True)

    @classmethod
    def retrieve(cls, id, account):

        # is the article id valid?
        ar = models.Article.pull(id)
        if ar is None:
            raise Api404Error()

        # at this point we're happy to return the article if it's
        # meant to be seen by the public
        if ar.is_in_doaj():
            try:
                return OutgoingArticleDO.from_model(ar)
            except:
                raise Api500Error()

        # as long as authentication (in the layer above) has been successful, and the account exists, then
        # we are good to proceed
        if account is None or account.is_anonymous:
            raise Api401Error()

        # Check we're allowed to retrieve this article
        articleService = DOAJ.articleService()
        if not articleService.is_legitimate_owner(ar, account.id):
            raise Api404Error()  # not found for this account

        # Return the article
        oa = OutgoingArticleDO.from_model(ar)
        return oa

    @classmethod
    def update_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['parameters'].append(cls.SWAG_ID_PARAM)
        template['parameters'].append(cls.SWAG_ARTICLE_BODY_PARAM)
        template['responses']['204'] = cls.R204
        template['responses']['400'] = cls.R400
        template['responses']['401'] = cls.R401
        template['responses']['404'] = cls.R404
        return cls._build_swag_response(template)

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
        # ~~-> Article:Service~~
        articleService = DOAJ.articleService()
        if not articleService.is_legitimate_owner(ar, account.id):
            raise Api404Error()  # not found for this account

        # next thing to do is a structural validation of the replacement data, by instantiating the object
        try:
            ia = IncomingArticleDO(data)
        except dataobj.DataStructureException as e:
            raise Api400Error(str(e))

        # if that works, convert it to an Article object bringing over everything outside the
        # incoming article from the original article

        # we need to ensure that any properties of the existing article that aren't allowed to change
        # are copied over
        new_ar = ia.to_article_model(ar)
        new_ar.set_id(id)
        new_ar.set_created(ar.created_date)
        new_ar.bibjson().set_subjects(ar.bibjson().subjects())

        try:
            # Article save occurs in the BLL create_article
            result = articleService.create_article(new_ar, account, add_journal_info=True, update_article_id=id)
        except ArticleMergeConflict as e:
            raise Api400Error(str(e))
        except ArticleNotAcceptable as e:
            raise Api400Error("; ".join(e.errors))
        except DuplicateArticleException as e:
            raise Api403Error(str(e))

        if result.get("success") == 0:
            raise Api400Error("Article update failed for unanticipated reason")

        return new_ar

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
        ar = models.Article.pull(id)
        if ar is None:
            raise Api404Error()

        # Check we're allowed to retrieve this article
        # ~~-> Article:Service~~
        articleService = DOAJ.articleService()
        if not articleService.is_legitimate_owner(ar, account.id):
            raise Api404Error()  # not found for this account

        # issue the delete (no record of the delete required)
        if not dry_run:
            ar.delete()
