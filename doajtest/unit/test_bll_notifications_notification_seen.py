import time

from doajtest.helpers import DoajTestCase
from portality import models
from portality.bll import DOAJ
from portality.bll.exceptions import NoSuchObjectException

class TestBLLNotificationSeen(DoajTestCase):

    def setUp(self):
        super(TestBLLNotificationSeen, self).setUp()

    def tearDown(self):
        super(TestBLLNotificationSeen, self).tearDown()

    def test_01_notification_missing(self):
        acc = models.Account()
        acc.set_id("testuser")

        n = models.Notification()
        n.who = "testuser"
        n.long = "my message"
        n.short = "short note"
        n.action = "/test"
        n.classification = "test_class"
        n.created_by = "test:notify"
        n.save(blocking=True)

        svc = DOAJ.notificationsService()
        with self.assertRaises(NoSuchObjectException):
            ns = svc.notification_seen(acc, "randomid")

    def test_02_notification_successfully_seen(self):
        acc = models.Account()
        acc.set_id("testuser")

        n = models.Notification()
        n.who = "testuser"
        n.long = "my message"
        n.short = "short note"
        n.action = "/test"
        n.classification = "test_class"
        n.created_by = "test:notify"
        n.save(blocking=True)

        svc = DOAJ.notificationsService()
        ns = svc.notification_seen(acc, n.id)
        assert ns

        time.sleep(2)
        n2 = models.Notification.pull(n.id)
        assert n2.is_seen()

    def test_02_not_owner(self):
        acc = models.Account()
        acc.set_id("testuser")

        n = models.Notification()
        n.who = "testuser2"
        n.long = "my message"
        n.short = "short note"
        n.action = "/test"
        n.classification = "test_class"
        n.created_by = "test:notify"
        n.save(blocking=True)

        svc = DOAJ.notificationsService()
        ns = svc.notification_seen(acc, n.id)
        assert not ns

        time.sleep(2)
        n2 = models.Notification.pull(n.id)
        assert not n2.is_seen()