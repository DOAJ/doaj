from doajtest.fixtures.article_crossref import CrossrefArticleFixtureFactory
from doajtest.fixtures.article_doajxml import DoajXmlArticleFixtureFactory


class FTPMockFactory(object):

    @classmethod
    def create(cls, schema):
        if schema == "doaj":
            return FTPMockDoajFactory
        else:
            return FTPMockCrossrefFactory

    @classmethod
    def sendcmd(cls, *args, **kwargs):
        return "200"

    @classmethod
    def size(cls, *args, **kwargs):
        return 100

    @classmethod
    def close(cls):
        pass

    def retrbinary(self, cmd, callback, chunk_size):
        if self.content is None:
            for i in range(9):
                data = str(i) * chunk_size
                callback(data)
        else:
            callback(self.content)
        return "226"


class FTPMockDoajFactory(FTPMockFactory):

    def __init__(self, hostname,  *args, **kwargs):
        if hostname in ["fail"]:
            raise RuntimeError("Hostname on Fail List")
        self.content = None
        if hostname in ["valid"]:
            self.content = DoajXmlArticleFixtureFactory.upload_1_issn_correct().read()


class FTPMockCrossrefFactory(FTPMockFactory):

    def __init__(self, hostname,  *args, **kwargs):
        if hostname in ["fail"]:
            raise RuntimeError("oops")
        self.content = None
        if hostname in ["valid"]:
            self.content = CrossrefArticleFixtureFactory.upload_1_issn_correct().read()
