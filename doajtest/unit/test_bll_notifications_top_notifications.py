from doajtest.helpers import DoajTestCase
from portality import models
from portality.bll import DOAJ

class TestBLLTopNotifications(DoajTestCase):

    def setUp(self):
        super(TestBLLTopNotifications, self).setUp()

    def tearDown(self):
        super(TestBLLTopNotifications, self).tearDown()

    def test_01_top_notifications(self):
        acc = models.Account()
        acc.set_id("testuser")
        acc.set_email("test@example.com")
        acc.save(blocking=True)

        n = models.Notification()
        n.who = "testuser"
        n.long = "my message"
        n.short = "short note"
        n.action = "/test"
        n.classification = "test_class"
        n.created_by = "test:notify"
        n.save(blocking=True)

        svc = DOAJ.notificationsService()
        ns = svc.top_notifications(acc)

        assert len(ns) == 1
        assert ns[0].id == n.id