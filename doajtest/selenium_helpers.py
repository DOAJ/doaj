import datetime
import logging
import time
from multiprocessing import Process
from typing import TYPE_CHECKING

import selenium
from selenium import webdriver
from selenium.common import StaleElementReferenceException, ElementClickInterceptedException
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By

from doajtest.fixtures.url_path import URL_LOGOUT
from doajtest.helpers import DoajTestCase, patch_config
from portality import app, models, core
from portality.dao import ESMappingMissingError

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

log = logging.getLogger(__name__)


def find_ele_by_css(driver, css_selector: str) -> 'WebElement':
    return driver.find_element(By.CSS_SELECTOR, css_selector)


def find_eles_by_css(driver, css_selector: str) -> 'WebElement':
    return driver.find_elements(By.CSS_SELECTOR, css_selector)


def fix_index_not_found_exception(app):
    """
    fix index_not_found_exception
    some mappings have not created in initialise_index
    and will be created in this function to avoid index_not_found_exception
    :return:
    """
    missing_mappings = {}
    for name in [
        'draft_application',
        'application',
    ]:
        missing_mappings[name] = {
            'mappings': app.config['DEFAULT_DYNAMIC_MAPPING'],
            'settings': app.config['DEFAULT_INDEX_SETTINGS'],
        }

    core.put_mappings(core.es_connection, missing_mappings)


class SeleniumTestCase(DoajTestCase):
    doaj_process = None
    SELENIUM_URL = 'http://localhost:4444/wd/hub'
    selenium = None  # selenium driver

    DOAJ_HOST = app.app.config.get('SELENIUM_DOAJ_HOST', 'localhost')
    DOAJ_PORT = app.app.config.get('SELENIUM_DOAJ_PORT', 5014)

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.originals = patch_config(cls.app_test, {
            "DEBUG": False,
        })

    def find_ele_by_css(self, css_selector: str) -> 'WebElement':
        return find_ele_by_css(self.selenium, css_selector)

    def find_eles_by_css(self, css_selector: str) -> 'WebElement':
        return find_eles_by_css(self.selenium, css_selector)

    def setUp(self):
        super().setUp()

        # run doaj server in a background process
        def _run():
            try:
                app.run_server(host=self.DOAJ_HOST, port=self.DOAJ_PORT)
            except Exception as e:
                if isinstance(e, ESMappingMissingError):
                    log.error(f'es index could be removed by TestCase: {str(e)}')
                    return

                raise e

        self.doaj_process = Process(target=_run, daemon=True)
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

        # wait for server to start
        wait_unit(self._is_doaj_server_running, 10, 1.5, timeout_msg='doaj server not started')

        fix_index_not_found_exception(self.app_test)
        self.fix_es_mapping()

    def _is_doaj_server_running(self):
        log.info('checking if doaj server is running')

        for _ in range(5):
            try:
                goto(self.selenium, "/")
                break
            except selenium.common.exceptions.UnexpectedAlertPresentException as e:
                print('alert present, retrying...')
                continue
            except selenium.common.exceptions.WebDriverException as e:
                if 'ERR_CONNECTION_REFUSED' in str(e):
                    log.info('doaj server is not running')
                    return False
                raise e

        try:
            self.selenium.find_element(By.CSS_SELECTOR, 'div.container')
            log.info('doaj server is running')
            return True
        except selenium.common.exceptions.NoSuchElementException:
            log.info('doaj server is not running')
            return False

    def _is_selenium_quit(self):
        try:
            self.selenium.title
            return False
        except:
            return True

    def tearDown(self):

        print(f'{datetime.datetime.now().isoformat()} --- doaj process terminating...')
        self.doaj_process.terminate()
        self.doaj_process.join()
        wait_unit(lambda: not self._is_doaj_server_running(), 10, 1,
                  timeout_msg='doaj server is still running')

        self.selenium.quit()

        wait_unit(self._is_selenium_quit, 10, 1, timeout_msg='selenium is still running')
        print('selenium terminated')

        super().tearDown()

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


def wait_unit(exit_cond_fn, timeout=10, check_interval=0.1,
              timeout_msg="wait_unit but exit_cond timeout"):
    start = time.time()
    while (time.time() - start) < timeout:
        if exit_cond_fn():
            return
        time.sleep(check_interval)
    raise TimeoutError(timeout_msg)


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
