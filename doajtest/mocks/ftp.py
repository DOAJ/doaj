from doajtest.fixtures.article_crossref import Crossref442ArticleFixtureFactory, Crossref531ArticleFixtureFactory
from doajtest.fixtures.article_doajxml import DoajXmlArticleFixtureFactory


class FTPMockFactory(object):

    @classmethod
    def create(cls, schema):
        if schema == "doaj":
            return FTPMockDoajFactory
        elif schema == "crossref442":
            return FTPMockCrossref442Factory
        elif schema == "crossref531":
            return FTPMockCrossref531Factory

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


class FTPMockCrossref442Factory(FTPMockFactory):

    def __init__(self, hostname,  *args, **kwargs):
        if hostname in ["fail"]:
            raise RuntimeError("oops")
        self.content = None
        if hostname in ["valid"]:
            self.content = Crossref442ArticleFixtureFactory.upload_1_issn_correct().read()

class FTPMockCrossref531Factory(FTPMockCrossref442Factory):

    def __init__(self, hostname,  *args, **kwargs):
        if hostname in ["fail"]:
            raise RuntimeError("oops")
        self.content = None
        if hostname in ["valid"]:
            self.content = Crossref531ArticleFixtureFactory.upload_1_issn_correct().read()
