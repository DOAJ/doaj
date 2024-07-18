from typing import Dict, List

from doajtest import helpers
from doajtest.fixtures.accounts import AccountFixtureFactory
from doajtest.fixtures.article_doajxml import DoajXmlArticleFixtureFactory
from portality import models
from portality.models.uploads import BaseArticlesUpload


def assert_failed(fu: BaseArticlesUpload,
                  reason_cases: Dict[str, List] = None,
                  reason_size: Dict[str, int] = None,
                  expected_details=None):
    assert fu is not None
    assert fu.status == "failed"
    assert fu.imported == 0
    assert fu.updates == 0
    assert fu.new == 0

    assert fu.error is not None
    assert fu.error != ""

    # assert error details
    if expected_details is None:
        pass
    elif isinstance(expected_details, str):
        assert fu.error_details == expected_details
    elif expected_details:
        assert fu.error_details is not None and fu.error_details != ""
    elif not expected_details:
        assert fu.error_details is None

    # assert failure reasons
    fr = fu.failure_reasons
    if not reason_cases and not reason_size:
        assert list(fr.keys()) == []

    reason_keys = ["shared", "unowned", "unmatched"]
    reason_size = reason_size or {}

    if reason_cases:
        reason_size = {k: len(reason_cases.get(k, [])) for k in reason_keys}

        # assert list match
        for k, expected_cases in reason_cases.items():
            assert set(expected_cases) == set(fr.get(k, set())), f'list mismatch {k} ~ {expected_cases}'

    # assert reason size
    for k, expected_size in reason_size.items():
        assert len(fr.get(k, [])) == expected_size, f'size mismatch {k} ~ {expected_size}'


def assert_processed(fu, target_issns=None, n_abstract=None):
    assert fu is not None
    assert fu.status == "processed"
    assert fu.imported == 1
    assert fu.updates == 0
    assert fu.new == 1

    fr = fu.failure_reasons
    assert len(fr.get("shared", [])) == 0
    assert len(fr.get("unowned", [])) == 0
    assert len(fr.get("unmatched", [])) == 0

    if target_issns is not None:
        found = [a for a in models.Article.find_by_issns(target_issns)]
        assert len(found) == 1
        if n_abstract is not None:
            assert len(found[0].bibjson().abstract) == n_abstract


def create_simple_journal(owner, pissn=None, eissn=None, in_doaj=True, blocking=None):
    j = models.Journal()
    j.set_owner(owner)
    bj1 = j.bibjson()
    if pissn is not None:
        bj1.add_identifier(bj1.P_ISSN, pissn)
    if eissn is not None:
        bj1.add_identifier(bj1.E_ISSN, eissn)
    j.set_in_doaj(in_doaj)
    if blocking is not None:
        j.save(blocking=blocking)
    return j


def create_simple_publisher(user_id, blocking=None):
    asource = AccountFixtureFactory.make_publisher_source()
    account = models.Account(**asource)
    account.set_id(user_id)
    if blocking is not None:
        account.save(blocking=blocking)
    return account


def test_lcc_spelling_error(run_background_process_fn):
    # create a journal with a broken subject classification
    j1 = models.Journal()
    j1.set_owner("testowner1")
    bj1 = j1.bibjson()
    bj1.add_identifier(bj1.P_ISSN, "1234-5678")
    bj1.add_identifier(bj1.E_ISSN, "9876-5432")
    bj1.add_subject("LCC", "Whatever", "WHATEVA")
    bj1.add_subject("LCC", "Aquaculture. Fisheries. Angling", "SH1-691")
    j1.set_in_doaj(True)
    j1.save()

    helpers.save_all_block_last([
        j1,
        create_simple_publisher("testowner1"),
    ])

    handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
    fu = run_background_process_fn("testowner1", handle)
    target_issns = ["1234-5678", "9876-5432"]
    assert_processed(fu, target_issns=target_issns)

    found = [a for a in models.Article.find_by_issns(target_issns)]
    cpaths = found[0].data["index"]["classification_paths"]
    assert len(cpaths) == 1
    assert cpaths[0] == "Agriculture: Aquaculture. Fisheries. Angling"


def test_one_journal_one_article_2_issns_one_unknown(run_background_process_fn):
    # Create one journal and ingest one article.  The Journal has two issns, and the article
    # has two issns, but one of the journal's issns is unknown
    # We expect an ingest failure
    helpers.save_all_block_last([
        create_simple_journal("testowner1", pissn="1234-5678", eissn="2222-2222"),
        create_simple_publisher("testowner1"),
    ])

    handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
    fu = run_background_process_fn("testowner1", handle)
    assert_failed(fu, reason_cases={"unmatched": ["9876-5432"]})
    assert models.Article.count_by_issns(["1234-5678", "9876-5432"]) == 0


