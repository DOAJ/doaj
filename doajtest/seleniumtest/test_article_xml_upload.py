import time
from pathlib import Path
from time import sleep
from typing import Type, Union

from parameterized import parameterized
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

from doajtest import selenium_helpers
from doajtest.fixtures import JournalFixtureFactory, AccountFixtureFactory, url_path, article_doajxml
from doajtest.fixtures.accounts import PUBLISHER_B_SOURCE
from doajtest.fixtures.article_doajxml import ARTICLE_UPLOAD_SUCCESSFUL
from doajtest.fixtures.url_path import URL_PUBLISHER_UPLOADFILE
from doajtest.selenium_helpers import SeleniumTestCase
from portality import models, dao
from portality.constants import FileUploadStatus

HISTORY_ROW_PROCESSING_FAILED = 'processing failed'
XML_FORMAT_DOAJ = 'doaj'


def get_latest(domain_obj: Union[Type[dao.DomainObject], dao.DomainObject]):
    obj = domain_obj.iterate({
        "sort": [{"created_date": {"order": "desc"}}],
        "size": 1,
    })
    return next(obj, None)


class ArticleXmlUploadDoajXmlSTC(SeleniumTestCase):
    """ testbook: article_xml_upload/doaj_xml """

    def goto_upload_page(self, acc: models.Account = None):
        publisher = acc or create_publisher_a()
        selenium_helpers.login_by_acc(self.selenium, publisher)
        selenium_helpers.goto(self.selenium, URL_PUBLISHER_UPLOADFILE)
        return publisher

    def upload_submit_file(self, file_path):
        self.selenium.find_element(By.ID, 'upload-xml-file').send_keys(file_path)
        self.selenium.find_element(By.ID, 'upload_form').submit()

    def test_without_file(self):
        """ similar to "Try uploading without providing a file" from testbook """
        self.goto_upload_page()
        self.selenium.find_element(By.ID, 'upload_form').submit()

        assert 'You must specify the file or upload from a link' in self.selenium.find_element(
            By.CSS_SELECTOR, '.form__question .error').text

    @parameterized.expand([
        # case "Upload a file which is not XML"
        (article_doajxml.NON_XML_FILE, 'Unable to parse XML file'),
        # case "Upload an XML file which does not meet the DOAJ schema"
        (article_doajxml.SCHEMA_INVALID, 'Unable to validate document with identified schema'),
        # case "Upload a malformed XML file"
        (article_doajxml.XML_MALFORMED, 'Unable to parse XML file'),
    ])
    def test_upload_fail(self, file_path, err_msg):
        """ cases about upload article failed with error message """
        self.goto_upload_page()
        self.upload_submit_file(file_path)

        alert_ele = self.selenium.find_element(By.CSS_SELECTOR, '.alert--message')
        assert alert_ele
        assert err_msg in alert_ele.text

        for _ in range(3):
            time.sleep(0.5)  # wait for es update history of uploads
            self.selenium.refresh()
            rows = find_history_rows(self.selenium)
            if rows:
                break

        assert rows
        self.assert_history_row(rows[0], status_msg='processing failed', file_path=file_path)

    def assert_history_row(self, history_row, status_msg=None, file_path=None, note=None):
        history_row_text = history_row.text
        if file_path:
            assert Path(file_path).name in history_row_text

        if status_msg:
            assert status_msg in history_row_text

        if note:
            assert note in history_row_text

    def test_duplicates_inside_the_file(self):
        """ similar to "Upload a file with duplicates inside the file" from testbook """
        publisher = create_publisher_a()
        create_journal_a(publisher)

        self.goto_upload_page(publisher)

        self.select_xml_format_by_value('doaj')

        file_path = article_doajxml.DUPLICATE_IN_FILE
        history_row = self.upload_pending_wait_bgjob(file_path, FileUploadStatus.Failed, XML_FORMAT_DOAJ)

        self.assert_history_row(history_row, status_msg=HISTORY_ROW_PROCESSING_FAILED, file_path=file_path,
                                note='One or more articles in this batch have duplicate identifiers')

    def select_xml_format_by_value(self, value):
        Select(self.selenium.find_element(By.ID, 'upload-xml-format')).select_by_value(value)

    def upload_pending_wait_bgjob(self, file_path, expected_bgjob_status, xml_format=None):
        # assume browser at publisher upload page

        if xml_format:
            self.select_xml_format_by_value(xml_format)

        n_file_upload = models.FileUpload.count()
        n_org_rows = len(find_history_rows(self.selenium))
        self.upload_submit_file(file_path)

        assert 'File uploaded and waiting to be processed' in self.find_ele_by_css('.alert--success').text
        new_rows = find_history_rows(self.selenium)
        assert n_org_rows + 1 == len(new_rows)
        assert 'pending' in new_rows[0].text
        assert n_file_upload + 1 == models.FileUpload.count()

        # wait for background job to finish
        selenium_helpers.wait_unit(
            lambda: get_latest(models.FileUpload).status not in (
                FileUploadStatus.Validated, FileUploadStatus.Incoming),
            timeout=15,
        )

        new_file_upload: models.FileUpload = get_latest(models.FileUpload)

        # trigger upload article background job by function call
        assert new_file_upload.filename == Path(file_path).name
        assert new_file_upload.status == expected_bgjob_status

        # back to /publisher/uploadfile check status updated
        selenium_helpers.goto(self.selenium, URL_PUBLISHER_UPLOADFILE)
        new_rows = find_history_rows(self.selenium)
        return new_rows[0]

    def assert_one_or_more_articles_failed(self, publisher, file_path, expected_failed_issn,
                                           expected_detail):
        self.goto_upload_page(publisher)

        history_row = self.upload_pending_wait_bgjob(file_path, FileUploadStatus.Failed,
                                                     XML_FORMAT_DOAJ)

        self.assert_history_row(history_row,
                                status_msg=HISTORY_ROW_PROCESSING_FAILED,
                                note='One or more articles failed to ingest')
        self.js_click('.show_error_details')
        time.sleep(0.5)  # wait for js to show details

        detail = find_history_rows(self.selenium)[0].find_element(By.CSS_SELECTOR, 'div[id^="details_"]').text
        assert expected_detail in detail
        assert expected_failed_issn in detail

    def test_containing_issn_the_publisher_does_not_own(self):
        """ similar to "Upload a file containing ISSNs the publisher does not own" from testbook """

        pub_b = models.Account(**PUBLISHER_B_SOURCE)
        pub_b.save()

        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(pub_b.id)
        bib = journal.bibjson()
        bib.pissn = '0000-0000'
        bib.eissn = '0000-000X'
        journal.save(blocking=True)

        publisher = create_publisher_a()
        self.assert_one_or_more_articles_failed(publisher, article_doajxml.UNOWNED_ISSN,
                                                expected_failed_issn='0000-0000',
                                                expected_detail='If you believe you should own these ISSNs, please contact us with the details',
                                                )

    def test_has_been_withdrawn(self):
        """ similar to "Upload a file containing ISSN that has been withdrawn" from testbook """

        publisher = create_publisher_a()
        publisher.save()

        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=False))
        journal.set_owner(publisher.id)
        journal.save(blocking=True)

        self.goto_upload_page(publisher)

        history_row = self.upload_pending_wait_bgjob(article_doajxml.WITHDRAWN_JOURNAL, FileUploadStatus.Failed,
                                                     XML_FORMAT_DOAJ)

        self.assert_history_row(history_row,
                                status_msg=HISTORY_ROW_PROCESSING_FAILED,
                                note='You are trying to add the articles to a journal that has been withdrawn from DOAJ')

    def test_issn_not_previously_seen_in_doaj(self):
        """ similar to "Upload a file containing ISSNs not previously seen in DOAJ" from testbook """

        publisher = create_publisher_a()
        publisher.save()

        journal = create_journal_a(publisher)
        journal.save(blocking=True)

        self.assert_one_or_more_articles_failed(publisher, article_doajxml.UNMATCHED_ISSN,
                                                expected_failed_issn='5555-5555',
                                                expected_detail='If you believe these ISSNs should be associated with a journal you own')

    def test_upload_file_erroneously_shared_ISSNs(self):
        """ similar to "Upload a file containing ISSNs erroneously shared with another account" from testbook """

        publisher = create_publisher_a()
        pub_b = models.Account(**PUBLISHER_B_SOURCE)
        pub_b.save()

        create_journal_by_issn(publisher=publisher, pissn='1111-1111', eissn='2222-2222')
        create_journal_by_issn(publisher=pub_b, pissn='2222-2222', eissn='3333-3333')

        self.assert_one_or_more_articles_failed(publisher, article_doajxml.SHARED_ISSN,
                                                expected_failed_issn='2222-2222',
                                                expected_detail='If you believe these ISSNs should be associated with a journal you own')

    def test_new_article_success(self):
        """ similar to "Successfully upload a file containing a new article" from testbook """

        publisher = create_publisher_a()

        journal = create_journal_a(publisher)

        # goto upload page and upload article xml file
        self.goto_upload_page(acc=publisher)

        latest_history_row = self.upload_pending_wait_bgjob(ARTICLE_UPLOAD_SUCCESSFUL, FileUploadStatus.Processed,
                                                            XML_FORMAT_DOAJ)

        self.assert_history_row(latest_history_row, note='successfully processed 1 articles imported')

        selenium_helpers.goto(self.selenium, url_path.url_toc(journal.bibjson().eissn))
        assert 'The Title' in self.selenium.find_element(
            By.CSS_SELECTOR, 'main.page-content header h1').text


def create_journal_a(publisher) -> models.Journal:
    journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
    journal.set_owner(publisher.id)
    bib = journal.bibjson()
    bib.pissn = '1111-1111'
    bib.eissn = '2222-2222'
    bib.is_replaced_by = []
    bib.replaces = []
    journal.save(blocking=True)
    return journal

def create_journal_by_issn(publisher=None, pissn=None, eissn=None, blocking=False) -> models.Journal:
    journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
    if publisher is not None:
        journal.set_owner(publisher.id)
    bib = journal.bibjson()
    if pissn is not None:
        bib.pissn = pissn
    if eissn is not None:
        bib.eissn = eissn
    bib.is_replaced_by = []
    bib.replaces = []
    journal.save(blocking=blocking)
    return journal


def create_publisher_a():
    publisher = models.Account(**AccountFixtureFactory.make_publisher_source())
    return publisher


def find_history_rows(driver):
    return driver.find_elements(By.CSS_SELECTOR, "#previous_files tbody tr")
