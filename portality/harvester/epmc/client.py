from portality.core import app
from portality.lib import httputil
import urllib.request, urllib.parse, urllib.error, string
from portality.harvester.epmc import models
from portality.harvester.epmc.queries import QueryBuilder
from datetime import datetime
import time


def quote(s, **kwargs):
    try:
        return urllib.parse.quote_plus(s, **kwargs)
    except:
        pass

    try:
        utf = s.encode("utf-8")
        return urllib.parse.quote(utf, **kwargs)
    except:
        return None


def check_epmc_version(resp_json):
    try:
        received_ver = resp_json['version']
        configured_ver = app.config.get("EPMC_TARGET_VERSION")
        if received_ver != configured_ver:
            app.logger.warn("Mismatching EPMC API version; recommend checking for changes. Expected '{0}' Found '{1}'".format(configured_ver, received_ver))
    except KeyError:
        app.logger.warn("Couldn't check EPMC API version; did not find 'version' key in response. Proceed with caution as the EPMC API may have changed.")


def to_keywords(s):
    # FIXME: this method does not strip stop words - investigations into that indicate that as a natural language
    # processing thing, the libraries required to do it (e.g. NLTK) are awkward and overblown for our purposes.

    # translate out all of the punctuation
    exclude = set(string.punctuation)
    raw = ''.join(ch if ch not in exclude else " " for ch in s)

    # normalise the spacing
    return " ".join([x for x in raw.split(" ") if x != ""])


class EuropePMCException(Exception):
    def __init__(self, *args, **kwargs):
        httpresponse = kwargs.get("httpresponse")
        if httpresponse is not None:
            del kwargs["httpresponse"]
        super(EuropePMCException, self).__init__(*args)
        self.response = httpresponse


class EPMCFullTextException(Exception):
    def __init__(self, message, rawstring, *args, **kwargs):
        super(EPMCFullTextException, self).__init__(message, *args)
        self.raw = rawstring


class EuropePMC(object):
    @classmethod
    def get_by_pmcid(cls, pmcid, cursor=""):
        return cls.field_search("PMCID", pmcid, cursor=cursor)

    @classmethod
    def get_by_pmid(cls, pmid, cursor=""):
        return cls.field_search("EXT_ID", pmid, cursor=cursor)

    @classmethod
    def get_by_doi(cls, doi, cursor=""):
        return cls.field_search("DOI", doi, cursor=cursor)

    @classmethod
    def title_exact(cls, title, cursor=""):
        return cls.field_search("TITLE", title, cursor=cursor)

    @classmethod
    def title_approximate(cls, title, cursor=""):
        nt = to_keywords(title)
        return cls.field_search("TITLE", nt, fuzzy=True, cursor=cursor)

    @classmethod
    def field_search(cls, field, value, fuzzy=False, cursor="", page_size=25):
        """
        :return: (results, next_cursor)
        """
        qb = QueryBuilder()
        qb.add_string_field(field, value, fuzzy)
        return cls.query(qb.to_url_query_param(), cursor=cursor, page_size=page_size)

    @classmethod
    def field_search_iterator(cls, field, value, fuzzy=False, page_size=25, throttle=None):
        qb = QueryBuilder()
        qb.add_string_field(field, value, fuzzy)
        return cls.iterate(qb.to_url_query_param(), page_size=page_size, throttle=throttle)

    @classmethod
    def complex_search(cls, query_builder, cursor="", page_size=25):
        """
        :return: (results, next_cursor)
        """
        return cls.query(query_builder.to_url_query_param(), cursor=cursor, page_size=page_size)

    @classmethod
    def complex_search_iterator(cls, query_builder, page_size=1000, throttle=None):
        return cls.iterate(query_builder.to_url_query_param(), page_size=page_size, throttle=throttle)

    @classmethod
    def iterate(cls, query_string, page_size=1000, throttle=None):
        cursor = ""
        last = None
        while True:
            if last is not None and throttle is not None:
                diff = (datetime.utcnow() - last).total_seconds()
                app.logger.debug("Last request at {x}, {y}s ago; throttle {z}s".format(x=last, y=diff, z=throttle))
                if diff < throttle:
                    waitfor = throttle - diff
                    app.logger.debug("Throttling EPMC requests for {x}s".format(x=waitfor))
                    time.sleep(waitfor)
            results, cursor = cls.query(query_string, cursor=cursor, page_size=page_size)
            last = datetime.utcnow()
            if len(results) == 0:
                break
            for r in results:
                yield r

    @classmethod
    def query(cls, query_string, cursor="", page_size=25):
        """
        :return: (results, next_cursor)
        """
        quoted = quote(query_string, safe="/")
        qcursor = quote(str(cursor))
        qsize = quote(str(page_size))
        if qsize is None or qcursor is None or quoted is None:
            raise EuropePMCException(None, "unable to url escape the string")

        url = app.config.get("EPMC_REST_API") + "search?query=" + query_string
        url += "&resulttype=core&format=json&pageSize=" + qsize

        if cursor != "":
            url += "&cursorMark=" + qcursor
        app.logger.debug("Requesting EPMC metadata from " + url)

        resp = httputil.get(url)
        if resp is None:
            raise EuropePMCException(message="could not get a response from EPMC")
        if resp.status_code != 200:
            raise EuropePMCException(resp)

        try:
            j = resp.json()
            check_epmc_version(j)
        except:
            raise EuropePMCException(message="could not decode JSON from EPMC response")

        results = [models.EPMCMetadata(r) for r in j.get("resultList", {}).get("result", [])]
        next_cursor_mark = j.get("nextCursorMark", "")
        return results, next_cursor_mark                      # NOTE: previous versions just returned results, not tuple

    @classmethod
    def fulltext(cls, pmcid):
        url = app.config.get("EPMC_REST_API") + pmcid + "/fullTextXML"
        app.logger.debug("Searching for Fulltext at " + url)
        resp = httputil.get(url)
        if resp is None:
            raise EuropePMCException(message="could not get a response for fulltext from EPMC")
        if resp.status_code != 200:
            raise EuropePMCException(resp)
        return EPMCFullText(resp.text)


class EPMCFullText(models.JATS):
    """
    For backwards compatibility - don't add any methods here
    """
    pass