def test_unknown_journal_issn(run_background_process_fn):
    # create a journal with one of the ISSNs specified
    helpers.save_all_block_last([
        create_simple_journal("testowner1", pissn="1234-5678"),
        create_simple_publisher("testowner1"),
    ])

    # take an article with 2 issns, but one of which is not in the index
    handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
    fu = run_background_process_fn("testowner1", handle)
    assert_failed(fu, reason_size={"unmatched": 1})


def test_2_journals_different_owners_different_issns_mixed_article_fail(run_background_process_fn):
    # Create 2 different journals with different owners and different issns (2 each).
    # The article's issns match one issn in each journal
    # We expect an ingest failure

    helpers.save_all_block_last([
        create_simple_journal("testowner1", pissn="1234-5678", eissn="2345-6789"),
        create_simple_journal("testowner2", pissn="8765-4321", eissn="9876-5432"),
        create_simple_publisher("testowner1"),
    ])

    handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
    fu = run_background_process_fn("testowner1", handle)
    assert_failed(fu, reason_cases={'unowned': ['9876-5432']})

    assert models.Article.count_by_issns(["1234-5678", "9876-5432"]) == 0


def test_2_journals_same_owner_issn_each_fail(run_background_process_fn):
    # Create 2 journals with the same owner, each with one different issn.  The article's 2 issns
    # match each of these issns
    # We expect a failed article ingest
    helpers.save_all_block_last([
        create_simple_journal("testowner", pissn="1234-5678"),
        create_simple_journal("testowner", eissn="9876-5432"),
        create_simple_publisher("testowner"),
    ])

    handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
    fu = run_background_process_fn("testowner", handle)
    target_issns = ["1234-5678", "9876-5432"]
    assert_failed(fu, reason_size={'unmatched': 2})

    assert models.Article.count_by_issns(["1234-5678", "9876-5432"]) == 0


def test_2_journals_different_owners_issn_each_fail(run_background_process_fn):
    # Create 2 journals with different owners and one different issn each.  The two issns in the
    # article match each of the journals respectively
    # We expect an ingest failure

    user_id = "testowner1"
    helpers.save_all_block_last([
        create_simple_journal(user_id, pissn="1234-5678"),
        create_simple_journal("testowner2", eissn="9876-5432"),
        create_simple_publisher(user_id),
    ])

    handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
    fu = run_background_process_fn(user_id, handle)

    assert_failed(fu, reason_cases={'unowned': ['9876-5432']})
    assert models.Article.count_by_issns(["1234-5678", "9876-5432"]) == 0


def test_2_journals_different_owners_both_issns_fail(run_background_process_fn):
    # Create 2 journals with the same issns but different owners, which match the issns on the article
    # We expect an ingest failure
    helpers.save_all_block_last([
        create_simple_journal("testowner1", pissn="1234-5678", eissn="9876-5432"),
        create_simple_journal("testowner2", pissn="1234-5678", eissn="9876-5432"),
        create_simple_publisher("testowner1"),
    ])

    handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
    fu = run_background_process_fn("testowner1", handle)
    target_issns = ["1234-5678", "9876-5432"]
    assert_failed(fu, reason_cases={'shared': target_issns})
    assert models.Article.count_by_issns(["1234-5678", "9876-5432"]) == 0


def test_journal_2_article_2_1_different_success(run_background_process_fn):
    # Create a journal with 2 issns, one of which is the same as an issn on the
    # article, but the article also contains an issn which doesn't match the journal
    # We expect a failed ingest
    helpers.save_all_block_last([
        create_simple_journal("testowner", pissn="1234-5678", eissn="9876-5432"),
        create_simple_publisher("testowner"),
    ])

    handle = DoajXmlArticleFixtureFactory.upload_2_issns_ambiguous()
    fu = run_background_process_fn("testowner", handle)
    assert_failed(fu, reason_size={"unmatched": 1})
    assert models.Article.count_by_issns(["1234-5678", "9876-5432"]) == 0


def test_journal_1_article_1_success(run_background_process_fn):
    # Create a journal with 1 issn, which is the same 1 issn on the article
    # we expect a successful article ingest
    helpers.save_all_block_last([
        create_simple_journal("testowner", pissn="1234-5678"),
        create_simple_publisher("testowner"),
    ])

    handle = DoajXmlArticleFixtureFactory.upload_1_issn_correct()
    fu = run_background_process_fn("testowner", handle)
    assert_processed(fu, target_issns=["1234-5678"])


