from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import DoajXmlArticleFixtureFactory, AccountFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.models import Article, Account,Journal
from portality.lib.paths import rel2abs
from doajtest.mocks.bll_article import BLLArticleMockFactory
from doajtest.mocks.model_Article import ModelArticleMockFactory
from portality.dao import ESMappingMissingError

import time

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "article_batch_create_article"), "batch_create_article", "test_id",
                               {"test_id" : []})

EXCEPTIONS = {
    "ArgumentException" : exceptions.ArgumentException,
    "DuplicateArticleException" : exceptions.DuplicateArticleException,
    "IngestException" : exceptions.IngestException
}

class TestBLLArticleBatchCreateArticle(DoajTestCase):

    def setUp(self):
        super(TestBLLArticleBatchCreateArticle, self).setUp()
        self.svc = DOAJ.articleService()
        self._is_legitimate_owner = self.svc.is_legitimate_owner
        self._get_duplicate = self.svc.get_duplicate
        self._issn_ownership_status = self.svc.issn_ownership_status
        self._get_journal = Article.get_journal


    def tearDown(self):
        self.svc.is_legitimate_owner = self._is_legitimate_owner
        self.svc.get_duplicate = self._get_duplicate
        self.svc.issn_ownership_status = self._issn_ownership_status
        Article.get_journal = self._get_journal
        super(TestBLLArticleBatchCreateArticle, self).tearDown()

    @parameterized.expand(load_cases)
    def test_01_batch_create_article(self, name, kwargs):

        articles_arg = kwargs.get("articles")
        duplicate_in_batch_arg = kwargs.get("duplicate_in_batch")
        duplicate_in_index_arg = kwargs.get("duplicate_in_index")
        account_arg = kwargs.get("account")
        duplicate_check_arg = kwargs.get("duplicate_check")
        merge_duplicate_arg = kwargs.get("merge_duplicate")
        limit_to_account_arg = kwargs.get("limit_to_account")
        add_journal_info_arg = kwargs.get("add_journal_info")

        raises_arg = kwargs.get("raises")
        success_arg = kwargs.get("success")
        fail_arg = kwargs.get("fail")
        update_arg = kwargs.get("update")

        ###############################################
        ## set up

        success = int(success_arg)
        fail = int(fail_arg)
        update = int(update_arg)

        duplicate_in_batch = duplicate_in_batch_arg == "yes"
        duplicate_in_index = int(duplicate_in_index_arg)

        raises = EXCEPTIONS.get(raises_arg)

        duplicate_check = None
        if duplicate_check_arg != "none":
            duplicate_check = True if duplicate_check_arg == "true" else False

        merge_duplicate = None
        if merge_duplicate_arg != "none":
            merge_duplicate = True if merge_duplicate_arg == "true" else False

        limit_to_account = None
        if limit_to_account_arg != "none":
            limit_to_account = True if limit_to_account_arg == "true" else False

        add_journal_info = None
        if add_journal_info_arg != "none":
            add_journal_info = True if add_journal_info_arg == "true" else False

        account = None
        if account_arg != "none":
            source = AccountFixtureFactory.make_publisher_source()
            account = Account(**source)

        journal_specs = []
        last_doi = None
        last_ft = None
        last_issn = None
        last_id = None
        articles = None
        if articles_arg != "none":
            articles = []
            if articles_arg == "yes":
                # one with a DOI and no fulltext
                source = DoajXmlArticleFixtureFactory.make_article_source(
                    eissn="0000-0000",
                    pissn="0000-0000",
                    doi="10.123/abc/0",
                    fulltext=False
                )
                del source["bibjson"]["journal"]
                article = Article(**source)
                article.set_id()
                articles.append(article)
                if add_journal_info:
                    journal_specs.append({"title" : "0", "pissn" : "0000-0000", "eissn" : "0000-0000"})

                # another with a DOI and no fulltext
                source = DoajXmlArticleFixtureFactory.make_article_source(
                    eissn="1111-1111",
                    pissn="1111-1111",
                    doi="10.123/abc/1",
                    fulltext=False
                )
                del source["bibjson"]["journal"]
                article = Article(**source)
                article.set_id()
                articles.append(article)
                if add_journal_info:
                    journal_specs.append({"title" : "1", "pissn" : "1111-1111", "eissn" : "1111-1111"})

                # one with a fulltext and no DOI
                source = DoajXmlArticleFixtureFactory.make_article_source(
                    eissn="2222-2222",
                    pissn="2222-2222",
                    fulltext="http://example.com/2",
                    doi=False
                )
                del source["bibjson"]["journal"]
                article = Article(**source)
                article.set_id()
                articles.append(article)
                if add_journal_info:
                    journal_specs.append({"title" : "2", "pissn" : "2222-2222", "eissn" : "2222-2222"})

                # another one with a fulltext and no DOI
                source = DoajXmlArticleFixtureFactory.make_article_source(
                    eissn="3333-3333",
                    pissn="3333-3333",
                    fulltext="http://example.com/3",
                    doi=False
                )
                del source["bibjson"]["journal"]
                article = Article(**source)
                article.set_id()
                articles.append(article)
                if add_journal_info:
                    journal_specs.append({"title" : "3", "pissn" : "3333-3333", "eissn" : "3333-3333"})

                last_issn = "3333-3333"
                last_doi = "10.123/abc/1"
                last_ft = "http://example.com/3"
                last_id = articles[-1].id

                if duplicate_in_batch:
                    # one with a duplicated DOI
                    source = DoajXmlArticleFixtureFactory.make_article_source(
                        eissn="4444-4444",
                        pissn="4444-4444",
                        doi="10.123/abc/0",
                        fulltext="http://example.com/4"
                    )
                    del source["bibjson"]["journal"]
                    article = Article(**source)
                    article.set_id()
                    articles.append(article)
                    if add_journal_info:
                        journal_specs.append({"title" : "4", "pissn" : "4444-4444", "eissn" : "4444-4444"})

                    # one with a duplicated Fulltext
                    source = DoajXmlArticleFixtureFactory.make_article_source(
                        eissn="5555-5555",
                        pissn="5555-5555",
                        doi="10.123/abc/5",
                        fulltext="http://example.com/1"
                    )
                    del source["bibjson"]["journal"]
                    article = Article(**source)
                    article.set_id()
                    articles.append(article)
                    if add_journal_info:
                        journal_specs.append({"title" : "5", "pissn" : "5555-5555", "eissn" : "5555-5555"})

        ilo_mock = None
        if account_arg == "owner":
            ilo_mock = BLLArticleMockFactory.is_legitimate_owner(legit=True)
        elif account_arg == "own_1":
            ilo_mock = BLLArticleMockFactory.is_legitimate_owner(legit_on_issn=[last_issn])
        else:
            ilo_mock = BLLArticleMockFactory.is_legitimate_owner()
        self.svc.is_legitimate_owner = ilo_mock

        gd_mock = None
        if duplicate_in_index == 1:
            gd_mock = BLLArticleMockFactory.get_duplicate(given_article_id=last_id, eissn=last_issn, pissn=last_issn, doi=last_doi, fulltext=last_ft)
        elif duplicate_in_index == 2:
            gd_mock = BLLArticleMockFactory.get_duplicate(merge_conflict=True)
        else:
            gd_mock = BLLArticleMockFactory.get_duplicate(return_none=True)
        self.svc.get_duplicate = gd_mock

        ios_mock = BLLArticleMockFactory.issn_ownership_status([], [], [], [])
        self.svc.issn_ownership_status = ios_mock

        if add_journal_info:
            gj_mock = ModelArticleMockFactory.get_journal(journal_specs)
            Article.get_journal = gj_mock

        ###########################################################
        # Execution

        if raises is not None:
            with self.assertRaises(raises):
                try:
                    self.svc.batch_create_articles(articles, account, duplicate_check, merge_duplicate,
                                                   limit_to_account, add_journal_info)
                except exceptions.IngestException as e:
                    if duplicate_in_index != 2:
                        report = e.result
                        assert report["success"] == success
                        assert report["fail"] == fail
                        assert report["update"] == update
                        assert report["new"] == success - update
                    raise
        else:
            report = self.svc.batch_create_articles(articles, account, duplicate_check, merge_duplicate,
                                                    limit_to_account, add_journal_info)

            # make sure all the articles are saved before running the asserts
            aids = [(a.id, a.last_updated) for a in articles]
            for aid, lu in aids:
                Article.block(aid, lu, sleep=0.05)

            assert report["success"] == success
            assert report["fail"] == fail
            assert report["update"] == update
            assert report["new"] == success - update

            if success > 0:
                all_articles = Article.all()
                if len(all_articles) != success:
                    time.sleep(0.5)
                    all_articles = Article.all()
                assert len(all_articles) == success
                for article in all_articles:
                    if add_journal_info:
                        assert article.bibjson().journal_title is not None
                    else:
                        assert article.bibjson().journal_title is None

            else:
                # there's nothing in the article index
                with self.assertRaises(ESMappingMissingError):
                    Article.all()