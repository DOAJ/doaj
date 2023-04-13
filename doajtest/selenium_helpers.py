import time
from multiprocessing import Process
from typing import TYPE_CHECKING

from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By

from doajtest.helpers import DoajTestCase
from portality import app, models

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver


class SeleniumTestCase(DoajTestCase):
    doaj_process = None
    SELENIUM_URL = 'http://localhost:4444/wd/hub'
    selenium = None  # selenium driver

    DOAJ_HOST = app.app.config.get('SELENIUM_DOAJ_HOST', 'localhost')
    DOAJ_PORT = app.app.config.get('SELENIUM_DOAJ_PORT', 5014)

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.fix_es_mapping()

    def setUp(self):
        super().setUp()

        # run doaj server in a background process
        def _run():
            app.run_server(host=self.DOAJ_HOST, port=self.DOAJ_PORT)

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
        self.selenium.implicitly_wait(10) # KTODO test if this is needed

    def tearDown(self):
        super().tearDown()

        self.doaj_process.terminate()
        print('doaj process terminated')

        self.selenium.quit()
        time.sleep(5)  # wait for selenium to quit

    @classmethod
    def get_doaj_url(cls) -> str:
        return f'http://{cls.DOAJ_HOST}:{cls.DOAJ_PORT}'


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
        breakpoint()
    assert "/login" not in driver.current_url
