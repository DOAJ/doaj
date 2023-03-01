from selenium.webdriver.common.by import By

from doajtest import selenium_helpers
from doajtest.fixtures import ApplicationFixtureFactory, JournalFixtureFactory, AccountFixtureFactory
from doajtest.fixtures.article_doajxml import ARTICLE_UPLOAD_SUCCESSFUL
from doajtest.selenium_helpers import SeleniumTestCase
from portality import models
from portality.tasks import ingestarticles


class ArticleXmlUploadSTC(SeleniumTestCase):
    def test_upload_new_article(self):
        publisher = models.Account(**AccountFixtureFactory.make_publisher_source())
        password = 'password'
        publisher.set_password(password)
        publisher.save(blocking=True)

        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(publisher.id)
        journal.save(blocking=True)


        selenium_helpers.login(self.selenium, publisher.id, password)
        assert "/login" not in self.selenium.current_url

        selenium_helpers.goto(self.selenium, "/publisher/uploadfile")

        def _find_history_rows():
            return self.selenium.find_elements(By.CSS_SELECTOR, "#previous_files tbody tr")

        n_org_rows = len(_find_history_rows())
        self.selenium.find_element(By.ID, 'upload-xml-file').send_keys(ARTICLE_UPLOAD_SUCCESSFUL)
        self.selenium.find_element(By.ID, 'upload_form').submit()
        new_rows = _find_history_rows()
        assert n_org_rows + 1 == len(new_rows)
        assert 'pending' in new_rows[0].text

        # trigger upload article background job by function call
        for f in models.FileUpload.iterall():
            print(f)

        # task = ingestarticles.IngestArticlesBackgroundTask(job)



