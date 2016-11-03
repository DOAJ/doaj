from doajtest.helpers import DoajTestCase
from portality import models, lock
from portality.lib import dates
from doajtest.fixtures import JournalFixtureFactory
import time
from datetime import datetime, timedelta
from copy import deepcopy

class TestLock(DoajTestCase):

    def test_01_lock_success_fail(self):
        source = JournalFixtureFactory.make_journal_source()
        j = models.Journal(**source)
        j.save()

        time.sleep(2)

        # first set a lock
        l = lock.lock("journal", j.id, "testuser")
        assert l.about == j.id
        assert l.type == "journal"
        assert l.username == "testuser"
        assert not l.is_expired()

        time.sleep(2)

        # now try and set the lock again for the same thing by the same user
        l2 = lock.lock("journal", j.id, "testuser")
        assert l2 is not None
        assert l2.id == l.id

        # now try and set the lock as another user
        with self.assertRaises(lock.Locked):
            l3 = lock.lock("journal", j.id, "otheruser")

    def test_02_unlock(self):
        unlocked = lock.unlock("journal", "qojoiwjreiqwefoijqwiefjw", "testuser")
        assert unlocked is True

        source = JournalFixtureFactory.make_journal_source()
        j = models.Journal(**source)
        j.save()

        time.sleep(2)

        # first set a lock
        l = lock.lock("journal", j.id, "testuser")

        time.sleep(2)

        # try and unlock as a different user
        unlocked = lock.unlock("journal", j.id, "otheruser")
        assert unlocked is False

        # now unlock for real
        unlocked = lock.unlock("journal", j.id, "testuser")
        assert unlocked is True

    def test_03_batch_lock_unlock(self):
        source = JournalFixtureFactory.make_journal_source()
        ids = []

        # create a bunch of journals that we can play with
        j = models.Journal(**deepcopy(source))
        j.save()
        ids.append(j.id)

        j = models.Journal(**deepcopy(source))
        j.save()
        ids.append(j.id)

        j = models.Journal(**deepcopy(source))
        j.save()
        ids.append(j.id)

        j = models.Journal(**deepcopy(source))
        j.save()
        ids.append(j.id)

        j = models.Journal(**deepcopy(source))
        j.save()
        ids.append(j.id)

        time.sleep(2)

        ls = lock.batch_lock("journal", ids, "testuser")
        assert len(ls) == 5

        time.sleep(2)

        report = lock.batch_unlock("journal", ids, "testuser")
        assert len(report["success"]) == 5
        assert len(report["fail"]) == 0

        time.sleep(2)

        # now lock an individual record by a different user and check that no locks are set
        # in batch
        l = lock.lock("journal", ids[3], "otheruser")

        time.sleep(2)

        with self.assertRaises(lock.Locked):
            ls = lock.batch_lock("journal", ids, "testuser")

        for id in ids:
            assert lock.has_lock("journal", id, "testuser") is False

    def test_04_timeout(self):
        source = JournalFixtureFactory.make_journal_source()
        j = models.Journal(**source)
        j.save()

        time.sleep(2)

        after = datetime.utcnow() + timedelta(seconds=2300)

        # set a lock with a longer timout
        l = lock.lock("journal", j.id, "testuser", 2400)

        assert dates.parse(l.expires) > after

