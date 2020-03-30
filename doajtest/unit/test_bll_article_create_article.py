from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import ArticleFixtureFactory, AccountFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.models import Article, Account, Journal
from portality.lib.paths import rel2abs
from doajtest.mocks.bll_article import BLLArticleMockFactory


def create_article_load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "article_create_article"), "create_article",
                               "test_id",
                               {"test_id": []})


EXCEPTIONS = {
    "ArgumentException": exceptions.ArgumentException,
    "DuplicateArticleException": exceptions.DuplicateArticleException,
    "ArticleNotAcceptable": exceptions.ArticleNotAcceptable
}


def is_acceptable_load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "article_create_article"), "is_acceptable",
                               "test_id",
                               {"test_id": []})


class TestBLLArticleCreateArticle(DoajTestCase):

    def setUp(self):
        super(TestBLLArticleCreateArticle, self).setUp()
        self.svc = DOAJ.articleService()
        self._is_legitimate_owner = self.svc.is_legitimate_owner
        self._issn_ownership_status = self.svc.issn_ownership_status
        self._get_duplicate = self.svc.get_duplicate
        self.__doi_or_fulltext_updated = self.svc._doi_or_fulltext_updated

    def tearDown(self):
        self.svc.is_legitimate_owner = self._is_legitimate_owner
        self.svc.issn_ownership_status = self._issn_ownership_status
        self.svc.get_duplicate = self._get_duplicate
        self.svc._doi_or_fulltext_updated = self.__doi_or_fulltext_updated
        super(TestBLLArticleCreateArticle, self).tearDown()

    @parameterized.expand(create_article_load_cases)
    def test_01_create_article(self, value, kwargs):

        article_arg = kwargs.get("article")
        account_arg = kwargs.get("account")
        get_duplicate_result_arg = kwargs.get("get_duplicate_result")
        role_arg = kwargs.get("role")
        original_saved_arg = kwargs.get("original_saved")
        merge_duplicate_arg = kwargs.get("merge_duplicate")
        add_journal_info_arg = kwargs.get("add_journal_info")
        dry_run_arg = kwargs.get("dry_run")
        update_article_id_arg = kwargs.get("update_article_id")
        has_ft_doi_changed_arg = kwargs.get("has_ft_doi_changed_arg")

        raises_arg = kwargs.get("raises")
        success_arg = kwargs.get("success")
        original_saved_arg = kwargs.get("original_saved")
        merge_saved_arg = kwargs.get("merge_saved")

        ###############################################
        ## set up

        success = int(success_arg)

        has_ft_doi_changed = True if has_ft_doi_changed_arg == "yes" else False

        merge_duplicate = None
        if merge_duplicate_arg != "none":
            merge_duplicate = True if merge_duplicate_arg == "true" else False

        add_journal_info = None
        if add_journal_info_arg != "none":
            add_journal_info = True if add_journal_info_arg == "true" else False

        dry_run = None
        if dry_run_arg != "none":
            dry_run = True if dry_run_arg == "true" else False

        raises = EXCEPTIONS.get(raises_arg)

        eissn = "1234-5678"
        pissn = "9876-5432"
        doi = "10.123/abc/1"
        fulltext = "http://example.com/1"

        another_doi = "10.123/duplicate-1"
        another_fulltext = "http://duplicate.com"

        another_eissn = "1111-1111"
        another_pissn = "2222-2222"

        duplicate_id = None
        original_id = None
        update_article_id = None

        if add_journal_info:
            jsource = JournalFixtureFactory.make_journal_source(in_doaj=True)
            j = Journal(**jsource)
            bj = j.bibjson()
            bj.title = "Add Journal Info Title"
            bj.remove_identifiers()
            bj.add_identifier(bj.P_ISSN, pissn)
            bj.add_identifier(bj.E_ISSN, eissn)
            j.save(blocking=True)

        if get_duplicate_result_arg == 'different':
            source = ArticleFixtureFactory.make_article_source(eissn=another_eissn, pissn=another_pissn, doi=doi,
                                                               fulltext=fulltext)
            del source["bibjson"]["journal"]
            duplicate = Article(**source)
            duplicate.save()
            duplicate_id = duplicate.id

        article_id_to_upload = None
        if article_arg == "exists":
            source = ArticleFixtureFactory.make_article_source(eissn=eissn, pissn=pissn, doi=doi, fulltext=fulltext)
            del source["bibjson"]["journal"]
            article = Article(**source)
            article.set_id()
            article_id_to_upload = article.id

        if get_duplicate_result_arg == "itself":
            source = ArticleFixtureFactory.make_article_source(eissn=another_eissn, pissn=another_pissn, doi=doi,
                                                               fulltext=fulltext)
            del source["bibjson"]["journal"]
            duplicate = Article(**source)
            duplicate.set_id(article_id_to_upload)
            duplicate.save()
            duplicate_id = duplicate.id

        if update_article_id_arg != "none":

            another_source = ArticleFixtureFactory.make_article_source(eissn=eissn, pissn=pissn,
                                                                       doi=doi,
                                                                       fulltext=fulltext)
            original = Article(**another_source)
            original.save(blocking=True)
            original_id = original.id

            if update_article_id_arg == "doi_ft_not_changed":
                article.bibjson().title = "This needs to be updated"

            elif update_article_id_arg == "doi_ft_changed_duplicate":

                article.bibjson().remove_identifiers("doi")
                article.bibjson().add_identifier("doi", another_doi)

            elif update_article_id_arg == "doi_ft_changed_ok":

                article.bibjson().remove_identifiers("doi")
                article.bibjson().add_identifier("doi", "10.1234/updated")

        else:
            update_article_id = None

        account = None
        if account_arg != "none":
            source = AccountFixtureFactory.make_publisher_source()
            account = Account(**source)

        legit = True if account_arg == "owner" else False
        ilo_mock = BLLArticleMockFactory.is_legitimate_owner(legit=legit)
        self.svc.is_legitimate_owner = ilo_mock

        owned = [eissn, pissn] if account_arg == "owner" else []
        shared = []
        unowned = [eissn] if account_arg == "not_owner" else []
        unmatched = [pissn] if account_arg == "not_owner" else []
        ios_mock = BLLArticleMockFactory.issn_ownership_status(owned, shared, unowned, unmatched)
        self.svc.issn_ownership_status = ios_mock

        if role_arg == "admin":
            account.set_role("admin")

        account.save()

        if get_duplicate_result_arg == "none":
            gd_mock = BLLArticleMockFactory.get_duplicate(return_none=True)

        elif get_duplicate_result_arg == "itself":
            gd_mock = BLLArticleMockFactory.get_duplicate(eissn=eissn, pissn=pissn, doi=doi,
                                                          fulltext=fulltext, given_article_id=original_id)
        elif get_duplicate_result_arg == "different":
            gd_mock = BLLArticleMockFactory.get_duplicate(eissn=another_eissn, pissn=another_pissn, doi=doi,
                                                          fulltext=fulltext, given_article_id=duplicate_id)
        else:
            gd_mock = BLLArticleMockFactory.get_duplicate(given_article_id="exception")
        self.svc.get_duplicate = gd_mock
        mock_article = self.svc.get_duplicate(article)

        if role_arg == "admin" or (role_arg == "publisher" and account_arg == "owner"):
            has_permissions_mock = BLLArticleMockFactory.has_permissions(True)
        else:
            has_permissions_mock = BLLArticleMockFactory.has_permissions(False)
        self.svc.has_permissions = has_permissions_mock

        prepare_update_admin_mock = BLLArticleMockFactory._prepare_update_admin(get_duplicate_result_arg,
                                                                                update_article_id_arg)
        self.svc._prepare_update_admin = prepare_update_admin_mock

        prepare_update_publisher_mock = BLLArticleMockFactory._prepare_update_publisher(get_duplicate_result_arg,
                                                                                        has_ft_doi_changed)
        self.svc._prepare_update_publisher = prepare_update_publisher_mock

        ###########################################################
        # Execution

        if raises is not None:
            with self.assertRaises(raises):
                self.svc.create_article(article, account, merge_duplicate=merge_duplicate,
                                        add_journal_info=add_journal_info,
                                        dry_run=dry_run,
                                        update_article_id=original_id)
        else:
            report = self.svc.create_article(article, account, merge_duplicate=merge_duplicate,
                                             add_journal_info=add_journal_info,
                                             dry_run=dry_run,
                                             update_article_id=original_id)

            assert report["success"] == success

            # check that the article was saved and if it was saved that it was suitably merged
            if original_saved_arg == "yes" and update_article_id is not None:
                if get_duplicate_result_arg == "itself":
                    original = Article.pull(update_article_id)
                    assert original is not None
                    assert report["update"] == 1, "update: {}".format(report["update"])
                    assert report["new"] == 0, "update: {}".format(report["new"])
            elif original_saved_arg == "yes":
                if get_duplicate_result_arg == "itself":
                    new = Article.pull(article_id_to_upload)
                    assert new is not None
                    assert report["update"] == 1, "update: {}".format(report["update"])
                    assert report["new"] == 0, "update: {}".format(report["new"])
                elif get_duplicate_result_arg == "none":
                    new = Article.pull(article_id_to_upload)
                    assert new is not None
                    assert report["update"] == 0, "update: {}".format(report["update"])
                    assert report["new"] == 1, "update: {}".format(report["new"])

            if merge_saved_arg == "yes":
                merged = Article.pull(mock_article.id)
                assert merged is not None
                assert report["update"] == 1
            elif mock_article is not None and mock_article.id != original_id:
                merged = Article.pull(mock_article.id)
                assert merged is None, "merged: {}".format(merged)

            if add_journal_info:
                assert article.bibjson().journal_title == "Add Journal Info Title"

            if update_article_id_arg == "doi_ft_changed_ok":
                original = Article.pull(original_id)
                assert original is not None
            elif update_article_id_arg == "doi_ft_not_changed":
                original = Article.pull(original_id)
                assert original is not None


