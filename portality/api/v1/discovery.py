from portality.api.v1.common import Api
from portality import util
from portality.core import app
from datetime import datetime
import esprit
import re, json, uuid, os
from copy import deepcopy
from flask import url_for
from portality.bll.doaj import DOAJ

class DiscoveryException(Exception):
    pass

class SearchResult(object):
    def __init__(self, raw=None):
        self.data = raw if raw is not None else {}

def query_substitute(query, substitutions):
    if len(substitutions.keys()) == 0:
        return query

    # apply the regex escapes to the substitutions, so we know they
    # are ready to be matched
    escsubs = {}
    for k, v in substitutions.iteritems():
        escsubs[k.replace(":", "\\:")] = v

    # define a function which takes the match group and returns the
    # substitution if there is one
    def rep(match):
        for k, v in escsubs.iteritems():
            if k == match.group(1):
                return v
        return match.group(1)

    # define the regular expressions for splitting and then extracting
    # the field to be substituted
    split_rx = "([^\\\\]:)"
    field_rx = "([^\s\+\-\(\)\"]+?):$"

    # split the query around any unescaped colons
    bits = re.split(split_rx, query)

    # stitch back together the split sections and the separators
    segs = [bits[i] + bits[i+1] for i in range(0, len(bits), 2) if i+1 < len(bits)] + [bits[len(bits) - 1]] if len(bits) % 2 == 1 else []

    # substitute the fields as required
    subs = []
    for seg in segs:
        if seg.endswith(":"):
            subs.append(re.sub(field_rx, rep, seg))
        else:
            subs.append(seg)

    return ":".join(subs)

def allowed(query, wildcards=False, fuzzy=False):
    if not wildcards:
        rx = "(.+[^\\\\][\?\*]+.*)"
        if re.search(rx, query):
            return False

    if not fuzzy:
        # this covers both fuzzy searching and proximity searching
        rx = "(.+[^\\\\]~[0-9]{0,1}[\.]{0,1}[0-9]{0,1})"
        if re.search(rx, query):
            return False

    return True

def escape(query):
    # just escapes all instances of "/" in the query with "\\/"

    # Function which does the replacement
    def slasher(m):
        return m.group(0)[0] + "\\/"


    # the regular expression which looks for an unescaped /
    slash_rx = "[^\\\\]/"

    # because the regex matches two characters, neighbouring /s will not both
    # get replaced at the same time because re.sub looks at "non overlapping matches".
    # This means "//" will not be properly escaped.  So, we run the re.subn
    # function repeatedly until the number of replacements drops to 0
    count = 1
    while count > 0:
        query, count = re.subn(slash_rx, slasher, query)

    return query

DISCOVERY_API_SWAG = {}
DISCOVERY_API_SWAG['application'] = json.loads(util.load_file(os.path.join(app.config['BASE_FILE_PATH'], 'api', 'v1', 'discovery_api_application_swag.json')))
DISCOVERY_API_SWAG['journal'] = json.loads(util.load_file(os.path.join(app.config['BASE_FILE_PATH'], 'api', 'v1', 'discovery_api_journal_swag.json')))
DISCOVERY_API_SWAG['article'] = json.loads(util.load_file(os.path.join(app.config['BASE_FILE_PATH'], 'api', 'v1', 'discovery_api_article_swag.json')))

