from doajtest.testdrive.factory import TestDrive


class ArticleMetadataUploadForm(TestDrive):
    def setup(self) -> dict:
        # The "Enter Article Metadata" form's Print/Online ISSN dropdowns are
        # populated from the logged-in publisher's own in-DOAJ journals (see
        # choices_for_article_issns() in portality/forms/article_forms.py) - so this
        # test needs a publisher who already owns one, per the tester's note.
        publisher_acc, publisher_pw = self.publisher_account()
        journal = self.journals_in_doaj(publisher_acc, n=1, block=True)[0]

        report = {}
        self.report_accounts([(publisher_acc, publisher_pw)], report)
        self.report_journal_ids([journal], report)
        report["notes"] = [
            "Log in as the publisher account below to test the 'Enter Article "
            "Metadata' form.",
            f"This account owns a journal in DOAJ with print ISSN "
            f"{journal.bibjson().pissn} and online ISSN {journal.bibjson().eissn} - "
            "these should be the values offered in the form's ISSN dropdowns.",
        ]
        return report

    def teardown(self, params) -> dict:
        self.teardown_accounts(params)
        self.teardown_journals(params)
        return self.SUCCESS
