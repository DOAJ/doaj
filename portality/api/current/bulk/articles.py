# ~~APIBulkArticles:Feature->APIBulk:Feature~~
import warnings
from copy import deepcopy
from typing import List, Dict

from portality import models
from portality.api.common import Api, Api404Error, Api400Error, Api403Error, Api401Error
from portality.api.current.crud import ArticlesCrudApi
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.bll.exceptions import DuplicateArticleException
from portality.models import BulkArticles
from portality.tasks.article_bulk_create import ArticleBulkCreateBackgroundTask


class ArticlesBulkApi(Api):
    # ~~->Swagger:Feature~~
    # ~~->API:Documentation~~
    SWAG_TAG = 'Bulk API'

    @classmethod
    def create_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['parameters'].append(
            {
                "description": "<div class=\"search-query-docs\">A list/array of article JSON objects that you would like to create or update. The contents should be a list, and each object in the list should comply with the schema displayed in the <a href=\"/api/docs#CRUD_Articles_get_api_articles_article_id\"> GET (Retrieve) an article route</a>. Partial updates are not allowed, you have to supply the full JSON.</div>",
                "required": True,
                "schema": {"type": "string"},
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
        warnings.warn("This method is deprecated, use create_async instead", DeprecationWarning)
        # We run through the articles once, validating in dry-run mode
        # and deduplicating as we go. Then we .save() everything once
        # we know all incoming articles are valid.

        # as long as authentication (in the layer above) has been successful, and the account exists, then
        # we are good to proceed
        if account is None:
            raise Api401Error()

        # convert the data into a suitable article models
        articles = [ArticlesCrudApi.prep_article_for_api(data, account) for data in articles]

        # ~~->Article:Service~~
        articleService = DOAJ.articleService()
        try:
            # ~~->BatchCreateArticles:Feature~~
            result = articleService.batch_create_articles(articles, account, add_journal_info=True)
            return [a.id for a in articles]
        except DuplicateArticleException as e:
            raise Api403Error(str(e))
        except exceptions.IngestException as e:
            raise Api400Error(str(e))
        except exceptions.ArticleNotAcceptable as e:
            raise Api400Error(str(e))

    @classmethod
    def create_async_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        description = """
        <div class=\"search-query-docs\">
        A list/array of article JSON objects that you would like to create or update. 
        The contents should be a list, and each object in the list should comply with 
        the schema displayed in the 
        <a href=\"/api/docs#CRUD_Articles_get_api_articles_article_id\"> GET (Retrieve) an article route</a>. 
        Partial updates are not allowed, you have to supply the full JSON.
        
        This api is asynchronously, response will be a task id, you can use this id to query the task status.
        </div>
        """
        template['parameters'].append(
            {
                "description": description,
                "required": True,
                "schema": {"type": "string"},
                "name": "article_json",
                "in": "body"
            }
        )
        template['parameters'].append(cls.SWAG_API_KEY_REQ_PARAM)
        template['responses']['202'] = {
            "schema": {
                "properties": {
                    "msg": {"type": "string", },
                    "upload_id": {"type": "string",
                                  "description": "The upload id of the task, "
                                                 "User can use this id to check the bulk upload status."},
                },
                "type": "object"
            },
            "description": "Resources are being created asynchronously, response contains the task IDs "
        }
        template['responses']['400'] = cls.R400
        return cls._build_swag_response(template)

    @classmethod
    def create_async(cls, income_articles: List[Dict], account: models.Account):
        job = ArticleBulkCreateBackgroundTask.prepare(account.id, incoming_articles=income_articles)
        ArticleBulkCreateBackgroundTask.submit(job)
        upload_id = next(v for k, v in job.params.items() if k.endswith('__upload_id'))
        return upload_id

    @classmethod
    def get_async_status_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['parameters'].append(
            {
                "description": "<div class=\"search-query-docs\">The upload id of the task, "
                               "User can use this id to check the bulk upload status.</div>",
                "required": True,
                "schema": {"type": "string"},
                "name": "upload_id",
                "in": "query"
            }
        )
        template['parameters'].append(cls.SWAG_API_KEY_REQ_PARAM)
        template['responses']['200'] = {
            "schema": {
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "The status of the task",
                        "enum": ["incoming", "validated", "falied", "processed", "partial"]

                    },
                    "results": {
                        'type': 'object',
                        'description': 'The result of the upload',
                        "properties": {
                            "imported": {
                                "type": "integer",
                                "description": "The number of articles imported",
                            },
                            "failed": {
                                "type": "integer",
                                "description": "The number of articles failed to import",
                            },
                            "update": {
                                "type": "integer",
                                "description": "The number of articles updated",
                            },
                            "new": {
                                "type": "integer",
                                "description": "The number of articles created",
                            },
                        },
                    }

                },
                "type": "object"
            },
            "description": "Return status of upload ids"
        }
        template['responses']['400'] = {
            "schema": {
                "properties": {
                    "msg": {"type": "string", "description": "The error message"},
                },
                "type": "object"
            },
        }
        return cls._build_swag_response(template)

    @classmethod
    def get_async_status(cls, current_user_id, upload_id=None, ) -> Dict:
        if not upload_id:
            raise Api400Error("upload_id is required")

        bulk_article = BulkArticles.pull(upload_id)
        if bulk_article is None or bulk_article.owner != current_user_id:
            raise Api400Error("upload_id is invalid")

        internal_external_status_map = {
            "incoming": "pending",
            "partial": "processed_partial"
        }

        status = {
            "id": upload_id,
            "created": bulk_article.created_date,
            'status': internal_external_status_map.get(bulk_article.status, bulk_article.status),
        }

        if bulk_article.status in ["processed", "partial"]:
            status['results'] = {
                "imported": bulk_article.imported,
                "failed": bulk_article.failed_imports,
                "update": bulk_article.updates,
                "new": bulk_article.new,
            }

        if bulk_article.error:
            status['error'] = bulk_article.error

        if bulk_article.error_details:
            status['error_details'] = bulk_article.error_details

        if bulk_article.failure_reasons:
            status['failure_reasons'] = bulk_article.failure_reasons

        return status

    @classmethod
    def delete_swag(cls):
        template = deepcopy(cls.SWAG_TEMPLATE)
        template['parameters'].append(
            {
                "description": "<div class=\"search-query-docs\">A list/array of DOAJ article IDs. E.g. [\"4cf8b72139a749c88d043129f00e1b07\", \"232b53726fb74cc4a8eb4717e5a43193\"].</div>",
                "required": True,
                "schema": {"type": "string"},
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
        # ~~->APICrudArticles:Feature~~
        for id in article_ids:
            try:
                ArticlesCrudApi.delete(id, account, dry_run=True)
            except Api404Error as e:
                raise Api400Error("Id {x} does not exist or does not belong to this user account".format(x=id))
            except Api403Error as e:
                raise Api400Error("Id {x} is not in a state which allows it to be deleted".format(x=id))

        for id in article_ids:
            ArticlesCrudApi.delete(id, account)
