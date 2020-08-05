import datetime, calendar
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from doajtest.helpers import DoajTestCase
from portality.scripts.prune_marvel import generate_delete_pattern


class TestPruneMarvel(DoajTestCase):

    @classmethod
    def setUpClass(cls):
        cls.runs = []
        years = [2016, 2017]
        for year in years:
            for month in range(1, 13):
                num_days = calendar.monthrange(year, month)[1]
                days = [datetime.date(year, month, day) for day in range(1, num_days + 1)]
                for day in days:
                    cls.runs.append(day)  # datetime(2016, 1, 1) .. datetime(2017, 12, 31)

    @classmethod
    def tearDownClass(cls):
        cls.runs = []

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_generate_delete_pattern(self):
        for run in self.runs:
            with freeze_time(run):
                expected_delete_date = run - relativedelta(months=3)
                expected_delete_pattern = '.marvel-{}*'.format(expected_delete_date.strftime('%Y.%m'))
                actual_delete_pattern = generate_delete_pattern()
                assert actual_delete_pattern == expected_delete_pattern, 'Current time: {}. {} did not match expected {}'.format(run, generate_delete_pattern(), expected_delete_pattern)
                assert len(actual_delete_pattern) == 16, "actual_delete_pattern is the wrong length: {} characters for '{}'".format(len(actual_delete_pattern), actual_delete_pattern)

