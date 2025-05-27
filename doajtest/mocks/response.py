from doajtest.fixtures.article_crossref import Crossref442ArticleFixtureFactory, Crossref531ArticleFixtureFactory
from doajtest.fixtures.article_doajxml import DoajXmlArticleFixtureFactory
import requests

GET = requests.get


class ResponseMockFactory(object):

    @classmethod
    def head_success(cls, url, *args, **kwargs):
        return Response(200)

    @classmethod
    def head_fail(cls, url, *args, **kwargs):
        return Response(405)

    @classmethod
    def doaj_get_success(cls, url, *args, **kwargs):
        if url in ["http://success", "http://upload"]:
            return Response(200)
        elif url in ["http://valid"]:
            return Response(200, DoajXmlArticleFixtureFactory.upload_1_issn_correct().read())
        return GET(url, **kwargs)

    @classmethod
    def crossref442_get_success(cls, url, *args, **kwargs):
        if url in ["http://success", "http://upload"]:
            return Response(200)
        elif url in ["http://valid"]:
            return Response(200, Crossref442ArticleFixtureFactory.upload_1_issn_correct().read())
        return GET(url, **kwargs)

    @classmethod
    def crossref531_get_success(cls, url, *args, **kwargs):
        if url in ["http://success", "http://upload"]:
            return Response(200)
        elif url in ["http://valid"]:
            return Response(200, Crossref531ArticleFixtureFactory.upload_1_issn_correct().read())
        return GET(url, **kwargs)

    @classmethod
    def get_fail(cls, url, *args, **kwargs):
        if url in ["http://fail"]:
            return Response(405)
        if url in ["http://except"]:
            raise RuntimeError("oops")
        return GET(url, **kwargs)

    @classmethod
    def get_file(cls, url_file_map:dict, *args, **kwargs):
        def get_closure(url, **kwargs):
            if url in url_file_map.keys():
                return Response(200, url_file_map[url].read())
            return GET(url, **kwargs)
        return get_closure

    @classmethod
    def get_failure(cls, url_fail_map:dict, *args, **kwargs):
        def get_closure(url, **kwargs):
            if url in url_fail_map.keys():
                return Response(url_fail_map[url][0], url_fail_map[url][1])
            return GET(url, **kwargs)
        return get_closure


class Response(object):
    def __init__(self, code, content=None):
        self.status_code = code
        self.headers = {"content-length": 100}
        self.content = content

    def close(self):
        pass

    def iter_content(self, chunk_size=100):
        if self.content is None:
            for i in range(9):
                yield str(i) * chunk_size
        else:
            yield self.content

    @property
    def text(self):
        if self.content is None:
            return ""
        return self.content.decode('utf-8') if isinstance(self.content, bytes) else self.content
