import time

from portality.constants import BgjobOutcomeStatus
from portality.lib import dates
from portality.core import app
from portality.tasks import find_flags_with_approaching_deadline
from portality.background import BackgroundApi
from doajtest.fixtures import JournalFixtureFactory
from portality.models import Journal
from doajtest.helpers import DoajTestCase
from portality.ui.messages import Messages


class TestFindApproachingDeadlines(DoajTestCase):

    def setUp(self):
        self.journal_found_message = Messages.JOURNALS_WITH_APPROACHING_DEADLINES_FOUND[:15]
        super(TestFindApproachingDeadlines, self).setUp()

    def tearDown(self):
        super(TestFindApproachingDeadlines, self).tearDown()

    def test_1_success(self):

        jsource = JournalFixtureFactory.make_journal_source(in_doaj=True)
        imaginary_agriculture = Journal(**jsource)
        imaginary_agriculture.set_id("imaginary_agriculture")
        imaginary_agriculture.bibjson().title = "International Journal of Imaginary Agriculture"
        imaginary_agriculture.add_note("This is not very urgent", date=dates.today(), author_id="ProfessorSnifflepuff", assigned_to="DameQuacksalot", deadline=dates.format(dates.days_after_now(30), dates.FMT_DATE_STD))
        imaginary_agriculture.save(blocking=True)

        jsource2 = JournalFixtureFactory.make_journal_source(in_doaj=True)
        unlikely_engineering = Journal(**jsource2)
        unlikely_engineering.set_id("annalsofunlikelyengineering")
        unlikely_engineering.bibjson().title = "Annals of Unlikely Engineering"
        unlikely_engineering.add_note("This deadline is soon", date=dates.today(), author_id="ProfessorSnifflepuff",
                                       assigned_to="DameQuacksalot", deadline=dates.format(dates.days_after_now(app.config.get('APPROACHING_DEADLINE_DELTA', 7)), dates.FMT_DATE_STD))
        unlikely_engineering.save(blocking=True)


        user = app.config.get("SYSTEM_USERNAME")
        job = find_flags_with_approaching_deadline.FindFlagsWithApproachingDeadlineTask.prepare(user)
        task = find_flags_with_approaching_deadline.FindFlagsWithApproachingDeadlineTask(job)
        BackgroundApi.execute(task)

        job = task.background_job
        assert job.status == "complete"
        assert len(job.audit) > 2
        journal_found_log = [p["message"] for p in job.audit if p["message"].startswith(self.journal_found_message)]
        assert len(journal_found_log) == 1
        assert journal_found_log[0].split(": ")[-1] == unlikely_engineering.id
        assert job.outcome_status == BgjobOutcomeStatus.Success