from portality.api.v1.common import Api, Api404Error, Api400Error, Api403Error, Api401Error
from portality.api.v1.crud import ArticlesCrudApi

from portality.bll import DOAJ
from portality.bll import exceptions

from copy import deepcopy



class ArticlesBulkApi(Api):

    SWAG_TAG = 'Bulk API'

    @classmethod
    def create_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['parameters'].append(
            {
                "description": "<div class=\"search-query-docs\">A list/array of article JSON objects that you would like to create or update. The contents should be a list, and each object in the list should comply with the schema displayed in the <a href=\"/api/v1/docs#CRUD_Articles_get_api_v1_articles_article_id\"> GET (Retrieve) an article route</a>. Partial updates are not allowed, you have to supply the full JSON.</div>",
                "required": True,
                "type": "string",
                "name": "article_json",
                "in": "body"
            }
        )
        template['parameters'].append(cls.SWAG_API_KEY_REQ_PARAM)
        template['responses']['201'] = cls.R201_BULK
        template['responses']['400'] = cls.R400
        template['responses']['401'] = cls.R401
        template['responses']['403'] = cls.R403
        return cls._build_swag_response(template)

    @classmethod
    def create(cls, articles, account):
        # We run through the articles once, validating in dry-run mode
        # and deduplicating as we go. Then we .save() everything once
        # we know all incoming articles are valid.

        # as long as authentication (in the layer above) has been successful, and the account exists, then
        # we are good to proceed
        if account is None:
            raise Api401Error()

        # convert the data into a suitable article models
        articles = [ArticlesCrudApi.prep_article(data) for data in articles]

        articleService = DOAJ.articleService()
        try:
            result = articleService.batch_create_articles(articles, account, add_journal_info=True)
            return [a.id for a in articles]
        except exceptions.IngestException as e:
            raise Api400Error(e.message)


    @classmethod
    def delete_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['parameters'].append(
            {
                "description": "<div class=\"search-query-docs\">A list/array of DOAJ article IDs. E.g. [\"4cf8b72139a749c88d043129f00e1b07\", \"232b53726fb74cc4a8eb4717e5a43193\"].</div>",
                "required": True,
                "type": "string",
                "name": "article_ids",
                "in": "body"
            }
        )
        template['parameters'].append(cls.SWAG_API_KEY_REQ_PARAM)
        template['responses']['204'] = cls.R204
        template['responses']['400'] = cls.R400
        template['responses']['401'] = cls.R401
        return cls._build_swag_response(template)

    @classmethod
    def delete(cls, article_ids, account):
        # we run through delete twice, once as a dry-run and the second time
        # as the real deal
        for id in article_ids:
            try:
                ArticlesCrudApi.delete(id, account, dry_run=True)
            except Api404Error as e:
                raise Api400Error("Id {x} does not exist or does not belong to this user account".format(x=id))
            except Api403Error as e:
                raise Api400Error("Id {x} is not in a state which allows it to be deleted".format(x=id))

        for id in article_ids:
            ArticlesCrudApi.delete(id, account)
