import UserDict, requests, uuid
from copy import deepcopy
from datetime import datetime, timedelta
import time
import re

from portality.core import app
import urllib.request, urllib.error, urllib.parse
import json

import esprit


# All models in models.py should inherit this DomainObject to know how to save themselves in the index and so on.
# You can overwrite and add to the DomainObject functions as required. See models.py for some examples.


ES_MAPPING_MISSING_REGEX = re.compile(r'.*No mapping found for \[[a-zA-Z0-9-_]+?\] in order to sort on.*', re.DOTALL)


class ElasticSearchWriteException(Exception):
    pass


class DomainObject(UserDict.IterableUserDict, object):
    __type__ = None                                                       # set the type on the model that inherits this

    def __init__(self, **kwargs):
        # if self.data is already set, don't do anything here
        try:
            object.__getattribute__(self, "data")
        except:
            if '_source' in kwargs:
                self.data = dict(kwargs['_source'])
                self.meta = dict(kwargs)
                del self.meta['_source']
            else:
                self.data = dict(kwargs)
        # FIXME: calling super() breaks everything, even thought this is the correct thing to do
        # this is because the DomainObject incorrectly overrides properties of the super class
        # super(DomainObject, self).__init__()

    @classmethod
    def target_whole_index(cls):
        t = str(app.config['ELASTIC_SEARCH_HOST']).rstrip('/') + '/'
        t += app.config['ELASTIC_SEARCH_DB'] + '/'
        return t
            
    @classmethod
    def target(cls):
        t = cls.target_whole_index()
        t += cls.__type__ + '/'
        return t
    
    @classmethod
    def makeid(cls):
        """Create a new id for data object overwrite this in specific model types if required"""
        return str(uuid.uuid4().hex)

    @property
    def id(self):
        rawid = self.data.get("id", None)
        if rawid is not None:
            return str(rawid)
        return None
    
    def set_id(self, id=None):
        if id is None:
            id = self.makeid()
        self.data["id"] = str(id)
    
    @property
    def version(self):
        return self.meta.get('_version', None)

    @property
    def json(self):
        return json.dumps(self.data)
    
    def set_created(self, date=None):
        if date is None:
            self.data['created_date'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            self.data['created_date'] = date

    @property
    def created_date(self):
        return self.data.get("created_date")

    @property
    def created_timestamp(self):
        return datetime.strptime(self.data.get("created_date"), "%Y-%m-%dT%H:%M:%SZ")
    
    @property
    def last_updated(self):
        return self.data.get("last_updated")

    @property
    def last_updated_timestamp(self):
        return datetime.strptime(self.last_updated, "%Y-%m-%dT%H:%M:%SZ")

    def save(self, retries=0, back_off_factor=1, differentiate=False, blocking=False):

        if app.config.get("READ_ONLY_MODE", False) and app.config.get("SCRIPTS_READ_ONLY_MODE", False):
            app.logger.warn("System is in READ-ONLY mode, save command cannot run")
            return

        if 'id' not in self.data:
            self.data['id'] = self.makeid()

        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        if (blocking or differentiate) and "last_updated" in self.data:
            diff = datetime.now() - datetime.strptime(self.data["last_updated"], "%Y-%m-%dT%H:%M:%SZ")

            # we need the new last_updated time to be later than the new one
            if diff.total_seconds() < 1:
                soon = datetime.utcnow() + timedelta(seconds=1)
                now = soon.strftime("%Y-%m-%dT%H:%M:%SZ")

        self.data['last_updated'] = now

        if 'created_date' not in self.data:
            self.data['created_date'] = now

        attempt = 0
        url = self.target() + self.data['id']
        d = json.dumps(self.data)
        r = None
        while attempt <= retries:
            try:
                r = requests.post(url, data=d)
                if r.status_code > 400:
                    raise ElasticSearchWriteException("Error on ES save. Response code {0}".format(r.status_code))
                else:
                    break  # everything is OK, so r should now be assigned to the result

            except requests.exceptions.ConnectionError:
                app.logger.exception("Failed to connect to ES")
                attempt += 1
            except ElasticSearchWriteException:
                try:
                    error_details = r.json()
                except (ValueError, AttributeError):
                    error_details = r.text

                # Retries depend on which end the error lies.
                if 400 <= r.status_code < 500:
                    # Bad request, do not retry as it won't work. Fail with ElasticSearchWriteException.
                    app.logger.exception("Bad Request to ES, save failed. Details: {0}".format(error_details))
                    raise
                elif r.status_code >= 500:
                    # Server error, this could be temporary so we may want to retry
                    app.logger.exception("Server Error from ES, retrying. Details: {0}".format(error_details))
                    attempt += 1
            except Exception:
                # if any other exception occurs, make sure it's at least logged.
                app.logger.exception("Unhandled exception in save method of DAO")
                raise

            # wait before retrying
            time.sleep((2**attempt) * back_off_factor)

        if attempt > retries:
            raise DAOSaveExceptionMaxRetriesReached(
                "After {attempts} attempts the record with "
                "id {id} failed to save.".format(
                    attempts=attempt, id=self.data['id']))

        if blocking:
            q = {
                "query": {
                    "term": {"id.exact": self.id}
                },
                "fields": ["last_updated"]
            }
            while True:
                res = self.query(q=q, return_raw_resp=True)
                j = esprit.raw.unpack_result(res)
                if len(j) == 0:
                    time.sleep(0.25)
                    continue
                if len(j) > 1:
                    raise Exception("More than one record with id {x}".format(x=self.id))
                if j[0].get("last_updated", [])[0] == now:  # NOTE: only works on ES > 1.x
                    break
                else:
                    time.sleep(0.25)
                    continue

        return r

    @classmethod
    def bulk(cls, bibjson_list, idkey='id', refresh=False):
        if app.config.get("READ_ONLY_MODE", False) and app.config.get("SCRIPTS_READ_ONLY_MODE", False):
            app.logger.warn("System is in READ-ONLY mode, bulk command cannot run")
            return

        data = ''
        for r in bibjson_list:
            data += json.dumps({'index': {'_id': r[idkey]}}) + '\n'
            data += json.dumps(r) + '\n'
        r = requests.post(cls.target() + '_bulk', data=data)
        if refresh:
            cls.refresh()
        return r.json()

    @classmethod
    def refresh(cls):
        if app.config.get("READ_ONLY_MODE", False) and app.config.get("SCRIPTS_READ_ONLY_MODE", False):
            app.logger.warn("System is in READ-ONLY mode, refresh command cannot run")
            return

        r = requests.post(cls.target() + '_refresh')
        return r.json()

    @classmethod
    def pull(cls, id_):
        """Retrieve object by id."""
        if id_ is None:
            return None

        # swallow any network exceptions
        try:
            out = requests.get(cls.target() + id_)
        except Exception as e:
            return None
        if out is None:
            return None

        # allow other exceptions to bubble up, as they may be data structure exceptions we want to know about
        if out.status_code == 404:
            return None
        else:
            return cls(**out.json())

    @classmethod
    def pull_by_key(cls, key, value):
        res = cls.query(q={"query": {"term": {key+app.config['FACET_FIELD']: value}}})
        if res.get('hits', {}).get('total', 0) == 1:
            return cls.pull(res['hits']['hits'][0]['_source']['id'])
        else:
            return None

    @classmethod
    def es_keys(cls, mapping=False, prefix=''):
        # return a sorted list of all the keys in the index
        if not mapping:
            mapping = cls.query(endpoint='_mapping')[cls.__type__]['properties']
        keys = []
        for item in mapping:
            if 'fields' in mapping[item]:
                for itm in list(mapping[item]['fields'].keys()):
                    if itm != 'exact' and not itm.startswith('_'):
                        keys.append(prefix + itm + app.config['FACET_FIELD'])
            else:
                keys = keys + cls.es_keys(mapping=mapping[item]['properties'], prefix=prefix+item+'.')
        keys.sort()
        return keys
        
    @staticmethod
    def make_query(recid='', endpoint='_search', theq='', terms=None, facets=None, should_terms=None, consistent_order=True, **kwargs):
        """
        Generate a query object based on parameters but don't send to
        backend - return it instead. Must always have the same
        parameters as the query method. See query method for explanation
        of parameters.
        """
        q = deepcopy(theq)
        if recid and not recid.endswith('/'):
            recid += '/'
        if isinstance(q, dict):
            query = q
            if 'bool' not in query['query']:
                boolean = {'bool': {'must': []}}
                boolean['bool']['must'].append(query['query'])
                query['query'] = boolean
            if 'must' not in query['query']['bool']:
                query['query']['bool']['must'] = []
        elif q:
            query = {
                'query': {
                    'bool': {
                        'must': [
                            {'query_string': {'query': q}}
                        ]
                    }
                }
            }
        else:
            query = {
                'query': {
                    'bool': {
                        'must': [
                            {'match_all': {}}
                        ]
                    }
                }
            }

        if facets:
            if 'facets' not in query:
                query['facets'] = {}
            for k, v in list(facets.items()):
                query['facets'][k] = {"terms": v}

        if terms:
            boolean = {'must': []}
            for term in terms:
                if not isinstance(terms[term], list):
                    terms[term] = [terms[term]]
                for val in terms[term]:
                    obj = {'term': {}}
                    obj['term'][term] = val
                    boolean['must'].append(obj)
            if q and not isinstance(q, dict):
                boolean['must'].append({'query_string': {'query': q}})
            elif q and 'query' in q:
                boolean['must'].append(query['query'])
            query['query'] = {'bool': boolean}

        # FIXME: this may only work if a term is also supplied above - code is a bit tricky to read
        if should_terms is not None and len(should_terms) > 0:
            for s in should_terms:
                if not isinstance(should_terms[s], list):
                    should_terms[s] = [should_terms[s]]
                query["query"]["bool"]["must"].append({"terms": {s: should_terms[s]}})

        sort_specified = False
        for k, v in list(kwargs.items()):
            if k == '_from':
                query['from'] = v
            elif k == 'sort':
                sort_specified = True
                query['sort'] = v
            else:
                query[k] = v
        if "sort" in query:
            sort_specified = True

        if not sort_specified and consistent_order:
            query['sort'] = [{"id": {"order": "asc"}}]

        # print json.dumps(query)
        return query

    @classmethod
    def query(cls, recid='', endpoint='_search', q='', terms=None, facets=None, return_raw_resp=False, raise_es_errors=False, **kwargs):
        """Perform a query on backend.

        :param recid: needed if endpoint is about a record, e.g. mlt
        :param endpoint: default is _search, but could be _mapping, _mlt, _flt etc.
        :param q: maps to query_string parameter if string, or query dict if dict.
        :param terms: dictionary of terms to filter on. values should be lists. 
        :param facets: dict of facets to return from the query.
        :param kwargs: any keyword args as per
            http://www.elasticsearch.org/guide/reference/api/search/uri-request.html
        """
        query = cls.make_query(recid, endpoint, q, terms, facets, **kwargs)
        return cls.send_query(query, endpoint=endpoint, recid=recid, return_raw_resp=return_raw_resp, raise_es_errors=raise_es_errors)

    @classmethod
    def send_query(cls, qobj, endpoint='_search', recid='', retry=50, return_raw_resp=False, raise_es_errors=False):
        """Actually send a query object to the backend."""
        r = None
        count = 0
        exception = None
        while count < retry:
            count += 1
            try:
                if endpoint in ['_mapping']:
                    r = requests.get(cls.target() + recid + endpoint)
                else:
                    r = requests.post(cls.target() + recid + endpoint, data=json.dumps(qobj))
                break
            except Exception as e:
                exception = e
            time.sleep(0.5)
                
        if r is not None:
            j = r.json()

            if raise_es_errors:
                cls.check_es_raw_response(j)

            if return_raw_resp:
                return r

            return j
        if exception is not None:
            raise exception
        raise Exception("Couldn't get the ES query endpoint to respond.  Also, you shouldn't be seeing this.")

    def delete(self):
        if app.config.get("READ_ONLY_MODE", False) and app.config.get("SCRIPTS_READ_ONLY_MODE", False):
            app.logger.warn("System is in READ-ONLY mode, delete command cannot run")
            return

        r = requests.delete(self.target() + self.id)
    
    @classmethod
    def remove_by_id(cls, id):
        if app.config.get("READ_ONLY_MODE", False) and app.config.get("SCRIPTS_READ_ONLY_MODE", False):
            app.logger.warn("System is in READ-ONLY mode, delete_by_id command cannot run")
            return

        r = requests.delete(cls.target() + id)

    @classmethod
    def delete_by_query(cls, query):
        if app.config.get("READ_ONLY_MODE", False) and app.config.get("SCRIPTS_READ_ONLY_MODE", False):
            app.logger.warn("System is in READ-ONLY mode, delete_by_query command cannot run")
            return

        r = requests.delete(cls.target() + "_query", data=json.dumps(query))
        return r

    @classmethod
    def destroy_index(cls):
        if app.config.get("READ_ONLY_MODE", False) and app.config.get("SCRIPTS_READ_ONLY_MODE", False):
            app.logger.warn("System is in READ-ONLY mode, destroy_index command cannot run")
            return

        r = requests.delete(cls.target_whole_index())
        return r
    
    def update(self, doc):
        """
        add the provided doc to the existing object
        """
        if app.config.get("READ_ONLY_MODE", False) and app.config.get("SCRIPTS_READ_ONLY_MODE", False):
            app.logger.warn("System is in READ-ONLY mode, update command cannot run")
            return

        return requests.post(self.target() + self.id + "/_update", data=json.dumps({"doc": doc}))
    
    @classmethod
    def delete_all(cls):
        if app.config.get("READ_ONLY_MODE", False) and app.config.get("SCRIPTS_READ_ONLY_MODE", False):
            app.logger.warn("System is in READ-ONLY mode, delete_all command cannot run")
            return

        r = requests.delete(cls.target())
        r = requests.put(cls.target() + '_mapping', json.dumps(app.config['MAPPINGS'][cls.__type__]))

    @classmethod
    def check_es_raw_response(cls, res, extra_trace_info=''):
        if 'error' in res:
            es_resp = json.dumps(res, indent=2)

            error_to_raise = ESMappingMissingError if ES_MAPPING_MISSING_REGEX.match(es_resp) else ESError

            raise error_to_raise(
                (
                    "Elasticsearch returned an error:"
                    "\nES HTTP Response status: {es_status}"
                    "\nES Response:{es_resp}"
                    .format(es_status=res.get('status', 'unknown'), es_resp=es_resp)
                ) + extra_trace_info
            )

        if 'hits' not in res and 'hits' not in res['hits']:  # i.e. if res['hits']['hits'] does not exist
            raise ESResponseCannotBeInterpreted(
                (
                    "Elasticsearch did not return any records. "
                    "It probably returned an error we did not understand instead."
                    "\nES HTTP Response status: {es_status}"
                    "\nES Response:{es_resp}\n"
                    .format(es_status=res.get('status', 'unknown'), es_resp=json.dumps(res, indent=2))
                    ) + extra_trace_info
            )
        return True

    @classmethod
    def handle_es_raw_response(cls, res, wrap, extra_trace_info=''):
        """
        Handles the JSON returned by ES, raising errors as needed. If no problems are detected it returns its input
        unchanged.

        :param res: The full ES raw response to a query in a Python dict (this method does not handle the raw JSON ES
        outputs). Usually this parameter is the return value of the .query or .send_query methods.
        :param wrap: Did the caller request wrapping of each ES record inside a model object? This matters for handling
        records that have no '_source' or 'fields' keys, but do have an '_id' key. Such records should raise an error
        if wrapping was requested, since there is nothing to wrap. If no wrapping was requested, perhaps the caller
        simply needed the object IDs and nothing else, so we do not need to raise an error.
        :param extra_trace_info: A string with additional diagnostic information to be put into exceptions.
        """

        cls.check_es_raw_response(res)

        rs = []
        for i, each in enumerate(res['hits']['hits']):
            if '_source' in each:
                rs.append(each['_source'])
            elif 'fields' in each:
                rs.append(each['fields'])
            elif '_id' in each and not wrap:
                # "_id" is a sibling (not child) of "_source" so it can only be used with unwrapped raw responses.
                # wrap = True only makes sense if "_source" or "fields" were returned.
                # So, if "_id" is the only one present, extract it into an object that's shaped the same as the item
                # in the raw response.
                rs.append({"_id": each['_id']})
            else:
                msg1 = "Can't find any useful data in the ES response.\n" + extra_trace_info
                msg2 = "\nItem {i}.\nItem data:\n{each}".format(i=i, each=json.dumps(each, indent=2))
                raise ESResponseCannotBeInterpreted(msg1 + msg2)

        return rs

    @classmethod
    def iterate(cls, q, page_size=1000, limit=None, wrap=True):
        theq = deepcopy(q)
        theq["size"] = page_size
        theq["from"] = 0
        if "sort" not in theq:             # to ensure complete coverage on a changing index, sort by id is our best bet
            theq["sort"] = [{"_id": {"order": "asc"}}]
        counter = 0
        while True:
            # apply the limit
            if limit is not None and counter >= limit:
                break
            
            res = cls.query(q=theq)
            rs = cls.handle_es_raw_response(
                res,
                wrap=wrap,
                extra_trace_info=
                    "\nQuery sent to ES:\n{q}\n"
                    "\n\nPage #{counter} of the ES response with size {page_size}."
                    .format(q=json.dumps(theq, indent=2), counter=counter, page_size=page_size)
            )

            if len(rs) == 0:
                break
            for r in rs:
                # apply the limit (again)
                if limit is not None and counter >= limit:
                    break
                counter += 1
                if wrap:
                    yield cls(**r)
                else:
                    yield r
            theq["from"] += page_size   
    
    @classmethod
    def iterall(cls, page_size=1000, limit=None):
        return cls.iterate(deepcopy(all_query), page_size, limit)

    @classmethod
    def prefix_query(cls, field, prefix, size=5, facet_field=None, analyzed_field=True):
        # example of a prefix query
        # {
        #     "query": {"prefix" : { "bibjson.publisher" : "ope" } },
        #     "size": 0,
        #     "facets" : {
        #       "publisher" : { "terms" : {"field" : "bibjson.publisher.exact", "size": 5} }
        #     }
        # }

        suffix = app.config['FACET_FIELD']
        query_field = field
        if analyzed_field:
            if field.endswith(suffix):
                # strip .exact (or whatever it's configured as) off the end
                query_field = field[:field.rfind(suffix)]
        else:
            if not field.endswith(suffix):
                query_field = field + suffix

        # the actual terms should come from the .exact version of the
        # field - we are suggesting whole values, not fragments
        if facet_field is None:
            facet_field = query_field + suffix
        if not facet_field.endswith(suffix):
            facet_field = facet_field + suffix

        q = {
            "query": {"prefix": {query_field: prefix.lower()}},
            "size": 0,
            "facets": {
              field: {"terms": {"field": facet_field, "size": size}}
            }
        }

        return cls.send_query(q)

    @classmethod
    def wildcard_autocomplete_query(cls, field, substring, before=True, after=True, facet_size=5, facet_field=None):
        """
        Example of a wildcard query
        Works only on .exact fields

        {
            "query" : {
                "wildcard" : {"bibjson.publisher.exact" : "De *"}
            },
            "size" : 0,
            "facets" : {
                "bibjson.publisher.exact" : {
                    "terms" : {"field" : "bibjson.publisher.exact", "size" : 5}
                }
            }
        }
        :param field:
        :param substring:
        :param facet_size:
        :return:
        """
        # wildcard queries need to be on unanalyzed fields
        suffix = app.config['FACET_FIELD']
        filter_field = field
        if not filter_field.endswith(suffix):
            filter_field = filter_field + suffix

        # add the wildcard before/after
        if before:
            substring = "*" + substring
        if after:
            substring = substring + "*"

        # sort out the facet field
        if facet_field is None:
            facet_field = filter_field
        if not facet_field.endswith(suffix):
            facet_field = facet_field + suffix

        # build the query
        q = {
            "query": {
                "wildcard": {filter_field: substring}
            },
            "size": 0,
            "facets": {
                field: {
                    "terms": {"field": facet_field, "size": facet_size}
                }
            }
        }

        return cls.send_query(q)

    @classmethod
    def advanced_autocomplete(cls, filter_field, facet_field, substring, size=5, prefix_only=True):
        analyzed = True
        if " " in substring:
            analyzed = False

        substring = substring.lower()

        if " " in substring and not prefix_only:
            res = cls.wildcard_autocomplete_query(filter_field, substring, before=True, after=True, facet_size=size, facet_field=facet_field)
        else:
            res = cls.prefix_query(filter_field, substring, size=size, facet_field=facet_field, analyzed_field=analyzed)

        result = []
        for term in res['facets'][filter_field]['terms']:
            # keep ordering - it's by count by default, so most frequent
            # terms will now go to the front of the result list
            result.append({"id": term['term'], "text": term['term']})
        return result

    @classmethod
    def autocomplete(cls, field, prefix, size=5):
        res = None
        # if there is a space in the prefix, the prefix query won't work, so we fall back to a wildcard
        # we only do this if we have to, because the wildcard query is a little expensive
        if " " in prefix:
            res = cls.wildcard_autocomplete_query(field, prefix, before=False, after=True, facet_size=size)
        else:
            prefix = prefix.lower()
            res = cls.prefix_query(field, prefix, size=size)

        result = []
        for term in res['facets'][field]['terms']:
            # keep ordering - it's by count by default, so most frequent
            # terms will now go to the front of the result list
            result.append({"id": term['term'], "text": term['term']})
        return result

    @classmethod
    def q2obj(cls, **kwargs):
        extra_trace_info = ''
        if 'q' in kwargs:
            extra_trace_info = "\nQuery sent to ES (before manipulation in DomainObject.query):\n{}\n".format(json.dumps(kwargs['q'], indent=2))

        res = cls.query(**kwargs)
        rs = cls.handle_es_raw_response(res, wrap=True, extra_trace_info=extra_trace_info)
        results = [cls(**r) for r in rs]
        return results

    @classmethod
    def all(cls, size=10000000, **kwargs):
        return cls.q2obj(size=size, **kwargs)

    @classmethod
    def count(cls):
        return requests.get(cls.target() + '_count').json()['count']

    @classmethod
    def hit_count(cls, query, **kwargs):
        res = cls.query(q=query, **kwargs)

        return res.get("hits", {}).get("total", 0)

    @classmethod
    def block(cls, id, last_updated, sleep=0.5, max_retry_seconds=30):
        threshold = datetime.strptime(last_updated, "%Y-%m-%dT%H:%M:%SZ")
        query = deepcopy(block_query)
        query["query"]["bool"]["must"][0]["term"]["id.exact"] = id
        start_time = datetime.now()
        while True:
            res = cls.query(q=query)
            hits = res.get("hits", {}).get("hits", [])
            if len(hits) > 0:
                obj = hits[0].get("fields")
                if "last_updated" in obj:
                    lu = obj["last_updated"]
                    if len(lu) > 0:
                        lud = datetime.strptime(lu[0], "%Y-%m-%dT%H:%M:%SZ")
                        if lud >= threshold:
                            return
            else:
                if (datetime.now() - start_time).total_seconds() >= max_retry_seconds:
                    raise BlockTimeOutException("Attempting to block until record with id {id} appears in Elasticsearch, but this has not happened after {limit}".format(id=id, limit=max_retry_seconds))

            time.sleep(sleep)

    @classmethod
    def blockall(cls, ids_and_last_updateds, sleep=0.05, individual_max_retry_seconds=30):
        for id, lu in ids_and_last_updateds:
            cls.block(id, lu, sleep=sleep, max_retry_seconds=individual_max_retry_seconds)


class BlockTimeOutException(Exception):
    pass


class DAOSaveExceptionMaxRetriesReached(Exception):
    pass


class ESResponseCannotBeInterpreted(Exception):
    pass


class ESMappingMissingError(Exception):
    pass


class ESError(Exception):
    pass

########################################################################
# Some useful ES queries
########################################################################

all_query = { 
    "query": {
        "match_all": {}
    }
}

block_query = {
    "query": {
        "bool": {
            "must": [
                {"term": {"id.exact": "<identifier>"}}
            ]
        }
    },
    "fields": ["last_updated"]
}

#########################################################################
# A query handler that knows how to speak facetview2
#########################################################################


class Facetview2(object):

    """
    {"query":{"filtered":{"filter":{"bool":{"must":[{"term":{"_type":"article"}}]}},"query":{"query_string":{"query":"richard","default_operator":"OR"}}}},"from":0,"size":10}
    {"query":{"query_string":{"query":"richard","default_operator":"OR"}},"from":0,"size":10}
    """

    @staticmethod
    def make_term_filter(term, value):
        return {"term": {term: value}}

    @staticmethod
    def make_query(query_string=None, filters=None, default_operator="OR", sort_parameter=None, sort_order="asc"):
        query_part = {"match_all": {}}
        if query_string is not None:
            query_part = {"query_string": {"query": query_string, "default_operator": default_operator}}
        query = {"query": query_part}

        if filters is not None:
            if not isinstance(filters, list):
                filters = [filters]
            bool_part = {"bool": {"must": filters}}
            query = {"query": {"filtered": {"query": query_part, "filter": bool_part}}}

        if sort_parameter is not None:
            # For facetview we can only have one sort parameter, but ES actually supports lists
            sort_part = [{sort_parameter: {"order": sort_order}}]
            query["sort"] = sort_part

        return query

    @staticmethod
    def url_encode_query(query):
        return urllib.parse.quote(json.dumps(query).replace(' ', ''))
