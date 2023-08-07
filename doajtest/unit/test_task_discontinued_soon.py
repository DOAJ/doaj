import unittest
import datetime

from doajtest.helpers import DoajTestCase

from portality.core import app
from portality import models
from portality.tasks import find_discontinued_soon
from portality.ui.messages import Messages
from doajtest.fixtures import JournalFixtureFactory

DELTA = app.config.get('DISCONTINUED_DATE_DELTA',1)

class TestDiscontinuedSoon(DoajTestCase):

    def _date_to_found(self):
        return (datetime.datetime.today() + datetime.timedelta(days=DELTA)).strftime('%Y-%m-%d')

    def _date_too_late(self):
        return (datetime.datetime.today() + datetime.timedelta(days=DELTA+1)).strftime('%Y-%m-%d')

    def test_discontinued_soon_found(self):

        # Both these should be found
        journal_discontinued_to_found_1 = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal_discontinued_to_found_1.set_id("1")
        jbib = journal_discontinued_to_found_1.bibjson()
        jbib.title = "Discontinued Tomorrow 1"
        jbib.discontinued_date = self._date_to_found()
        journal_discontinued_to_found_1.save(blocking=True)

        journal_discontinued_to_found_2 = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal_discontinued_to_found_2.set_id("2")
        jbib = journal_discontinued_to_found_2.bibjson()
        jbib.title = "Discontinued Tomorrow 2"
        jbib.discontinued_date = self._date_to_found()
        journal_discontinued_to_found_2.save(blocking=True)

        # that shouldn't be found
        journal_discontinued_too_late = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal_discontinued_too_late.set_id("3")
        jbib = journal_discontinued_too_late.bibjson()
        jbib.title = "Discontinued In 2 days"
        jbib.discontinued_date = self._date_too_late()
        journal_discontinued_too_late.save(blocking=True)

        job = find_discontinued_soon.FindDiscontinuedSoonBackgroundTask.prepare("system")
        task = find_discontinued_soon.FindDiscontinuedSoonBackgroundTask(job)
        task.run()

        assert len(job.audit) == 2
        assert job.audit[0]["message"] == Messages.DISCONTINUED_JOURNAL_FOUND_LOG.format(id="1")
        assert job.audit[1]["message"] == Messages.DISCONTINUED_JOURNAL_FOUND_LOG.format(id="2")

    def test_discontinued_soon_not_found(self):

        # None of these should be found - this one discontinues in 2 days
        journal_discontinued_too_late = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal_discontinued_too_late.set_id("1")
        jbib = journal_discontinued_too_late.bibjson()
        jbib.title = "Discontinued In 2 days"
        jbib.discontinued_date = self._date_too_late()
        journal_discontinued_too_late.save(blocking=True)

        # this one is not in doaj
        journal_not_in_doaj = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=False))
        journal_not_in_doaj.set_id("2")
        jbib = journal_not_in_doaj.bibjson()
        jbib.discontinued_date = self._date_to_found()
        journal_not_in_doaj.save(blocking=True)

        job = find_discontinued_soon.FindDiscontinuedSoonBackgroundTask.prepare("system")
        task = find_discontinued_soon.FindDiscontinuedSoonBackgroundTask(job)
        task.run()

        assert len(job.audit) == 1
        assert job.audit[0]["message"] == Messages.NO_DISCONTINUED_JOURNALS_FOUND_LOG
