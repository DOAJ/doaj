from doajtest.testdrive.factory import TestDrive


class DeletedArticles(TestDrive):
    def setup(self) -> dict:
        # create 2 publisher accounts.  The first will have tombstoned articles,
        # the second will not
        publisher1, pw1 = self.publisher_account()
        publisher2, pw2 = self.publisher_account()

        # create one journal for each publisher
        journals1 = self.journals_in_doaj(publisher1, n=1, block=True)
        journals2 = self.journals_in_doaj(publisher2, n=1, block=True)

        # place 10 articles in each journal
        articles1 = self.articles(journals1[0], n=10)
        articles2 = self.articles(journals2[0], n=10)

        # for the first publishers journal, tombstone 10 articles
        tombs1 = self.article_tombstones(journals1[0], n=10)

        report = {}
        self.report_accounts([(publisher1, pw1), (publisher2, pw2)], report)
        self.report_journal_ids(journals1 + journals2, report)
        self.report_article_ids(articles1 + articles2, report)
        self.report_article_tombstone_ids(tombs1, report)
        self.report_script("article_deletion_notifications", "Run background task", report)

        return report

    def teardown(self, params) -> dict:
        self.teardown_accounts(params)
        self.teardown_journals(params)
        self.teardown_articles(params)
        self.teardown_article_tombstones(params)
        return self.SUCCESS