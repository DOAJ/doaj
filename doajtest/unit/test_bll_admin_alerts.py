import time

from doajtest.helpers import DoajTestCase
from portality.lib.thread_utils import wait_until
from portality import models
from portality.bll import DOAJ
from portality.bll.exceptions import NoSuchObjectException

class TestBLLAdminAlerts(DoajTestCase):

    def setUp(self):
        super(TestBLLAdminAlerts, self).setUp()

    def tearDown(self):
        super(TestBLLAdminAlerts, self).tearDown()

    def test_01_make_alert(self):
        svc = DOAJ.adminAlertsService()
        alert = svc.alert("test_source", "This is a test alert message")
        assert alert.source == "test_source"
        assert alert.message == "This is a test alert message"
        assert alert.state == models.AdminAlert.STATE_NEW

        wait_until(lambda: models.AdminAlert.count() > 0)
        a2 = models.AdminAlert.pull(alert.id)
        assert a2.source == "test_source"
        assert a2.message == "This is a test alert message"
        assert a2.state == models.AdminAlert.STATE_NEW

    def test_02_set_in_progress(self):
        svc = DOAJ.adminAlertsService()
        alert = svc.alert("test_source", "This is a test alert message")
        assert alert.source == "test_source"
        assert alert.message == "This is a test alert message"
        assert alert.state == models.AdminAlert.STATE_NEW

        wait_until(lambda: models.AdminAlert.count() > 0)
        svc.set_in_progress(alert.id)
        a2 = models.AdminAlert.pull(alert.id)
        assert a2.state == models.AdminAlert.STATE_IN_PROGRESS

    def test_03_set_closed(self):
        svc = DOAJ.adminAlertsService()
        alert = svc.alert("test_source", "This is a test alert message")
        assert alert.source == "test_source"
        assert alert.message == "This is a test alert message"
        assert alert.state == models.AdminAlert.STATE_NEW

        wait_until(lambda: models.AdminAlert.count() > 0)
        svc.set_closed(alert.id)
        a2 = models.AdminAlert.pull(alert.id)
        assert a2.state == models.AdminAlert.STATE_CLOSED