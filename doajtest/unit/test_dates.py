from doajtest.helpers import DoajTestCase, assert_expected_dict
from portality.lib import dates
from datetime import datetime, timedelta

DATETIME_STR_A = '1234-11-12'
DATETIME_A = datetime.strptime(DATETIME_STR_A, dates.FMT_DATE_STD)
DATETIME_STR_B = '2014-09-23T11:30:45Z'
DATETIME_B = datetime.strptime(DATETIME_STR_B, dates.FMT_DATETIME_STD)
DATETIME_STR_C = '29/02/80'
DATETIME_C = datetime.strptime(DATETIME_STR_C, "%d/%m/%y")


class TestDates(DoajTestCase):

    def assert_datetime(self, datetime_str: str, expect: dict, **kwargs):
        target = dates.parse(datetime_str, **kwargs)
        assert isinstance(target, datetime)
        assert_expected_dict(self, target, expect)

    def test_parse(self):
        cases = [
            (DATETIME_STR_A, dict(year=1234, month=11, hour=0)),
            (DATETIME_STR_C, dict(year=1980, month=2, day=29, hour=0)),
            (DATETIME_STR_B, dict(year=2014, month=9, day=23, hour=11, microsecond=0)),
            ('2010-01-01T00:00:00.123Z', dict(year=2010, month=1, day=1, hour=0, microsecond=123000)),
            ('February 2014', dict(year=2014, month=2, day=1, hour=0, microsecond=0)),
            ('1978', dict(year=1978, month=1, day=1, hour=0, microsecond=0)),
        ]
        for datetime_str, expected in cases:
            self.assert_datetime(datetime_str, expected)

    def test_parse__bad_datetime_str(self):
        for bad_val in ['asdkjaslkdj',
                        '01/30/80',  # invalid month value
                        '1234@11@12',  # unsupported format
                        '2014-09-23T11:30:45',  # missing Z
                        '',
                        ]:
            with self.assertRaises(ValueError, msg=f'bad_val[{bad_val}]'):
                dates.parse(bad_val)

    def test_parse__guess(self):
        self.assert_datetime(DATETIME_STR_A, dict(year=1234, month=11, hour=0), guess=False)
        with self.assertRaises(ValueError):
            dates.parse(DATETIME_STR_A, dates.FMT_DATE_HUMAN, guess=False)

    def test_format(self):
        assert dates.format(DATETIME_B) == DATETIME_STR_B
        assert dates.format(DATETIME_B, format=dates.FMT_DATE_YMDOT) == '2014.09'

    def test_reformat(self):
        assert dates.reformat(DATETIME_STR_C) == '1980-02-29T00:00:00Z'
        assert dates.reformat(DATETIME_STR_C, out_format=dates.FMT_DATE_HUMAN) == '29 February 1980'

        # reformat still work even in_format incorrect
        assert dates.reformat(DATETIME_STR_C, in_format=dates.FMT_DATE_HUMAN) == '1980-02-29T00:00:00Z'

    def test_now(self):
        assert isinstance(dates.now(), datetime)
        assert dates.now().year == datetime.now().year

    def test_random_date(self):

        from_val = dates.parse(dates.DEFAULT_TIMESTAMP_VAL)
        to_val = dates.now()
        datetime_val = dates.parse(dates.random_date())
        assert from_val <= datetime_val <= to_val

        datetime_val = dates.parse(dates.random_date(to=DATETIME_C))
        assert from_val <= datetime_val <= to_val

    def test_day_ranges(self):
        assert dates.day_ranges(DATETIME_C, DATETIME_C + timedelta(days=3)) == [
            ('1980-02-29T00:00:00Z', '1980-03-01T00:00:00Z'),
            ('1980-03-01T00:00:00Z', '1980-03-02T00:00:00Z'),
            ('1980-03-02T00:00:00Z', '1980-03-03T00:00:00Z'),
            ('1980-03-03T00:00:00Z', '1980-03-03T00:00:00Z'),
        ]

        assert dates.day_ranges(DATETIME_C + timedelta(days=3), DATETIME_C) == [
            ('1980-03-03T00:00:00Z', '1980-02-29T00:00:00Z')
        ]
