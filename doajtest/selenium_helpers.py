import datetime
import logging
import multiprocessing
from multiprocessing import Process, freeze_support
from typing import TYPE_CHECKING

import selenium
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException
from selenium.webdriver.common.by import By

from doajtest.fixtures.url_path import URL_LOGOUT
from doajtest.helpers import DoajTestCase, patch_config
from portality import app, models, core
from portality.dao import ESMappingMissingError
from portality.lib.thread_utils import wait_until

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

multiprocessing.set_start_method('fork')

log = logging.getLogger(__name__)
DOAJ_HOST = app.app.config.get('SELENIUM_DOAJ_HOST', 'localhost')
DOAJ_PORT = app.app.config.get('SELENIUM_DOAJ_PORT', 5014)


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


# run doaj server in a background process
def _run_doaj_server(app_batch):
    try:
        patch_config(app.app, app_batch)
        app.run_server(host=DOAJ_HOST, port=DOAJ_PORT)
    except Exception as e:
        if isinstance(e, ESMappingMissingError):
            log.error(f'es index could be removed by TestCase: {str(e)}')
            return

        raise e


class SeleniumTestCase(DoajTestCase):
    doaj_process = None
    selenium = None  # selenium driver

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.originals = patch_config(cls.app_test, {
            "DEBUG": False,
            'SSL': False,  # avoid /login redirect to https
        })

    def find_ele_by_css(self, css_selector: str) -> 'WebElement':
        return find_ele_by_css(self.selenium, css_selector)

    def find_eles_by_css(self, css_selector: str) -> 'WebElement':
        return find_eles_by_css(self.selenium, css_selector)

    def setUp(self):
        super().setUp()

        freeze_support()
        self.doaj_process = Process(target=_run_doaj_server, args=(self.create_app_patch(),), daemon=True)
        self.doaj_process.start()

        # prepare selenium driver
        selenium_remote_url = self.app_test.config.get('SELENIUM_REMOTE_URL')
        if selenium_remote_url:
            # run selenium with docker remote browser
            options = webdriver.ChromeOptions()
            options.add_argument("no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1400,1000")
            options.add_argument("--disable-dev-shm-usage")
            browser_driver = webdriver.Remote(
                command_executor=selenium_remote_url,
                options=options,
            )
        else:
            # run selenium with your local browser
            options = webdriver.ChromeOptions()
            options.add_argument('--start-maximized')  # maximize browser window
            if self.app_test.config.get('SELENIUM_HEADLESS', False):
                options.add_argument('--headless')
                options.add_argument("--window-size=1400,1000")
            browser_driver = webdriver.Chrome(options=options, )

        self.selenium = browser_driver
        self.selenium.maximize_window()  # avoid something is not clickable
        self.selenium.set_window_size(1400, 1000)  # avoid something is not clickable

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
        return f'http://{DOAJ_HOST}:{DOAJ_PORT}'

    def js_click(self, selector):
        script = f"document.querySelector('{selector}').click(); "
        self.selenium.execute_script(script)


def goto(driver: 'WebDriver', url_path: str):
    if not url_path.startswith('/'):
        url_path = '/' + url_path
    url = SeleniumTestCase.get_doaj_url() + url_path
    log.info(f'goto: {url}')
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
