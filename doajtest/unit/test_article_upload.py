from doajtest.helpers import DoajTestCase
from doajtest.fixtures.article import ArticleFixtureFactory
from portality import article, models
import uuid, time

class TestArticleUpload(DoajTestCase):

    def setUp(self):
        super(TestArticleUpload, self).setUp()

    def tearDown(self):
        super(TestArticleUpload, self).tearDown()

    def test_01_journal_2_article_2_success(self):
        # Create a journal with two issns both of which match the 2 issns in the article
        # we expect a successful article ingest

        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.save()

        time.sleep(2)

        handle = ArticleFixtureFactory.upload_2_issns_correct()
        results = article.ingest_file(handle, format_name="doaj", owner="testowner", upload_id=None)

        assert results["success"] == 1
        assert results["fail"] == 0
        assert results["update"] == 0
        assert results["new"] == 1
        assert len(results["shared"]) == 0
        assert len(results["unowned"]) == 0
        assert len(results["unmatched"]) == 0

        time.sleep(2)

        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 1

    def test_02_journal_2_article_1_success(self):
        # Create a journal with 2 issns, one of which is present in the article as the
        # only issn
        # We expect a successful article ingest

        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.save()

        time.sleep(2)

        handle = ArticleFixtureFactory.upload_1_issn_correct()
        results = article.ingest_file(handle, format_name="doaj", owner="testowner", upload_id=None)

        assert results["success"] == 1
        assert results["fail"] == 0
        assert results["update"] == 0
        assert results["new"] == 1
        assert len(results["shared"]) == 0
        assert len(results["unowned"]) == 0
        assert len(results["unmatched"]) == 0

        time.sleep(2)

        found = [a for a in models.Article.find_by_issns(["1234-5678"])]
        assert len(found) == 1

    def test_03_journal_1_article_2_success(self):
        # Create a journal with 1 issn, which is one of the 2 issns on the article
        # we expect a successful article ingest

        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.save()

        time.sleep(2)

        handle = ArticleFixtureFactory.upload_2_issns_correct()
        results = article.ingest_file(handle, format_name="doaj", owner="testowner", upload_id=None)

        assert results["success"] == 1
        assert results["fail"] == 0
        assert results["update"] == 0
        assert results["new"] == 1
        assert len(results["shared"]) == 0
        assert len(results["unowned"]) == 0
        assert len(results["unmatched"]) == 0

        time.sleep(2)

        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 1

    def test_04_journal_1_article_1_success(self):
        # Create a journal with 1 issn, which is the same 1 issn on the article
        # we expect a successful article ingest

        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save()

        time.sleep(2)

        handle = ArticleFixtureFactory.upload_1_issn_correct()
        results = article.ingest_file(handle, format_name="doaj", owner="testowner", upload_id=None)

        assert results["success"] == 1
        assert results["fail"] == 0
        assert results["update"] == 0
        assert results["new"] == 1
        assert len(results["shared"]) == 0
        assert len(results["unowned"]) == 0
        assert len(results["unmatched"]) == 0

        time.sleep(2)

        found = [a for a in models.Article.find_by_issns(["1234-5678"])]
        assert len(found) == 1

    def test_05_journal_2_article_2_1_different_success(self):
        # Create a journal with 2 issns, one of which is the same as an issn on the
        # article, but the article also contains an issn which doesn't match the journal
        # We expect a failed ingest

        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.save()

        time.sleep(2)

        handle = ArticleFixtureFactory.upload_2_issns_ambiguous()
        results = article.ingest_file(handle, format_name="doaj", owner="testowner", upload_id=None)

        assert results["success"] == 0
        assert results["fail"] == 1
        assert results["update"] == 0
        assert results["new"] == 0

        assert len(results["shared"]) == 0
        assert len(results["unowned"]) == 0
        assert len(results["unmatched"]) == 1

        time.sleep(2)

        found = [a for a in models.Article.find_by_issns(["1234-5678", "2345-6789"])]
        assert len(found) == 0

    def test_05_2_journals_different_owners_both_issns_fail(self):
        # Create 2 journals with the same issns but different owners, which match the issns on the article
        # We expect an ingest failure

        legit_fail = {"fail" : 0}
        def fail_callback_closure(register):
            def fail_callback(article):
                register["fail"] += 1
            return fail_callback

        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        bj1.add_identifier(bj1.E_ISSN, "9876-5432")
        j1.save()

        j2 = models.Journal()
        j2.set_owner("testowner2")
        j2.set_in_doaj(False)
        bj2 = j2.bibjson()
        bj2.add_identifier(bj2.P_ISSN, "1234-5678")
        bj2.add_identifier(bj2.E_ISSN, "9876-5432")
        j2.save()

        time.sleep(2)

        handle = ArticleFixtureFactory.upload_2_issns_correct()
        results = article.ingest_file(handle, format_name="doaj", owner="testowner1", upload_id=None, article_fail_callback=fail_callback_closure(legit_fail))

        assert results["success"] == 0
        assert results["fail"] == 1
        assert results["update"] == 0
        assert results["new"] == 0

        assert len(results["shared"]) == 2
        assert "1234-5678" in results["shared"]
        assert "9876-5432" in results["shared"]
        assert len(results["unowned"]) == 0
        assert len(results["unmatched"]) == 0

        assert legit_fail["fail"] == 1

        time.sleep(2)

        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 0

    def test_06_2_journals_different_owners_issn_each_fail(self):
        # Create 2 journals with different owners and one different issn each.  The two issns in the
        # article match each of the journals respectively
        # We expect an ingest failure

        legit_fail = {"fail" : 0}
        def fail_callback_closure(register):
            def fail_callback(article):
                register["fail"] += 1
            return fail_callback

        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        j1.save()

        j2 = models.Journal()
        j2.set_owner("testowner2")
        j2.set_in_doaj(False)
        bj2 = j2.bibjson()
        bj2.add_identifier(bj2.E_ISSN, "9876-5432")
        j2.save()

        time.sleep(2)

        handle = ArticleFixtureFactory.upload_2_issns_correct()
        results = article.ingest_file(handle, format_name="doaj", owner="testowner1", upload_id=None, article_fail_callback=fail_callback_closure(legit_fail))

        assert results["success"] == 0
        assert results["fail"] == 1
        assert results["update"] == 0
        assert results["new"] == 0

        assert len(results["shared"]) == 0
        assert len(results["unowned"]) == 1
        assert "9876-5432" in results["unowned"]
        assert len(results["unmatched"]) == 0

        assert legit_fail["fail"] == 1

        time.sleep(2)

        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 0

    def test_07_2_journals_same_owner_issn_each_success(self):
        # Create 2 journals with the same owner, each with one different issn.  The article's 2 issns
        # match each of these issns
        # We expect a successful article ingest

        j1 = models.Journal()
        j1.set_owner("testowner")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        j1.save()

        j2 = models.Journal()
        j2.set_owner("testowner")
        j2.set_in_doaj(False)
        bj2 = j2.bibjson()
        bj2.add_identifier(bj2.E_ISSN, "9876-5432")
        j2.save()

        time.sleep(2)

        handle = ArticleFixtureFactory.upload_2_issns_correct()
        results = article.ingest_file(handle, format_name="doaj", owner="testowner", upload_id=None)

        assert results["success"] == 1
        assert results["fail"] == 0
        assert results["update"] == 0
        assert results["new"] == 1

        assert len(results["shared"]) == 0
        assert len(results["unowned"]) == 0
        assert len(results["unmatched"]) == 0

        time.sleep(2)

        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 1

    def test_08_2_journals_different_owners_different_issns_mixed_article_fail(self):
        # Create 2 different journals with different owners and different issns (2 each).
        # The article's issns match one issn in each journal
        # We expect an ingest failure

        legit_fail = {"fail" : 0}
        def fail_callback_closure(register):
            def fail_callback(article):
                register["fail"] += 1
            return fail_callback

        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        bj1.add_identifier(bj1.E_ISSN, "2345-6789")
        j1.save()

        j2 = models.Journal()
        j2.set_owner("testowner2")
        j2.set_in_doaj(False)
        bj2 = j2.bibjson()
        bj2.add_identifier(bj2.P_ISSN, "8765-4321")
        bj2.add_identifier(bj2.E_ISSN, "9876-5432")
        j2.save()

        time.sleep(2)

        handle = ArticleFixtureFactory.upload_2_issns_correct()
        results = article.ingest_file(handle, format_name="doaj", owner="testowner1", upload_id=None, article_fail_callback=fail_callback_closure(legit_fail))

        assert results["success"] == 0
        assert results["fail"] == 1
        assert results["update"] == 0
        assert results["new"] == 0

        assert len(results["shared"]) == 0
        assert len(results["unowned"]) == 1
        assert "9876-5432" in results["unowned"]
        assert len(results["unmatched"]) == 0

        assert legit_fail["fail"] == 1

        time.sleep(2)

        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 0

    def test_09_duplication(self):
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.save()

        time.sleep(2)

        # make both handles, as we want as little gap as possible between requests in a moment
        handle1 = ArticleFixtureFactory.upload_2_issns_correct()
        handle2 = ArticleFixtureFactory.upload_2_issns_correct()

        # pile both requests in as fast as possible
        results1 = article.ingest_file(handle1, format_name="doaj", owner="testowner", upload_id=None)
        results2 = article.ingest_file(handle2, format_name="doaj", owner="testowner", upload_id=None)

        assert results1["success"] == 1
        assert results2["success"] == 1

        # now let's check that only one article got created
        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 1

    def test_10_journal_1_article_1_superlong_noclip(self):
        # Create a journal with 1 issn, which is the same 1 issn on the article
        # we expect a successful article ingest
        # But it's just shy of 30000 unicode characters long!

        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save()

        time.sleep(2)

        handle = ArticleFixtureFactory.upload_1_issn_superlong_should_not_clip()
        results = article.ingest_file(handle, format_name="doaj", owner="testowner", upload_id=None)

        assert results["success"] == 1
        assert results["fail"] == 0
        assert results["update"] == 0
        assert results["new"] == 1

        assert len(results["shared"]) == 0
        assert len(results["unowned"]) == 0
        assert len(results["unmatched"]) == 0

        time.sleep(2)

        found = [a for a in models.Article.find_by_issns(["1234-5678"])]
        assert len(found) == 1
        assert len(found[0].bibjson().abstract) == 26264, len(found[0].bibjson().abstract)

    def test_11_journal_1_article_1_superlong_clip(self):
        # Create a journal with 1 issn, which is the same 1 issn on the article
        # we expect a successful article ingest
        # But it's over 40k unicode characters long!

        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save()

        time.sleep(2)
        handle = ArticleFixtureFactory.upload_1_issn_superlong_should_clip()
        results = article.ingest_file(handle, format_name="doaj", owner="testowner", upload_id=None)

        assert results["success"] == 1
        assert results["fail"] == 0
        assert results["update"] == 0
        assert results["new"] == 1

        assert len(results["shared"]) == 0
        assert len(results["unowned"]) == 0
        assert len(results["unmatched"]) == 0

        time.sleep(2)

        found = [a for a in models.Article.find_by_issns(["1234-5678"])]
        assert len(found) == 1
        assert len(found[0].bibjson().abstract) == 30000, len(found[0].bibjson().abstract)

    def test_12_one_journal_one_article_2_issns_one_unknown(self):
        # Create 2 journals with different owners and one different issn each.  The two issns in the
        # article match each of the journals respectively
        # We expect an ingest failure

        legit_fail = {"fail" : 0}
        def fail_callback_closure(register):
            def fail_callback(article):
                register["fail"] += 1
            return fail_callback

        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        bj1.add_identifier(bj1.P_ISSN, "2222-2222")
        j1.save()

        time.sleep(2)

        handle = ArticleFixtureFactory.upload_2_issns_correct()
        results = article.ingest_file(handle, format_name="doaj", owner="testowner1", upload_id=None, article_fail_callback=fail_callback_closure(legit_fail))

        assert results["success"] == 0
        assert results["fail"] == 1
        assert results["update"] == 0
        assert results["new"] == 0

        assert len(results["shared"]) == 0
        assert len(results["unowned"]) == 0
        assert len(results["unmatched"]) == 1
        assert "9876-5432" in results["unmatched"]

        assert legit_fail["fail"] == 1

        time.sleep(2)

        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 0
