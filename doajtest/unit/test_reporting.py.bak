# -*- coding: UTF-8 -*-

from doajtest.helpers import DoajTestCase
from doajtest.fixtures import ProvenanceFixtureFactory, ApplicationFixtureFactory

import time, os, shutil, codecs, csv
from copy import deepcopy

from portality import clcsv, models
from portality.tasks import reporting
from portality.lib import dates, paths

MONTH_EDIT_OUTPUT = [
    ["User", "2015-01", "2015-02", "2015-03", "2015-04", "2015-05", "2015-06"],
    ["u1", 0, 1, 2, 3, 4, 5],
    ["u2", 6, 7, 8, 9, 10, 0],
    ["u3", 11, 12, 13, 14, 15, 16],
    ["u4", 2, 5, 0, 8, 13, 21],
    ["u5", 2, 5, 0, 8, 0, 4],
]

YEAR_EDIT_OUTPUT = [
    ["User", "2015"],
    ["u1", 15],
    ["u2", 40],
    ["u3", 81],
    ["u4", 49],
    ["u5", 19],
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
    [u"Cambôdia", 11, 12, 13, 14, 15, 16]
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
        with codecs.open(outfiles[0], "rb", "utf-8") as f:
            reader = clcsv.UnicodeReader(f)
            for row in reader:
                table.append(row)

        expected = self._as_output(APPLICATION_YEAR_OUTPUT)
        assert table == expected

    def test_04_background(self):
        provs = ProvenanceFixtureFactory.make_action_spread(MONTH_EDIT_OUTPUT, "edit", "month")
        for p in provs:
            p.save()

        apps = ApplicationFixtureFactory.make_application_spread(APPLICATION_YEAR_OUTPUT, "year")
        for a in apps:
            a.save()

        time.sleep(2)

        job = reporting.ReportingBackgroundTask.prepare("system", outdir=TMP_DIR, from_date="1970-01-01T00:00:00Z", to_date=dates.now())
        reporting.ReportingBackgroundTask.submit(job)

        time.sleep(2)

        job = models.BackgroundJob.pull(job.id)
        prov_outfiles = job.reference["reporting__provenance_outfiles"]
        cont_outfiles = job.reference["reporting__content_outfiles"]

        assert len(prov_outfiles) == 4
        assert len(cont_outfiles) == 1

    def test_05_status_role(self):
        counter = reporting.StatusCounter("month")

        roles = ["admin"]
        best = counter._get_best_role(roles)
        assert best == "admin"

        roles = ["associate_editor", "editor", "admin"]
        best = counter._get_best_role(roles)
        assert best == "admin"

        roles = ["api"]
        best = counter._get_best_role(roles)
        assert best is None

        roles = ["api", "whatever", "another"]
        best = counter._get_best_role(roles)
        assert best is None

        roles = ["associate_editor", "api", "editor"]
        best = counter._get_best_role(roles)
        assert best == "editor"

        roles = ["api", "associate_editor", "editor"]
        best = counter._get_best_role(roles)
        assert best == "editor"

    def test_06_status_is_countable(self):
        counter = reporting.StatusCounter("month")

        # We now disregard role and count all completion events per user https://github.com/DOAJ/doaj/issues/1385
        admin_accepted = models.Provenance(user="testuser", roles=["admin", "editor", "associate_editor"], action="status:accepted")
        assert counter._is_countable(admin_accepted, "admin")
        assert counter._is_countable(admin_accepted, "editor")
        assert counter._is_countable(admin_accepted, "associate_editor")
        assert counter._is_countable(admin_accepted, "api")

        admin_rejected = models.Provenance(user="testuser", roles=["admin", "editor", "associate_editor"], action="status:rejected")
        assert counter._is_countable(admin_rejected, "admin")
        assert counter._is_countable(admin_rejected, "editor")
        assert counter._is_countable(admin_rejected, "associate_editor")
        assert counter._is_countable(admin_rejected, "api")

        editor_ready = models.Provenance(user="testuser", roles=["editor", "associate_editor"], action="status:ready")
        assert counter._is_countable(editor_ready, "editor")
        assert counter._is_countable(editor_ready, "admin")
        assert counter._is_countable(editor_ready, "associate_editor")
        assert counter._is_countable(editor_ready, "api")

        assed_completed = models.Provenance(user="testuser", roles=["associate_editor"], action="status:completed")
        assert counter._is_countable(assed_completed, "associate_editor")
        assert counter._is_countable(assed_completed, "admin")
        assert counter._is_countable(assed_completed, "editor")
        assert counter._is_countable(assed_completed, "api")

        other = models.Provenance(user="testuser", roles=["admin", "editor", "associate_editor"], action="status:other")
        assert not counter._is_countable(other, "associate_editor")
        assert not counter._is_countable(other, "admin")
        assert not counter._is_countable(other, "editor")
        assert not counter._is_countable(other, "api")
