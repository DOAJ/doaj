from pathlib import Path
from time import sleep
from typing import Type, Union

from selenium.webdriver.common.by import By

from doajtest import selenium_helpers
from doajtest.fixtures import JournalFixtureFactory, AccountFixtureFactory
from doajtest.fixtures.article_doajxml import ARTICLE_UPLOAD_SUCCESSFUL
from doajtest.selenium_helpers import SeleniumTestCase
from portality import models, dao


def get_latest(domain_obj: Union[Type[dao.DomainObject], dao.DomainObject]):
    obj = domain_obj.iterate({
        "sort": [{"created_date": {"order": "desc"}}],
        "size": 1,
    })
    return next(obj, None)


class ArticleXmlUploadSTC(SeleniumTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.fix_es_mapping()

    def test_upload_new_article__success(self):
        publisher = models.Account(**AccountFixtureFactory.make_publisher_source())

        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(publisher.id)
        bib = journal.bibjson()
        bib.pissn = '1111-1111'
        bib.eissn = '2222-2222'
        journal.bibjson().is_replaced_by = []
        journal.bibjson().replaces = []
        journal.save(blocking=True)

        selenium_helpers.login_by_acc(self.selenium, publisher)

        # goto upload page and upload article xml file
        selenium_helpers.goto(self.selenium, "/publisher/uploadfile")

        def _find_history_rows():
            return self.selenium.find_elements(By.CSS_SELECTOR, "#previous_files tbody tr")

        n_file_upload = models.FileUpload.count()
        n_org_rows = len(_find_history_rows())
        self.selenium.find_element(By.ID, 'upload-xml-file').send_keys(ARTICLE_UPLOAD_SUCCESSFUL)
        self.selenium.find_element(By.ID, 'upload_form').submit()

        new_rows = _find_history_rows()
        assert n_org_rows + 1 == len(new_rows)
        assert 'pending' in new_rows[0].text
        assert n_file_upload + 1 == models.FileUpload.count()

        sleep(14)  # wait for background job to finish

        new_file_upload: models.FileUpload = get_latest(models.FileUpload)

        # trigger upload article background job by function call
        print(new_file_upload)
        assert new_file_upload.filename == Path(ARTICLE_UPLOAD_SUCCESSFUL).name
        assert new_file_upload.status == 'processed'

        # back to /publisher/uploadfile check status updated
        selenium_helpers.goto(self.selenium, "/publisher/uploadfile")
        new_rows = _find_history_rows()
        assert 'successfully processed 1 articles imported' in new_rows[0].text

        selenium_helpers.goto(self.selenium, f'/toc/{bib.eissn}')
        assert 'The Title' in self.selenium.find_element(
            By.CSS_SELECTOR, 'main.page-content header h1').text
