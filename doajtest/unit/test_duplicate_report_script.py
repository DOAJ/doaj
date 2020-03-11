""" Test the duplicate reporting and deletion script """

from portality.core import app
from doajtest.helpers import DoajTestCase
from doajtest.fixtures import ArticleFixtureFactory
from portality.tasks import article_duplicate_report
from portality.lib import paths
from portality import models
from portality.lib import dates

from collections import OrderedDict

import time
import os
import shutil
import csv

TMP_DIR = paths.rel2abs(__file__, "resources/article_duplicates_report")


class TestArticleMatch(DoajTestCase):

    def setUp(self):
        super(TestArticleMatch, self).setUp()
        if os.path.exists(TMP_DIR):
            shutil.rmtree(TMP_DIR)
        os.mkdir(TMP_DIR)

    def tearDown(self):
        super(TestArticleMatch, self).tearDown()
        shutil.rmtree(TMP_DIR)

    def test_01_duplicates_report(self):
        """Check duplication reporting across all articles in the index"""

        # Create 2 identical articles, a duplicate pair
        article1 = models.Article(**ArticleFixtureFactory.make_article_source(
            eissn='1111-1111',
            pissn='2222-2222',
            with_id=False,
            in_doaj=True,
            with_journal_info=True
        ))
        a1_doi = article1.bibjson().get_identifiers('doi')
        assert a1_doi is not None
        article1.save(blocking=True)

        time.sleep(1)

        article2 = models.Article(**ArticleFixtureFactory.make_article_source(
            eissn='1111-1111',
            pissn='2222-2222',
            with_id=False,
            in_doaj=True,
            with_journal_info=True
        ))
        a2_doi = article2.bibjson().get_identifiers('doi')
        assert a2_doi == a1_doi
        article2.save(blocking=True)

        # Run the reporting task
        user = app.config.get("SYSTEM_USERNAME")
        job = article_duplicate_report.ArticleDuplicateReportBackgroundTask.prepare(user, outdir=TMP_DIR)
        task = article_duplicate_report.ArticleDuplicateReportBackgroundTask(job)
        task.run()

        # The audit log should show we saved the reports to the TMP_DIR defined above
        audit_1 = job.audit.pop(0)
        assert audit_1.get('message', '').endswith(TMP_DIR)
        assert os.path.exists(TMP_DIR + '/duplicate_articles_global_' + dates.today() + '.csv')

        # It should also clean up its interim article csv
        assert not os.path.exists(paths.rel2abs(__file__, 'tmp_article_duplicate_report'))

        # The duplicates should be detected and appear in the report and audit summary count
        with open(TMP_DIR + '/duplicate_articles_global_' + dates.today() + '.csv') as f:
            csvlines = f.readlines()
            # We expect one result line + headings: our newest article has 1 duplicate
            res = csvlines.pop()
            assert res.startswith(article2.id)            # The newest comes first, so article1 is article2's duplicate.
            assert article1.id in res
            assert 'doi+fulltext' in res

        audit_2 = job.audit.pop(0)
        assert audit_2.get('message', '') == '2 articles processed for duplicates. 1 global duplicate sets found.'

    def test_02_duplicates_global_criteria(self):
        """ Check we match only the actual duplicates, amongst other articles in the index. """

        dup_doi = '10.xxx/xxx/duplicate'
        dup_fulltext = 'http://fulltext.url/article/duplicate'

        # Create 6 duplicate articles with varying creation times and duplication criteria
        for i in range(1, 7):
            src_minus_identifiers = ArticleFixtureFactory.make_article_source(
                with_id=False,
                in_doaj=True,
                with_journal_info=True
            )

            del src_minus_identifiers['bibjson']['identifier']
            del src_minus_identifiers['bibjson']['link']
            article = models.Article(**src_minus_identifiers)

            # some overlapping duplication criteria
            if i % 2:
                article.bibjson().add_identifier('doi', dup_doi)
            else:
                article.bibjson().add_identifier('doi', '10.1234/' + str(i))
            if i % 3:
                article.bibjson().add_url(url=dup_fulltext, urltype='fulltext', content_type='html')
            else:
                article.bibjson().add_url('http://not_duplicate/fulltext/' + str(i), 'fulltext', 'html')
            article.save(blocking=True)

        # So we have the following fixtures:
        # +---------------------------------------------------------+
        # |                Generated Articles                       |
        # +---------------------------------------------------------+
        # |   | DOI match | Fulltext match | Expected Report Result |
        # +---+-----------+----------------+------------------------+
        # | 1 | X         | X              | doi+fulltext           |
        # +---+-----------+----------------+------------------------+
        # | 2 | 0         | X              | fulltext               |
        # +---+-----------+----------------+------------------------+
        # | 3 | X         | 0              | doi                    |
        # +---+-----------+----------------+------------------------+
        # | 4 | 0         | X              | fulltext               |
        # +---+-----------+----------------+------------------------+
        # | 5 | X         | X              | doi+fulltext           |
        # +---+-----------+----------------+------------------------+
        # | 6 | 0         | 0              | none                   |
        # +---+-----------+----------------+------------------------+

        # If a criteria is hit, it is duplicated with all other articles i.e. not just pairwise. Going newest to oldest,
        # we expect: 5 is duplicated to 4, 3, 2, 1
        #            4 is duplicated to 5, 2, 1
        #            3 is duplicated to 5, 1
        #            2 is duplicated to 5, 4, 1
        #        and 1 is duplicated to 5, 4, 3, 2
        #
        # So the task will report that there are 16 duplicates.
        #
        # However, once a pair has been detected it'll only be reported once. Therefore, we expect:
        # 5 is duplicated to 4, 3, 2, 1
        # 4 is duplicated to 5, 2, 1
        # 3 is duplicated to 5, 1
        #
        # So the report will have 9 match pairs, totalling 10 lines including the headings.

        # Run the reporting task
        user = app.config.get("SYSTEM_USERNAME")
        job = article_duplicate_report.ArticleDuplicateReportBackgroundTask.prepare(user, outdir=TMP_DIR)
        task = article_duplicate_report.ArticleDuplicateReportBackgroundTask(job)
        task.run()

        audit = job.audit
        assert next((msg for msg in audit if msg["message"] == '6 articles processed for duplicates. 3 global duplicate sets found.'), None) is not None

        table = []
        with open(TMP_DIR + '/duplicate_articles_global_' + dates.today() + '.csv') as f:
            reader = csv.reader(f)
            for row in reader:
                table.append(row)

        # We expect there to be 10 rows.
        assert len(table) == 10, "expected: 10, received: {}".format(len(table))
        headings = table.pop(0)

        # We expect there to be one ID with 4 duplicates, one with 3, and one with 2 (in that order)
        article_ids = [row[0] for row in table]
        [a, b, c] = list(OrderedDict.fromkeys(article_ids))                                       # Dedupe keeping order
        expected = {a: 4, b: 3, c: 2}
        assert article_ids.count(a) == expected[a], "received: {}, expected: {}".format(article_ids.count(a), expected[a])
        assert article_ids.count(b) == expected[b], "received: {}, expected: {}".format(article_ids.count(a), expected[a])
        assert article_ids.count(c) == expected[c], "received: {}, expected: {}".format(article_ids.count(a), expected[a])

        # These counts should equal the number counted in the report itself
        for r in table:
            assert int(r[headings.index('n_matches')]) == expected[r[0]], "received: {}, expected: {}".format(int(r[headings.index('n_matches')]), expected[r[0]])

        # Article a should have one doi+fulltext match, one doi match, and 2 fulltext matches.
        a_duplicates = [row for row in table if row[0] == a]
        a_match_types = [row[headings.index('match_type')] for row in a_duplicates]
        assert a_match_types.count('doi+fulltext') == 1, "received: {}, expected 1".format(a_match_types.count('doi+fulltext'))
        assert a_match_types.count('doi') == 1, "received: {}, expected 1".format(a_match_types.count('doi'))
        assert a_match_types.count('fulltext') == 2, "received: {}, expected 2".format(a_match_types.count('fulltext'))
