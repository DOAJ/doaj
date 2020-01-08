from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class DoajMainPage:
    URL = 'localhost:5004'

    def __init__(self, browser):
        self.browser = browser

    def load(self):
        self.browser.get(self.URL)

    def search(self, phrase):
        search_input = self.browser.find_element_by_id("homepage-search-input")
        search_input.send_keys(phrase + Keys.RETURN)