class DiscoveryApi(Api):

    @staticmethod
    def get_application_swag():
        return deepcopy(DISCOVERY_API_SWAG['application'])

    @staticmethod
    def get_journal_swag():
        return deepcopy(DISCOVERY_API_SWAG['journal'])

    @staticmethod
    def get_article_swag():
        return deepcopy(DISCOVERY_API_SWAG['article'])

    @classmethod
    def _sanitise(cls, q, page, page_size, sort, search_subs, sort_subs):
        if not allowed(q):
            raise DiscoveryException("Query contains disallowed Lucene features")

        q = query_substitute(q, search_subs)
        q = escape(q)
        # print q

        # sanitise the page size information
        if page < 1:
            page = 1

        if page_size > app.config.get("DISCOVERY_MAX_PAGE_SIZE", 100):
            page_size = app.config.get("DISCOVERY_MAX_PAGE_SIZE", 100)
        elif page_size < 1:
            page_size = 10

        # calculate the position of the from cursor in the document set
        fro = (page - 1) * page_size

        # interpret the sort field into the form required by the query
        sortby = None
        sortdir = None
        if sort is not None:
            if ":" in sort:
                bits = sort.split(":")
                if len(bits) != 2:
                    raise DiscoveryException("Malformed sort parameter")

                sortby = bits[0]
                if sortby in sort_subs:
                    sortby = sort_subs[sortby]

                if bits[1] in ["asc", "desc"]:
                    sortdir = bits[1]
                else:
                    raise DiscoveryException("Sort direction must be 'asc' or 'desc'")
            else:
                sortby = sort
                if sortby in sort_subs:
                    sortby = sort_subs[sortby]

        return q, page, fro, page_size, sortby, sortdir

    @classmethod
    def _make_query(cls, index_type, account, q, page, page_size, sort, search_subs, sort_subs):
        # sanitise and prep the inputs
        q, page, fro, page_size, sortby, sortdir = cls._sanitise(q, page, page_size, sort, search_subs, sort_subs)

        # assemble the query
        search_query = SearchQuery(index_type, account, q, fro, page_size, sortby, sortdir)
        query, dao_klass = search_query.query()
        # print json.dumps(query)

        return dao_klass, query, page, page_size


    @staticmethod
    def _calc_pagination(total, page_size, requested_page):
        """
        Calculate pagination for API results like # of pages and the last page.

        Modified from https://github.com/Pylons/paginate/blob/master/paginate/__init__.py#L260 ,
        a pagination library. (__init__.py, Page.__init__)
        """
        FISRT_PAGE = 1

        if total == 0:
            return 1, None, None, 1

        page_count = ((total - 1) // page_size) + 1
        last_page = FISRT_PAGE + page_count - 1

        # Links to previous and next page
        if requested_page > FISRT_PAGE:
            previous_page = requested_page - 1
        else:
            previous_page = None

        if requested_page < last_page:
            next_page = requested_page + 1
        else:
            next_page = None

        return page_count, previous_page, next_page, last_page

    @classmethod
    def _make_response(cls, endpoint, res, q, page, page_size, sort,
                       obs):
        total = res.get("hits", {}).get("total", 0)

        page_count, previous_page, next_page, last_page = cls._calc_pagination(total, page_size, page)

        # build the response object
        result = {
            "total" : total,
            "page" : page,
            "pageSize" : page_size,
            "timestamp" : datetime.utcnow().strftime("%Y-%m%dT%H:%M:%SZ"),
            "query" : q,
            "results" : obs
        }

        if previous_page is not None:
            result["prev"] = app.config['BASE_URL'] + url_for(app.config['API_BLUEPRINT_NAME'] + '.' + endpoint, search_query=q, page=previous_page, pageSize=page_size, sort=sort)

        if next_page is not None:
            result["next"] = app.config['BASE_URL'] + url_for(app.config['API_BLUEPRINT_NAME'] + '.' + endpoint, search_query=q, page=next_page, pageSize=page_size, sort=sort)

        if last_page is not None:
            result["last"] = app.config['BASE_URL'] + url_for(app.config['API_BLUEPRINT_NAME'] + '.' + endpoint, search_query=q, page=last_page, pageSize=page_size, sort=sort)

        if sort is not None:
            result["sort"] = sort

        return SearchResult(result)

    @classmethod
    def search_articles(cls, q, page, page_size, sort=None):
        search_subs = app.config.get("DISCOVERY_ARTICLE_SEARCH_SUBS", {})
        sort_subs = app.config.get("DISCOVERY_ARTICLE_SORT_SUBS", {})
        dao_klass, query, page, page_size = cls._make_query('article', None, q, page, page_size, sort, search_subs, sort_subs)

        # execute the query against the articles
        res = dao_klass.query(q=query.as_dict(), consistent_order=False)

        # check to see if there was a search error
        if res.get("error") is not None:
            magic = uuid.uuid1()
            app.logger.error("Error executing discovery query search: {x} (ref: {y})".format(x=res.get("error"), y=magic))
            raise DiscoveryException("There was an error executing your query (ref: {y})".format(y=magic))

        obs = [dao_klass(**raw) for raw in esprit.raw.unpack_json_result(res)]
        return cls._make_response('search_articles', res, q, page, page_size, sort, obs)

    @classmethod
    def search_journals(cls, q, page, page_size, sort=None):
        search_subs = app.config.get("DISCOVERY_JOURNAL_SEARCH_SUBS", {})
        sort_subs = app.config.get("DISCOVERY_JOURNAL_SORT_SUBS", {})
        dao_klass, query, page, page_size = cls._make_query('journal', None, q, page, page_size, sort, search_subs, sort_subs)

        # execute the query against the articles
        res = dao_klass.query(q=query.as_dict(), consistent_order=False)

        # check to see if there was a search error
        if res.get("error") is not None:
            magic = uuid.uuid1()
            app.logger.error("Error executing discovery query search: {x} (ref: {y})".format(x=res.get("error"), y=magic))
            raise DiscoveryException("There was an error executing your query (ref: {y})".format(y=magic))

        obs = [dao_klass(**raw) for raw in esprit.raw.unpack_json_result(res)]
        return cls._make_response('search_journals', res, q, page, page_size, sort, obs)

    @classmethod
    def search_applications(cls, account, q, page, page_size, sort=None):
        search_subs = app.config.get("DISCOVERY_APPLICATION_SEARCH_SUBS", {})
        sort_subs = app.config.get("DISCOVERY_APPLICATION_SORT_SUBS", {})
        dao_klass, query, page, page_size = cls._make_query('suggestion', account, q, page, page_size, sort, search_subs, sort_subs)

        # execute the query against the articles
        res = dao_klass.query(q=query.as_dict(), consistent_order=False)

        # check to see if there was a search error
        if res.get("error") is not None:
            magic = uuid.uuid1()
            app.logger.error("Error executing discovery query search: {x} (ref: {y})".format(x=res.get("error"), y=magic))
            raise DiscoveryException("There was an error executing your query (ref: {y})".format(y=magic))

        obs = [dao_klass(**raw) for raw in esprit.raw.unpack_json_result(res)]
        return cls._make_response('search_applications', res, q, page, page_size, sort, obs)


class SearchQuery(object):
    def __init__(self, index_type, account, qs, fro, psize, sortby=None, sortdir=None):
        self.index_type = index_type
        self.account = account
        self.qs = qs
        self.fro = fro
        self.psize = psize
        self.sortby = sortby
        self.sortdir = sortdir if sortdir is not None else "asc"

    def query(self):
        q = {
            "query" : {
                "query_string" : {
                    "query" : self.qs,
                    "default_operator": "AND"
                }
            },
            "from" : self.fro,
            "size" : self.psize
        }
        if self.sortby is not None:
            q["sort"] = [{self.sortby : {"order" : self.sortdir, "mode" : "min"}}]

        query_service = DOAJ.queryService()
        query, dao_klass = query_service.prepare_query('api_query', self.index_type, q, self.account)
        return query, dao_klass
