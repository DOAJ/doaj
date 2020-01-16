from behave import *
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Chrome

import pytest
from doajtest.UI.pages.main_page import DoajMainPage
from doajtest.UI.pages.public_search_results import PublicSearchResults

URL = 'localhost:5004'
PHRASE = 'cats'

@pytest.fixture
def browser():
    driver = Chrome()
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

@given('Main page is loaded')
def load(context):
    main_page = DoajMainPage(browser)
    main_page.load()

@when('we type search phrase into search box and click Enter')
def search(context):

    search_page = DoajMainPage(browser)
    search_page.load()
    search_page.search(PHRASE)

@then('we receive correct search results')
def check_results(context):
    search_results = PublicSearchResults(browser)
    search_results.unfold_abstracts()

    assert search_results.count_records_found() > 0
    assert search_results.confirm_phrase_in_results(PHRASE)