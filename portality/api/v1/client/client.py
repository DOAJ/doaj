from portality.core import app
from portality.lib import http
import esprit, json
from portality.api.v1.client import models


DOAJ_RETRY_CODES = [
    408,    # request timeout
    429,    # rate limited
    502,    # bad gateway; retry to see if the gateway can re-establish connection
    503,    # service unavailable; retry to see if it comes back
    504     # gateway timeout; retry to see if it responds next time
]

class DOAJException(Exception):
    def __init__(self, msg, *args, **kwargs):
        self.message = msg
        super(DOAJException, self).__init__(*args, **kwargs)


class DOAJv1API(object):

    CLASSMAP = {
        "journal" : models.Journal,
        "journals" : models.Journal,
    }

    SEARCH_TYPES = [
        "applications",
        "articles",
        "journals"
    ]

    def __init__(self, api_base_url=None, api_key=None):
        self.api_base_url = api_base_url if api_base_url else app.config.get("DOAJ_API1_BASE_URL", "https://doaj.org/api/v1/")
        self.api_key = api_key

        if not self.api_base_url.endswith("/"):
            self.api_base_url += "/"

    def doaj_url(self, endpoint=None, type=None, object_id=None, additional_path=None, params=None):
        """
        build the api request url

        :param endpoint: the endpoint we're sending to.  Unless "search" you can probably leave this out
        :param type: the type we're making the request to; could be application, applications, articles, journals
        :param object_id: the id of the object; only respected if type is given
        :param additional_path: additional path elements to add on the end of the constructed url (used mostly for search criteria)
        :param params: url parameters as a dict - these will be escaped for you, so just pass the values as they are
        :return:
        """
        url = self.api_base_url

        if endpoint is not None:
            url += endpoint + "/"

        if type is not None:
            url += type
            if object_id is not None:
                url += "/" + object_id

        if additional_path is not None:
            if not url.endswith("/"):
                url += "/"
            url += additional_path

        qs = ""
        if params is not None:
            for k, v in params.items():
                if qs != "":
                    qs += "&"
                qs += http.quote(k) + "=" + http.quote(str(v))
        if qs != "":
            url += "?" + qs

        return url

    ###################################################
    ## Methods for handling search queries

    def field_search(self, type, field, value, quote=True, page=1, page_size=10, sort_by=None, sort_dir=None):
        qb = ANDQueryBuilder()
        qb.add_string_field(field, value, quote)
        return self.built_search(type, qb, page=page, page_size=page_size, sort_by=sort_by, sort_dir=sort_dir)

    def built_search(self, type, query_builder, page=1, page_size=10, sort_by=None, sort_dir=None):
        return self.string_search(type, query_builder.make_query(), page=page, page_size=page_size, sort_by=sort_by, sort_dir=sort_dir)

    def string_search(self, type, query_string, page=1, page_size=10, sort_by=None, sort_dir=None):
        # check this search is against an allowed type
        if type not in self.SEARCH_TYPES:
            raise DOAJException("Type {x} is not a supported search type".format(x=type))

        # construct the url parameters
        params = {"page" : page, "pageSize" : page_size}
        if sort_by is not None:
            sort = sort_by
            if sort_dir is not None:
                sort += ":" + sort_dir
            params["sort"] = sort

        url = self.doaj_url("search", type, additional_path=http.quote(query_string), params=params)
        print(url)

        resp = http.get(url, retry_codes=DOAJ_RETRY_CODES)
        j = resp.json()

        klazz = self.CLASSMAP.get(type)
        if klazz is None:
            raise DOAJException("Type {x} does not have a class representation in the client".format(x=type))

        obs = [klazz(r) for r in j.get("results", [])]
        return obs

    def field_search_iterator(self, type, field, value, quoted=True, page_size=100, sort_by=None, sort_dir=None):
        qb = ANDQueryBuilder()
        qb.add_string_field(field, value, quoted)
        return self.built_search_iterator(type, qb, page_size=page_size, sort_by=sort_by, sort_dir=sort_dir)

    def built_search_iterator(self, type, query_builder, page_size=100, sort_by=None, sort_dir=None):
        return self.string_search_iterator(type, query_builder.make_query(), page_size=page_size, sort_by=sort_by, sort_dir=sort_dir)

    def string_search_iterator(self, type, query_string, page_size=100, sort_by=None, sort_dir=None):
        page = 1
        while True:
            results = self.string_search(type, query_string, page=page, page_size=page_size, sort_by=sort_by, sort_dir=sort_dir)
            if len(results) == 0:
                break
            for r in results:
                yield r
            page += 1

    ###################################################
    ## methods for article CRUD

    def create_article(self, article):
        # support either the article object or the dict representation
        article_data = article
        if isinstance(article, models.Article):
            article_data = article.data

        url = self.doaj_url(type="articles", params={"api_key" : self.api_key})
        resp = http.post(url, data=json.dumps(article_data), headers={"Content-Type" : "application/json"}, retry_codes=DOAJ_RETRY_CODES)

        if resp.status_code == 400:
            raise DOAJException("Bad request against DOAJ API: '{x}'".format(x=resp.json().get("error", "no error provided")))
        elif resp.status_code == 403:
            raise DOAJException("Forbidden action - your API key was incorrect, or you are trying to add an article with an ISSN you don't own")
        elif resp.status_code == 401:
            raise DOAJException("Authentication failed, your API key was probably wrong")

        j = resp.json()
        return j.get("id"), j.get("location")

class ANDQueryBuilder(object):

    def __init__(self):
        self.fields = []

    def add_string_field(self, field, value, quote=True):
        self.fields.append((field, value, quote))

    def make_query(self):
        q = ""
        for field, val, quote in self.fields:
            if q != "":
                q += " AND "
            wrap = "\"" if quote else ""
            q += field + ":" + wrap + val + wrap
        return q



################################################################
# Old DOAJ client for use against the public search endpoint
#
# This is deprecated, and you should use the DOAJCv1API above for full
# access to all Search and CRUD activities

class DOAJSearchClient(object):

    def __init__(self, search_base=None, query_endpoint=None, search_type=None, search_port=None):
        self.search_base = search_base if search_base else app.config.get("DOAJ_BASE_URL", "https://doaj.org")
        self.query_endpoint = query_endpoint if query_endpoint else app.config.get("DOAJ_QUERY_ENDPOINT", "query")
        self.search_type = search_type if search_type else app.config.get("DOAJ_SEARCH_TYPE", "journal,article")
        self.search_port = search_port if search_port else app.config.get("DOAJ_SEARCH_PORT", 80)

        # FIXME: we have turned off SSL verification for the moment, for convenience of working with the new
        # https-everywhere policy of the DOAJ
        self.conn = esprit.raw.Connection(self.search_base, self.query_endpoint, port=self.search_port, verify_ssl=False)

    def object_search(self, query):
        try:
            resp = esprit.raw.search(self.conn, type=self.search_type, query=query, method="GET")
            results = esprit.raw.unpack_result(resp)
            return results
        except:
            app.logger.info("Got exception talking to DOAJ query endpoint")
            return None

    def journals_by_issns(self, issns):
        if not isinstance(issns, list):
            issns = [issns]
        q = IssnQuery("journal", issns)
        return self.object_search(q.query())


class IssnQuery(object):
    def __init__(self, type, issn):
        self.type = type
        self.issn = issn

    def query(self):
        return {
            "query" : {
                "bool" : {
                    "must" : [
                        {"terms" : {"index.issn.exact" : self.issn}},
                        {"term" : {"_type" : self.type}}
                    ]
                }
            }
        }