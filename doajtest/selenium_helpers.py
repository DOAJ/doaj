import logging
import multiprocessing
import time
from multiprocessing import Process
from typing import TYPE_CHECKING

import selenium
from selenium import webdriver
from selenium.common import StaleElementReferenceException, ElementClickInterceptedException
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By

from doajtest.fixtures.url_path import URL_LOGOUT
from doajtest.helpers import DoajTestCase
from portality import app, models
from portality.dao import ESMappingMissingError

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

log = logging.getLogger(__name__)


def find_ele_by_css(driver, css_selector: str) -> 'WebElement':
    return driver.find_element(By.CSS_SELECTOR, css_selector)


def find_eles_by_css(driver, css_selector: str) -> 'WebElement':
    return driver.find_elements(By.CSS_SELECTOR, css_selector)


class SeleniumTestCase(DoajTestCase):
    doaj_process = None
    SELENIUM_URL = 'http://localhost:4444/wd/hub'
    selenium = None  # selenium driver

    DOAJ_HOST = app.app.config.get('SELENIUM_DOAJ_HOST', 'localhost')
    DOAJ_PORT = app.app.config.get('SELENIUM_DOAJ_PORT', 5014)

    def find_ele_by_css(self, css_selector: str) -> 'WebElement':
        return find_ele_by_css(self.selenium, css_selector)

    def find_eles_by_css(self, css_selector: str) -> 'WebElement':
        return find_eles_by_css(self.selenium, css_selector)

    def setUp(self):
        super().setUp()
        process_manager = multiprocessing.Manager()

        # run doaj server in a background process
        def _run():
            try:
                app.run_server(host=self.DOAJ_HOST, port=self.DOAJ_PORT)
            except Exception as e:
                if isinstance(e, ESMappingMissingError):
                    log.error(str(e))
                    return

                raise e

        self.doaj_process = Process(target=_run)
        self.doaj_process.start()

        # prepare selenium driver
        path_chrome_driver = self.app_test.config.get('SELENIUM_CHROME_DRIVER_PATH')
        if path_chrome_driver:
            # run selenium with your local browser
            options = webdriver.ChromeOptions()
            options.add_argument('--start-maximized')  # maximize browser window
            browser_driver = webdriver.Chrome(path_chrome_driver, options=options)
        else:
            # run selenium with docker remote browser
            options = webdriver.ChromeOptions()
            options.add_argument("no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=800,600")
            options.add_argument("--disable-dev-shm-usage")
            browser_driver = webdriver.Remote(
                command_executor=self.SELENIUM_URL,
                desired_capabilities=DesiredCapabilities.CHROME,
                options=options,
            )

        self.selenium = browser_driver
        self.selenium.maximize_window()  # avoid something is not clickable

        self.fix_es_mapping()

        # wait for server to start
        def _is_doaj_server_running():
            goto(self.selenium, "/")
            try:
                self.selenium.find_element(By.CSS_SELECTOR, 'div.container')
                return True
            except selenium.common.exceptions.NoSuchElementException:
                return False

        try:
            wait_unit(_is_doaj_server_running, 10, 1.5)
        except TimeoutError:
            raise TimeoutError('doaj server not started')

    def tearDown(self):
        super().tearDown()

        self.doaj_process.terminate()
        print('doaj process terminated')

        self.selenium.quit()
        time.sleep(5)  # wait for selenium to quit

    @classmethod
    def get_doaj_url(cls) -> str:
        return f'http://{cls.DOAJ_HOST}:{cls.DOAJ_PORT}'

    def js_click(self, selector):
        script = f"document.querySelector('{selector}').click(); "
        self.selenium.execute_script(script)


def goto(driver: 'WebDriver', url_path: str):
    if not url_path.startswith('/'):
        url_path = '/' + url_path
    url = SeleniumTestCase.get_doaj_url() + url_path
    driver.get(url)


def cancel_alert(driver: 'WebDriver'):
    try:
        alert = driver.switch_to.alert
        alert.accept()
    except:
        pass


def login(driver: 'WebDriver', username: str, password: str):
    goto(driver, "/login")
    driver.find_element(By.ID, 'user').send_keys(username)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()


def logout(driver: 'WebDriver'):
    goto(driver, URL_LOGOUT)


def login_by_acc(driver: 'WebDriver', acc: models.Account = None):
    password = 'password'
    acc.set_password(password)
    acc.save(blocking=True)
    from selenium.common import NoSuchElementException
    try:
        login(driver, acc.id, password)
    except NoSuchElementException:
        import traceback
        traceback.print_exc()
        breakpoint()  # for checking, how could this happen?
    assert "/login" not in driver.current_url


def wait_unit(exit_cond_fn, timeout=10, check_interval=0.1):
    start = time.time()
    while (time.time() - start) < timeout:
        if exit_cond_fn():
            return
        time.sleep(check_interval)
    raise TimeoutError(f"wait_unit timeout after {timeout} seconds")


def wait_unit_elements(driver: 'WebDriver', css_selector: str, timeout=10, check_interval=0.1):
    elements = []

    def exit_cond_fn():
        nonlocal elements
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, css_selector)
            return elements
        except:
            return False

    wait_unit(exit_cond_fn, timeout, check_interval)
    return elements


def wait_unit_click(driver: 'WebDriver', css_selector: str, timeout=10, check_interval=0.1):
    def _click():
        try:
            ele = find_ele_by_css(driver, css_selector)
            if ele:
                ele.click()
                return True
            return False
        except (StaleElementReferenceException, ElementClickInterceptedException):
            return False

    wait_unit(_click, timeout=10, check_interval=0.1)


def click_edges_item(driver: 'WebDriver', ele_name, item_name):
    wait_unit_click(driver, f'#edges-bs3-refiningand-term-selector-toggle-{ele_name}')
    for ele in find_eles_by_css(driver, f'.edges-bs3-refiningand-term-selector-result-{ele_name} a'):
        if item_name in ele.text.strip():
            ele.click()
