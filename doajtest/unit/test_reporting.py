from doajtest.helpers import DoajTestCase
from doajtest.fixtures import ProvenanceFixtureFactory, ApplicationFixtureFactory

import time, os, shutil, codecs, csv
from copy import deepcopy

from portality import reporting
from portality.lib import dates, paths

MONTH_EDIT_OUTPUT = [
    ["User", "2015-01", "2015-02", "2015-03", "2015-04", "2015-05", "2015-06"],
    ["u1", 0, 1, 2, 3, 4, 5],
    ["u2", 6, 7, 8, 9, 10, 0],
    ["u3", 11, 12, 13, 14, 15, 16]
]

YEAR_EDIT_OUTPUT = [
    ["User", "2015"],
    ["u1", 15],
    ["u2", 40],
    ["u3", 81]
]

MONTH_COMPLETE_OUTPUT = [
    ["User", "2015-01", "2015-02", "2015-03", "2015-04", "2015-05", "2015-06"],
    ["u1", 0, 1, 2, 3, 4, 5],
    ["u2", 6, 7, 8, 9, 10, 0],
    ["u3", 11, 12, 13, 14, 15, 16]
]

YEAR_COMPLETE_OUTPUT = [
    ["User", "2015"],
    ["u1", 15],
    ["u2", 40],
    ["u3", 81]
]

APPLICATION_YEAR_OUTPUT = [
    ["Country", "2010", "2011", "2012", "2013", "2014", "2015"],
    ["Angola", 0, 1, 2, 3, 4, 5],
    ["Belarus", 6, 7, 8 , 9, 10, 0],
    ["Cambodia", 11, 12, 13, 14, 15, 16]
]

TMP_DIR = paths.rel2abs(__file__, "resources/reports")

class TestReporting(DoajTestCase):
    def setUp(self):
        super(TestReporting, self).setUp()
        if os.path.exists(TMP_DIR):
            shutil.rmtree(TMP_DIR)
        os.mkdir(TMP_DIR)

    def tearDown(self):
        super(TestReporting, self).tearDown()
        shutil.rmtree(TMP_DIR)

    def _as_output(self, table):
        table = deepcopy(table)
        for row in table:
            for i in range(len(row)):
                row[i] = unicode(row[i])
        return table

    def test_01_edits(self):
        provs = ProvenanceFixtureFactory.make_action_spread(MONTH_EDIT_OUTPUT, "edit", "month")
        for p in provs:
            p.save()
        time.sleep(2)

        outfiles = reporting.provenance_reports("2015-01-01T00:00:00Z", "2016-01-01T00:00:00Z", TMP_DIR)

        monthfile = None
        yearfile = None

        assert len(outfiles) == 4
        for o in outfiles:
            assert os.path.exists(o)
            if o.startswith(os.path.join(TMP_DIR, "edit_by_month")):
                monthfile = o
            elif o.startswith(os.path.join(TMP_DIR, "edit_by_year")):
                yearfile = o

        table_month = []
        with codecs.open(monthfile) as f:
            reader = csv.reader(f)
            for row in reader:
                table_month.append(row)

        expected_month = self._as_output(MONTH_EDIT_OUTPUT)
        assert table_month == expected_month

        table_year = []
        with codecs.open(yearfile) as f:
            reader = csv.reader(f)
            for row in reader:
                table_year.append(row)

        expected_year = self._as_output(YEAR_EDIT_OUTPUT)
        assert table_year == expected_year

    def test_02_completes(self):
        provs = ProvenanceFixtureFactory.make_status_spread(MONTH_COMPLETE_OUTPUT, "month", {"u1" : "admin", "u2" : "editor", "u3" : "associate_editor"})
        for p in provs:
            p.save()
        time.sleep(2)

        outfiles = reporting.provenance_reports("2015-01-01T00:00:00Z", "2016-01-01T00:00:00Z", TMP_DIR)

        monthfile = None
        yearfile = None

        assert len(outfiles) == 4
        for o in outfiles:
            assert os.path.exists(o)
            if o.startswith(os.path.join(TMP_DIR, "completion_by_month")):
                monthfile = o
            elif o.startswith(os.path.join(TMP_DIR, "completion_by_year")):
                yearfile = o

        table_month = []
        with codecs.open(monthfile) as f:
            reader = csv.reader(f)
            for row in reader:
                table_month.append(row)

        expected_month = self._as_output(MONTH_COMPLETE_OUTPUT)
        assert table_month == expected_month

        table_year = []
        with codecs.open(yearfile) as f:
            reader = csv.reader(f)
            for row in reader:
                table_year.append(row)

        expected_year = self._as_output(YEAR_COMPLETE_OUTPUT)
        assert table_year == expected_year

    def test_03_apps_by_country(self):
        apps = ApplicationFixtureFactory.make_application_spread(APPLICATION_YEAR_OUTPUT, "year")
        for a in apps:
            a.save()
        time.sleep(2)

        outfiles = reporting.content_reports("1970-01-01T00:00:00Z", dates.now(), TMP_DIR)

        assert len(outfiles) == 1
        assert os.path.exists(outfiles[0])

        table = []
        with codecs.open(outfiles[0]) as f:
            reader = csv.reader(f)
            for row in reader:
                table.append(row)

        expected = self._as_output(APPLICATION_YEAR_OUTPUT)
        assert table == expected