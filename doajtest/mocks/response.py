from doajtest.fixtures.article_crossref import CrossrefArticleFixtureFactory
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
    def crossref_get_success(cls, url, *args, **kwargs):
        if url in ["http://success", "http://upload"]:
            return Response(200)
        elif url in ["http://valid"]:
            return Response(200, CrossrefArticleFixtureFactory.upload_1_issn_correct().read())
        return GET(url, **kwargs)

    @classmethod
    def get_fail(cls, url, *args, **kwargs):
        if url in ["http://fail"]:
            return Response(405)
        if url in ["http://except"]:
            raise RuntimeError("oops")
        return GET(url, **kwargs)


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
