from portality.api.v1.common import Api, Api404Error, Api400Error, Api403Error
from portality.api.v1.crud import ArticlesCrudApi

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
        # we run through create twice, once as a dry-run and the second time
        # as the real deal
        for a in articles:
            ArticlesCrudApi.create(a, account, dry_run=True)
        # no formatting issues, the JSON of each article complies with required format at this point

        ids = []
        dois_seen = set()
        fulltext_urls_seen = set()
        for a in articles:
            duplicate = False  # skip articles if their fulltext URL or DOI is the same

            for i in a['bibjson']['identifier']:
                if i['type'] == 'doi':
                    if i['id'] in dois_seen:
                        duplicate = True
                        break
                    dois_seen.add(i['id'])

            if duplicate:
                continue

            for l in a['bibjson']['link']:
                if l['type'] == 'fulltext':
                    if l['url'] in fulltext_urls_seen:
                        duplicate = True
                        break
                    fulltext_urls_seen.add(l['url'])

            if duplicate:
                continue

            n = ArticlesCrudApi.create(a, account)
            ids.append(n.id)

        return ids

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