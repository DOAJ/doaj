import pytest
from selenium.webdriver import Chrome

from doajtest.UI.pages.login_page import DoajLoginPage
from doajtest.UI.pages.main_page import DoajMainPage
from doajtest.UI.pages.metadata_form import PublisherMetadataForm
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

def test_metadata_form(browser):
    TITLE = "New Article"
    AUTHOR = {"name": "Aga Domanska", "affiliation" : "CL University"}
    FULLTEXT_URL = "https://www.example.com"
    ACCOUNT = {"username" : "Aga", "password" : "password", "issns" : ["1234-5678", "9876-5432"]}

    login_page = DoajLoginPage(browser)
    login_page.load()
    login_page.login(ACCOUNT["username"], ACCOUNT["password"])
    #should we confirm successful login here?

    form_page = PublisherMetadataForm(browser)
    form_page.load()
    form_page.add_article()
    assert form_page.focus_on_element("title")

    form_page.add_title(TITLE)
    form_page.add_article()
    errors = form_page.errors()
    assert "no_doi" in errors
    assert "not_enough_authors" in errors
    assert "invalid_url" in errors
    assert "no_pissn_or_eissn" in errors

    assert form_page.count_author_fields() == 3
    form_page.remove_author()
    assert form_page.count_author_fields() == 2

    form_page.add_author_field()
    assert form_page.count_author_fields() == 3

    form_page.add_author(AUTHOR)
    form_page.add_url(FULLTEXT_URL)
    assert form_page.confirm_issn_dropdown(ACCOUNT["issns"])
    form_page.choose_pissn(ACCOUNT["issns"][0])

    form_page.add_article()
    assert form_page.success()
