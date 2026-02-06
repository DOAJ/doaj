from doajtest.helpers import DoajTestCase
from portality.tasks.article_deletion_notifications import ArticleDeletionNotificationsBackgroundTask
from portality import models
from doajtest.fixtures.article import ArticleFixtureFactory
from doajtest.fixtures.accounts import AccountFixtureFactory
from portality.lib import dates
import time

class TestArticleDeletionNotifications(DoajTestCase):

    def test_article_deletion_notifications(self):
        # 1. Setup data
        # Create two publishers
        pub1 = models.Account(**AccountFixtureFactory.make_publisher_source())
        pub1.set_id("pub1")
        pub1.save(blocking=True)

        pub2 = models.Account(**AccountFixtureFactory.make_publisher_source())
        pub2.set_id("pub2")
        pub2.save(blocking=True)

        # Create some ArticleTombstones
        # Recent tombstone for pub1
        at1 = models.ArticleTombstone(**ArticleFixtureFactory.make_article_source())
        at1.set_id("at1")
        at1.set_created(dates.format(dates.before_now(1 * 24 * 60 * 60)))
        at1.data['admin'] = {'owner': 'pub1'}
        at1.save(blocking=True)

        # Another recent tombstone for pub1
        at2 = models.ArticleTombstone(**ArticleFixtureFactory.make_article_source())
        at2.set_id("at2")
        at2.set_created(dates.format(dates.before_now(2 * 24 * 60 * 60)))
        at2.data['admin'] = {'owner': 'pub1'}
        at2.save(blocking=True)

        # Recent tombstone for pub2
        at3 = models.ArticleTombstone(**ArticleFixtureFactory.make_article_source())
        at3.set_id("at3")
        at3.set_created(dates.format(dates.before_now(3 * 24 * 60 * 60)))
        at3.data['admin'] = {'owner': 'pub2'}
        at3.save(blocking=True)

        # Old tombstone (should be ignored)
        at4 = models.ArticleTombstone(**ArticleFixtureFactory.make_article_source())
        at4.set_id("at4")
        at4.set_created(dates.format(dates.before_now(10 * 24 * 60 * 60)))
        at4.data['admin'] = {'owner': 'pub1'}
        at4.save(blocking=True)

        # 2. Run the task
        job = ArticleDeletionNotificationsBackgroundTask.prepare("system")
        task = ArticleDeletionNotificationsBackgroundTask(job)
        task.run()

        time.sleep(2)

        # 3. Verify notifications
        # Pub1 should have 1 notification with 2 articles
        notes1 = models.Notification.all()
        self.assertEqual(len(notes1), 2)
        
        note1 = None
        for n in notes1:
            if n.who == "pub1":
                note1 = n
                break
        
        self.assertIsNotNone(note1)
        self.assertIn("Deleted articles in your journal(s) this week", note1.short)
        # It should contain titles of at1 and at2, but not at4
        # We need to be careful about what make_article_source produces as titles
        
        # Pub2 should have 1 notification with 1 article
        note2 = None
        for n in notes1:
            if n.who == "pub2":
                note2 = n
                break
        self.assertIsNotNone(note2)
    
    def test_no_articles(self):
        # Run task without any tombstones
        job = ArticleDeletionNotificationsBackgroundTask.prepare("system")
        task = ArticleDeletionNotificationsBackgroundTask(job)
        task.run()
        
        # Verify no notifications sent
        notes = models.Notification.all()
        self.assertEqual(len(notes), 0)
        self.assertIn("No deleted articles in the last week", job.audit[0]['message'])
