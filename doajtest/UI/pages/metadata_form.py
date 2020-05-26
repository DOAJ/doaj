from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class PublisherMetadataForm:
    URL = 'localhost:5004/publisher/metadata'
    SEARCH_ADD_ARTICLE_BUTTON = (By.XPATH, "//button[@type='submit' and contains(., 'Add Article')]")
    SEARCH_ERRORS = (By.XPATH, "//ul[@class='errors']//li")
    SEARCH_AUTHOR_FIELDS = (By.XPATH, "//input[contains(@id,'authors-')]")
    SEARCH_REMOVE_BUTTON = (By.XPATH, "//button[contains(@id, 'remove_authors-')]")
    SEARCH_ADD_AUTHOR_BUTTON = (By.XPATH, "//input[@type='submit' and @name='more_authors']")
    SEARCH_ISSN_SELECT = (By.ID, "select2-chosen-2")
    SEARCH_SUCCESS_BANNER = (By.CLASS_NAME, "alert-success")

    def __init__(self, browser):
        self.browser = browser

    def load(self):
        self.browser.get(self.URL)

    def add_article(self):
        add_article_btn = self.browser.find_element(*self.SEARCH_ADD_ARTICLE_BUTTON)
        add_article_btn.click()

    def focus_on_element(self, elem_id):
        return self.browser.find_element_by_id(elem_id) == self.browser.switch_to.active_element

    def add_title(self, title):
        title_input = self.browser.find_element_by_id("title")
        title_input.send_keys(title)

    def errors(self):
        errors = self.browser.find_elements(*self.SEARCH_ERRORS)
        result = []
        for e in errors:
            if e.text == 'Invalid DOI. A DOI can optionally start with a prefix (such as "doi:"), followed by "10." and the remainder of the identifier':
                result.append('no_doi')
            elif e.text == 'Please provide at least one author':
                result.append('not_enough_authors')
            elif e.text == 'Invalid URL.':
                result.append('invalid_url')
            elif e.text == 'Either this field or Journal ISSN (online version) is required':
                result.append('no_pissn_or_eissn')
        return result

    def remove_author(self):
        remove_button = self.browser.find_element(*self.SEARCH_REMOVE_BUTTON)
        remove_button.click()

    def count_author_fields(self):
        authors_fields = self.browser.find_elements(*self.SEARCH_AUTHOR_FIELDS)
        return len(authors_fields) // 2

    def add_author_field(self):
        add_author_btn = self.browser.find_element(*self.SEARCH_ADD_AUTHOR_BUTTON)
        add_author_btn.click()

    def add_author(self, author):
        author_name_input = self.browser.find_element_by_id("authors-0-name")
        author_name_input.send_keys(author["name"])
        author_aff_input = self.browser.find_element_by_id("authors-0-affiliation")
        author_aff_input.send_keys(author["affiliation"])

    def add_url(self, fulltext):
        fulltext_input = self.browser.find_element_by_id("fulltext")
        fulltext_input.send_keys(fulltext)

    def _open_issn_dropdown(self):
        issn_dropdown = self.browser.find_element(*self.SEARCH_ISSN_SELECT)
        webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()
        issn_dropdown.click()
        return issn_dropdown

    def confirm_issn_dropdown(self, issns):
        issn_dropdown = self._open_issn_dropdown()
        options_elements = issn_dropdown.find_elements_by_xpath("//ul[contains(@id,'select2-results')]//li")
        options = [x.text for x in options_elements]
        issns.append("Select an ISSN")
        return len(options) == len(issns) and sorted(options) == sorted(issns)

    def choose_pissn(self, pissn):
        issn_dropdown = self._open_issn_dropdown()
        input = issn_dropdown.find_element_by_xpath("//input")
        input.send_keys(pissn + Keys.RETURN)

    def success(self):
        banner = self.browser.find_element(*self.SEARCH_SUCCESS_BANNER)
        return banner
