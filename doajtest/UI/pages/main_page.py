from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class DoajMainPage:
    URL = 'localhost:5004'
    SEARCH_INPUT = (By.ID, "homepage-search-input")

    def __init__(self, browser):
        self.browser = browser

    def load(self):
        self.browser.get(self.URL)

    def search(self, phrase):
        search_input = self.browser.find_element(*self.SEARCH_INPUT)
        search_input.send_keys(phrase + Keys.RETURN)