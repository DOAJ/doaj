from doajtest.helpers import DoajTestCase
from portality import models, lock
from portality.lib import dates
from portality.lib.dates import FMT_DATETIME_STD
from doajtest.fixtures import JournalFixtureFactory
from datetime import timedelta
from copy import deepcopy


class TestLock(DoajTestCase):

    def test_01_lock_success_fail(self):
        source = JournalFixtureFactory.make_journal_source()
        j = models.Journal(**source)
        j.save(blocking=True)

        # first set a lock
        l = lock.lock("journal", j.id, "testuser", blocking=True)
        assert l.about == j.id
        assert l.type == "journal"
        assert l.username == "testuser"
        assert not l.is_expired()

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
        j.save(blocking=True)

        # first set a lock
        l = lock.lock("journal", j.id, "testuser", blocking=True)

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

        ls = lock.batch_lock("journal", ids, "testuser")
        assert len(ls) == 5

        # refresh so the locks (saved non-blocking inside batch_lock) are immediately searchable
        models.Lock.refresh()

        report = lock.batch_unlock("journal", ids, "testuser")
        assert len(report["success"]) == 5
        assert len(report["fail"]) == 0

        # refresh so the deletes from batch_unlock are visible before the next lock
        models.Lock.refresh()

        # now lock an individual record by a different user and check that no locks are set
        # in batch
        l = lock.lock("journal", ids[3], "otheruser", blocking=True)

        with self.assertRaises(lock.Locked):
            ls = lock.batch_lock("journal", ids, "testuser")

        # refresh so any rollback writes/deletes from batch_lock are visible
        models.Lock.refresh()

        for id in ids:
            assert lock.has_lock("journal", id, "testuser") is False

    def test_04_timeout(self):
        source = JournalFixtureFactory.make_journal_source()
        j = models.Journal(**source)
        j.save()

        after = dates.now() + timedelta(seconds=2300)

        # set a lock with a longer timeout
        l = lock.lock("journal", j.id, "testuser", 2400)

        assert dates.parse(l.expires) > after

    def test_05_expired_lock_takeover(self):
        """An expired lock held by another user can be overwritten"""
        resource_id = "test_resource_expiry"

        # manually create an already-expired lock held by "otheruser"
        expired = models.Lock()
        expired.set_about(resource_id)
        expired.set_type("journal")
        expired.set_username("otheruser")
        expired.data["expires"] = (dates.now() - timedelta(seconds=60)).strftime(FMT_DATETIME_STD)
        expired.save(blocking=True)

        # testuser should be able to acquire it since the existing lock is expired
        l = lock.lock("journal", resource_id, "testuser", blocking=True)
        assert l.username == "testuser"
        assert not l.is_expired()

        # the Locked exception carries the conflicting lock object when a live lock blocks us
        with self.assertRaises(lock.Locked) as ctx:
            lock.lock("journal", resource_id, "seconduser")
        assert ctx.exception.lock is not None
        assert ctx.exception.lock.username == "testuser"

    def test_06_has_lock(self):
        """has_lock correctly reflects lock state for all relevant scenarios"""
        resource_id = "test_resource_has_lock"

        # no lock exists yet
        assert lock.has_lock("journal", resource_id, "testuser") is False

        # set a lock for testuser and confirm it is visible
        lock.lock("journal", resource_id, "testuser", blocking=True)
        assert lock.has_lock("journal", resource_id, "testuser") is True
        assert lock.has_lock("journal", resource_id, "otheruser") is False

        # after unlocking, testuser no longer holds the lock
        lock.unlock("journal", resource_id, "testuser")
        models.Lock.refresh()
        assert lock.has_lock("journal", resource_id, "testuser") is False

        # an expired lock does not count as holding the lock
        expired = models.Lock()
        expired.set_about(resource_id)
        expired.set_type("journal")
        expired.set_username("testuser")
        expired.data["expires"] = (dates.now() - timedelta(seconds=60)).strftime(FMT_DATETIME_STD)
        expired.save(blocking=True)
        assert lock.has_lock("journal", resource_id, "testuser") is False

    def test_07_batch_unlock_partial_failure(self):
        """batch_unlock reports per-resource success/failure when locks are held by different users"""
        testuser_ids = ["resource_a", "resource_b", "resource_c"]
        otheruser_ids = ["resource_d", "resource_e"]

        for rid in testuser_ids:
            lock.lock("journal", rid, "testuser", blocking=True)
        for rid in otheruser_ids:
            lock.lock("journal", rid, "otheruser", blocking=True)

        models.Lock.refresh()

        report = lock.batch_unlock("journal", testuser_ids + otheruser_ids, "testuser")

        assert set(report["success"]) == set(testuser_ids)
        assert set(report["fail"]) == set(otheruser_ids)