class TestBLLHelpers(DoajTestCase):

    def setUp(self):
        super(TestBLLHelpers, self).setUp()
        self.svc = DOAJ.articleService()

    def tearDown(self):
        super(TestBLLHelpers, self).tearDown()

    @parameterized.expand(is_acceptable_load_cases)
    def test_is_acceptable(self, value, kwargs):
        doi_arg = kwargs.get("doi")
        ft_arg = kwargs.get("fulltext_url")
        is_acceptable_arg = kwargs.get("is_acceptable")

        is_acceptable = True if is_acceptable_arg == "yes" else False
        doi = "10.1234/article-10" if doi_arg == "exists" else None
        ft = "https://example.com" if ft_arg == "exists" else None

        article_source = ArticleFixtureFactory.make_article_source()
        article = Article(**article_source)

        if doi is None:
            article.bibjson().remove_identifiers("doi")
        if ft is None:
            article.bibjson().remove_urls("fulltext")

        if is_acceptable:
            self.assertIsNone(self.svc.is_acceptable(article))

        else:
            with self.assertRaises(exceptions.ArticleNotAcceptable):
                self.svc.is_acceptable(article)

    def test_has_permissions(self):

        journal_source = JournalFixtureFactory.make_journal_source()
        journal1 = Journal(**journal_source)

        publisher_owner_src = AccountFixtureFactory.make_publisher_source()
        publisher_owner = Account(**publisher_owner_src)
        publisher_stranged_src = AccountFixtureFactory.make_publisher_source()
        publisher_stranged = Account(**publisher_stranged_src)
        admin_src = AccountFixtureFactory.make_managing_editor_source()
        admin = Account(**admin_src)

        journal1.set_owner(publisher_owner)
        journal1.save(blocking=True)

        eissn = journal1.bibjson().get_one_identifier("eissn")
        pissn = journal1.bibjson().get_one_identifier("pissn")

        art_source = ArticleFixtureFactory.make_article_source(eissn=eissn,
                                                               pissn=pissn)
        article = Article(**art_source)

        assert self.svc.has_permissions(publisher_stranged, article, False)
        assert self.svc.has_permissions(publisher_owner, article, True)
        assert self.svc.has_permissions(admin, article, True)
        failed_result = self.svc.has_permissions(publisher_stranged, article, True)
        assert failed_result == {'success': 0, 'fail': 1, 'update': 0, 'new': 0, 'shared': [], 'unowned': [pissn, eissn],
                                 'unmatched': []}, "received: {}".format(failed_result)
