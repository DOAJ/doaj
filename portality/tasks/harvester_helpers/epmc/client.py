from portality.core import app
from portality.lib import httputil
import urllib.request, urllib.parse, urllib.error, string

from portality.settings import BASE_FILE_PATH
from portality.tasks.harvester_helpers.epmc import models
from portality.tasks.harvester_helpers.epmc.queries import QueryBuilder
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

    def __init__(self):
        self.logger = ""

    def get_by_pmcid(self, pmcid, cursor=""):
        return self.field_search("PMCID", pmcid, cursor=cursor)


    def get_by_pmid(self, pmid, cursor=""):
        return self.field_search("EXT_ID", pmid, cursor=cursor)


    def get_by_doi(self, doi, cursor=""):
        return self.field_search("DOI", doi, cursor=cursor)


    def title_exact(self, title, cursor=""):
        return self.field_search("TITLE", title, cursor=cursor)


    def title_approximate(self, title, cursor=""):
        nt = to_keywords(title)
        return self.field_search("TITLE", nt, fuzzy=True, cursor=cursor)


    def field_search(self, field, value, fuzzy=False, cursor="", page_size=25):
        """
        :return: (results, next_cursor)
        """
        qb = QueryBuilder()
        qb.add_string_field(field, value, fuzzy)
        return self.query(qb.to_url_query_param(), cursor=cursor, page_size=page_size)


    def field_search_iterator(self, field, value, fuzzy=False, page_size=25, throttle=None):
        qb = QueryBuilder()
        qb.add_string_field(field, value, fuzzy)
        return self.iterate(qb.to_url_query_param(), page_size=page_size, throttle=throttle)


    def complex_search(self, query_builder, cursor="", page_size=25):
        """
        :return: (results, next_cursor)
        """
        return self.query(query_builder.to_url_query_param(), cursor=cursor, page_size=page_size)


    def complex_search_iterator(self, query_builder, page_size=1000, throttle=None):
        return self.iterate(query_builder.to_url_query_param(), page_size=page_size, throttle=throttle)


    def _write_to_logger(self, msg):
        self.logger = self.logger + "\n" + msg


    def iterate(self, query_string, page_size=1000, throttle=None):
        cursor = ""
        last = None
        while True:
            if last is not None and throttle is not None:
                diff = (datetime.utcnow() - last).total_seconds()
                self._write_to_logger("Last request at {x}, {y}s ago; throttle {z}s".format(x=last, y=diff, z=throttle))
                if diff < throttle:
                    waitfor = throttle - diff
                    self._write_to_logger("Throttling EPMC requests for {x}s".format(x=waitfor))
                    time.sleep(waitfor)
            results, cursor = self.query(query_string, cursor=cursor, page_size=page_size)
            last = datetime.utcnow()
            if len(results) == 0:
                break
            for r in results:
                yield r


    def url_from_query(self, query_string, cursor, page_size):
        quoted = quote(query_string, safe="/")
        qsize = quote(str(page_size))
        qcursor = quote(str(cursor))

        if qsize is None or quoted is None or qcursor is None:
            raise EuropePMCException(None, "unable to url escape the string")

        url = app.config.get("EPMC_REST_API") + "search?query=" + query_string
        url += "&resulttype=core&format=json&pageSize=" + qsize

        if cursor != "":
            url += "&cursorMark=" + qcursor

        return url


    def query(self, query_string, cursor="", page_size=25):
        """
        :return: (results, next_cursor)
        """
        url = self.url_from_query(query_string, cursor, page_size)
        self._write_to_logger("Requesting EPMC metadata from " + url)

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


    def fulltext(self, pmcid):
        url = app.config.get("EPMC_REST_API") + pmcid + "/fullTextXML"
        self._write_to_logger("Searching for Fulltext at " + url)
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