def test_journal_1_article_1_superlong_clip(run_background_process_fn):
    # Create a journal with 1 issn, which is the same 1 issn on the article
    # we expect a successful article ingest
    # But it's over 40k unicode characters long!
    helpers.save_all_block_last([
        create_simple_journal("testowner", pissn="1234-5678"),
        create_simple_publisher("testowner"),
    ])

    handle = DoajXmlArticleFixtureFactory.upload_1_issn_superlong_should_clip()
    fu = run_background_process_fn("testowner", handle)
    assert_processed(fu, target_issns=["1234-5678"], n_abstract=30000)


def test_journal_1_article_1_superlong_noclip(run_background_process_fn):
    # Create a journal with 1 issn, which is the same 1 issn on the article
    # we expect a successful article ingest
    # But it's just shy of 30000 unicode characters long!
    helpers.save_all_block_last([
        create_simple_journal("testowner", pissn="1234-5678"),
        create_simple_publisher("testowner"),
    ])

    handle = DoajXmlArticleFixtureFactory.upload_1_issn_superlong_should_not_clip()
    fu = run_background_process_fn("testowner", handle)
    assert_processed(fu, target_issns=["1234-5678"], n_abstract=26264)


def test_journal_2_article_2_success(run_background_process_fn):
    # Create a journal with two issns both of which match the 2 issns in the article
    # we expect a successful article ingest
    acc_id = "testowner"
    helpers.save_all_block_last([
        create_simple_journal(acc_id, pissn="1234-5678", eissn="9876-5432"),
        create_simple_publisher(acc_id),
    ])

    handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()

    job = run_background_process_fn(acc_id, handle)

    assert_processed(job, target_issns=["1234-5678", "9876-5432"])


def test_journal_2_article_1_success(run_background_process_fn):
    # Create a journal with 2 issns, one of which is present in the article as the
    # only issn
    # We expect a successful article ingest
    acc_id = "testowner"
    helpers.save_all_block_last([
        create_simple_journal(acc_id, pissn="1234-5678", eissn="9876-5432"),
        create_simple_publisher(acc_id),
    ])

    handle = DoajXmlArticleFixtureFactory.upload_1_issn_correct()
    job = run_background_process_fn(acc_id, handle)
    assert_processed(job, target_issns=["1234-5678"])


def test_fail_unowned_issn(run_background_process_fn):
    # Create 2 journals with different owners and one different issn each.  The two issns in the
    # article match each of the journals respectively
    # article match each of the journals respectively
    # We expect an ingest failure
    helpers.save_all_block_last([
        create_simple_journal("testowner1", pissn="1234-5678"),
        create_simple_journal("testowner2", eissn="9876-5432"),
        create_simple_publisher("testowner"),
    ])

    handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
    fu = run_background_process_fn("testowner", handle)
    assert_failed(fu, expected_details=False,
                  reason_cases={"unowned": ["9876-5432", '1234-5678']})


def test_fail_shared_issn(run_background_process_fn):
    # Create 2 journals with the same issns but different owners, which match the issns on the article
    # We expect an ingest failure
    helpers.save_all_block_last([
        create_simple_journal("testowner1", pissn="1234-5678", eissn="9876-5432"),
        create_simple_journal("testowner2", pissn="1234-5678", eissn="9876-5432"),
        create_simple_publisher("testowner1"),
    ])

    handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
    fu = run_background_process_fn("testowner1", handle)
    assert_failed(fu, expected_details=False, reason_cases={"shared": ["1234-5678", "9876-5432"]})


def test_submit_success(run_background_process_fn):
    helpers.save_all_block_last([
        create_simple_journal('testowner', pissn='1234-5678'),
        create_simple_publisher("testowner"),
    ])

    handle = DoajXmlArticleFixtureFactory.upload_1_issn_correct()
    fu = run_background_process_fn("testowner", handle)
    assert_processed(fu)


def test_fail_unmatched_issn(run_background_process_fn):
    # Create a journal with 2 issns, one of which is the same as an issn on the
    # article, but the article also contains an issn which doesn't match the journal
    # We expect a failed ingest

    helpers.save_all_block_last([
        create_simple_journal("testowner", pissn="1234-5678", eissn="9876-5432"),
        create_simple_publisher("testowner"),
    ])

    handle = DoajXmlArticleFixtureFactory.upload_2_issns_ambiguous()
    fu = run_background_process_fn("testowner", handle)
    assert_failed(fu, reason_cases={"unmatched": ["2345-6789"]})
