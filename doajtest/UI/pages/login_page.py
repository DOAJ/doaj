from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

class DoajLoginPage:
    URL = 'localhost:5004/account/login'

    def __init__(self, browser):
        self.browser = browser

    def load(self):
        self.browser.get(self.URL)

    def login(self, username, password):
        username_input = self.browser.find_element_by_id("username")
        username_input.send_keys(username)
        password_input = self.browser.find_element_by_id("password")
        password_input.send_keys(password)
        login_btn = self.browser.find_element_by_id("login-button")
        login_btn.click()