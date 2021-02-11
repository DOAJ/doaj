from selenium.webdriver.common.by import By
import re


class PublicSearchResults:
    ABSTRACT_LINKS = (By.PARTIAL_LINK_TEXT, "Abstract")
    TITLE = (By.CLASS_NAME, "title")
    ABSTRACT_TEXT = (By.CLASS_NAME, "doaj-public-search-abstracttext")
    RECORDS = (By.CLASS_NAME, "doaj-public-search-record-results")

    def __init__(self, browser):
        self.browser = browser

    def count_records_found(self):
        records = self.browser.find_elements(*self.RECORDS)
        return len(records)

    def unfold_abstracts(self):
        abstract_links = self.browser.find_elements(*self.ABSTRACT_LINKS)
        for abstract in abstract_links:
            self.browser.execute_script("arguments[0].click();", abstract)

    def confirm_phrase_in_results(self, phrase):
        records = self.browser.find_elements(*self.RECORDS)
        for r in records:
            title = r.find_element(*self.TITLE).text
            abstract = r.find_element(*self.ABSTRACT_TEXT).text
            if not re.search(phrase, title, re.IGNORECASE) and not re.search(phrase, abstract, re.IGNORECASE):
                return False
        return True