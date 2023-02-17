from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from doajtest.fixtures import JournalFixtureFactory, ApplicationFixtureFactory
from portality.events.consumers.journal_discontinuing_soon_notify import JournalDiscontinuingSoonNotify
from doajtest.fixtures import BackgroundFixtureFactory
import time

# Mock required to make application lookup work
@classmethod
def pull_application(cls, id):
    app = models.Application(**ApplicationFixtureFactory.make_application_source())
    return app

@classmethod
def pull_by_key(cls, key, value):
    ed = models.EditorGroup()
    acc = models.Account()
    acc.set_id('testuser')
    acc.set_email("test@example.com")
    acc.save(blocking=True)
    ed.set_maned(acc.id)
    ed.save(blocking=True)

    return ed

class TestJournalDiscontinuingSoonNotify(DoajTestCase):
    def setUp(self):
        super(TestJournalDiscontinuingSoonNotify, self).setUp()
        self.pull_application = models.Application.pull
        models.Application.pull = pull_application
        self.pull_by_key = models.EditorGroup.pull_by_key
        models.EditorGroup.pull_by_key = pull_by_key

    def tearDown(self):
        super(TestJournalDiscontinuingSoonNotify, self).tearDown()
        models.Application.pull = self.pull_application
        models.EditorGroup.pull_by_key = self.pull_by_key

    def test_consumes(self):

        event = models.Event("test:event", context={"data" : {"1234"}})
        assert not JournalDiscontinuingSoonNotify.consumes(event)

        event = models.Event("test:event", context={"data": {}})
        assert not JournalDiscontinuingSoonNotify.consumes(event)

        event = models.Event(constants.EVENT_JOURNAL_DISCONTINUING_SOON)
        assert not JournalDiscontinuingSoonNotify.consumes(event)

        event = models.Event(constants.EVENT_JOURNAL_DISCONTINUING_SOON, context = {"journal": {"1234"}, "discontinue_date": "2002-22-02"})
        assert JournalDiscontinuingSoonNotify.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")

        source = BackgroundFixtureFactory.example()
        bj = models.BackgroundJob(**source)
        # bj.save(blocking=True)

        acc = models.Account()
        acc.set_id('testuser')
        acc.set_email("test@example.com")
        acc.add_role('admin')
        acc.save(blocking=True)

        source = JournalFixtureFactory.make_journal_source()
        journal = models.Journal(**source)
        journal.save(blocking=True)

        event = models.Event(constants.BACKGROUND_JOB_FINISHED, context={"job" : bj.data, "journal" : journal.id})
        JournalDiscontinuingSoonNotify.consume(event)

        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == acc.id
        assert n.created_by == JournalDiscontinuingSoonNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS
        assert n.long is not None
        assert n.short is not None
        assert n.action is not None
        assert not n.is_seen()
