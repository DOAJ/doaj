from multiprocessing import Process

from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By

from doajtest.helpers import DoajTestCase
from portality import app
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver


class SeleniumTestCase(DoajTestCase):
    DOAJ_HOST = '172.17.0.1'
    DOAJ_PORT = 5014
    doaj_process = None
    SELENIUM_URL = 'http://localhost:4444/wd/hub'
    selenium = None  # selenium driver

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        # run doaj server in a background process
        def _run():
            app.run_server(host=cls.DOAJ_HOST, port=cls.DOAJ_PORT)

        cls.doaj_process = Process(target=_run)
        cls.doaj_process.start()

        # prepare selenium driver
        options = webdriver.ChromeOptions()
        options.add_argument("no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=800,600")
        options.add_argument("--disable-dev-shm-usage")
        cls.selenium = webdriver.Remote(
            command_executor=cls.SELENIUM_URL,
            desired_capabilities=DesiredCapabilities.CHROME,
            options=options,
        )
        cls.selenium.maximize_window()  # avoid something is not clickable
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

        cls.doaj_process.terminate()
        print('doaj process terminated')

        cls.selenium.quit()

    @classmethod
    def get_doaj_url(cls) -> str:
        return f'http://{cls.DOAJ_HOST}:{cls.DOAJ_PORT}'


def goto(driver: 'WebDriver', url_path: str):
    if not url_path.startswith('/'):
        url_path = '/' + url_path
    url = SeleniumTestCase.get_doaj_url() + url_path
    driver.get(url)


def login(driver: 'WebDriver', username: str, password: str):
    goto(driver, "/login")
    driver.find_element(By.ID, 'user').send_keys(username)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
