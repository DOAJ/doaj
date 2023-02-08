import unittest
import datetime

from doajtest.helpers import DoajTestCase

from portality.core import app
from portality import models
from portality.tasks import find_discontinued_soon
from portality.ui.messages import Messages
from doajtest.fixtures import JournalFixtureFactory

class TestDiscontinuedSoon(DoajTestCase):

    def _date_tomorrow(self):
        return (datetime.datetime.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    def _date_in_2_days(self):
        return (datetime.datetime.today() + datetime.timedelta(days=2)).strftime('%Y-%m-%d')

    def test_discontinued_soon_found(self):

        # Both these should be found
        journal_discontinued_tommorow_1 = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal_discontinued_tommorow_1.set_id("1")
        jbib = journal_discontinued_tommorow_1.bibjson()
        jbib.title = "Discontinued Tomorrow 1"
        jbib.discontinued_date = self._date_tomorrow()
        journal_discontinued_tommorow_1.save(blocking=True)

        journal_discontinued_tommorow_2 = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal_discontinued_tommorow_2.set_id("2")
        jbib = journal_discontinued_tommorow_2.bibjson()
        jbib.title = "Discontinued Tomorrow 2"
        jbib.discontinued_date = self._date_tomorrow()
        journal_discontinued_tommorow_2.save(blocking=True)

        # that shouldn't be found
        journal_discontinued_in_2_days = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal_discontinued_in_2_days.set_id("3")
        jbib = journal_discontinued_in_2_days.bibjson()
        jbib.title = "Discontinued In 2 days"
        jbib.discontinued_date = self._date_in_2_days()
        journal_discontinued_in_2_days.save(blocking=True)

        job = find_discontinued_soon.FindDiscontinuedSoonBackgroundTask.prepare("system")
        task = find_discontinued_soon.FindDiscontinuedSoonBackgroundTask(job)
        task.run()

        assert len(job.audit) == 2
        assert job.audit[0]["message"] == Messages.DISCONTINUED_JOURNAL_FOUND_LOG.format(id="1")
        assert job.audit[1]["message"] == Messages.DISCONTINUED_JOURNAL_FOUND_LOG.format(id="2")

    def test_discontinued_soon_not_found(self):

        # None of these should be found - this one discontinues in 2 days
        journal_discontinued_in_2_days = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal_discontinued_in_2_days.set_id("1")
        jbib = journal_discontinued_in_2_days.bibjson()
        jbib.title = "Discontinued In 2 days"
        jbib.discontinued_date = self._date_in_2_days()
        journal_discontinued_in_2_days.save(blocking=True)

        # this one is not in doaj
        journal_not_in_doaj = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=False))
        journal_not_in_doaj.set_id("2")
        jbib = journal_not_in_doaj.bibjson()
        jbib.discontinued_date = self._date_tomorrow()
        journal_not_in_doaj.save(blocking=True)

        job = find_discontinued_soon.FindDiscontinuedSoonBackgroundTask.prepare("system")
        task = find_discontinued_soon.FindDiscontinuedSoonBackgroundTask(job)
        task.run()

        assert len(job.audit) == 1
        assert job.audit[0]["message"] == Messages.NO_DISCONTINUED_JOURNALS_FOUND_LOG
