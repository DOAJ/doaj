import pytest
from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys

from doajtest.UI.pages.main_page import DoajMainPage
from doajtest.UI.pages.public_search_results import PublicSearchResults

@pytest.fixture
def browser():
    driver = Chrome()
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

def test_basic_search(browser):
    # Set up some test case data
    PHRASE = 'cats'

    search_page = DoajMainPage(browser)
    search_page.load()
    search_page.search(PHRASE)

    search_results = PublicSearchResults(browser)
    search_results.unfold_abstracts()

    assert search_results.count_records_found() > 0
    assert search_results.confirm_phrase_in_results(PHRASE)

    # result_page = DuckDuckGoResultPage(browser)
    # assert result_page.link_div_count() > 0
    # assert result_page.phrase_result_count(PHRASE) > 0
    # assert result_page.search_input_value() == PHRASE