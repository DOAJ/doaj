from doajtest.helpers import DoajTestCase
from doajtest.fixtures import ApplicationFixtureFactory

from portality.autocheck.checkers.publication_time import PublicationTime
from portality import app, models, core

publication_time_threshold = app.app.config.get("AUTOCHECK_PUBLICATION_THRESHOLD", 2)

class TestPublicationTime(DoajTestCase):

    def test_01_publication_time_short(self):

        publication_time = PublicationTime()

        form = {
            "publication_time_weeks": str(publication_time_threshold - 1),
        }

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)

        autochecks = models.Autocheck()

        publication_time.check(form, app, autochecks, None, logger=lambda x: x)

        assert len(autochecks.checks) == 1
        check = autochecks.checks[0]
        assert check.get("advice") == publication_time.BELOW_THRESHOLD

    def test_02_publication_time_edge_case(self):

        publication_time = PublicationTime()

        form = {
            "publication_time_weeks": str(publication_time_threshold),
        }

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)

        autochecks = models.Autocheck()

        publication_time.check(form, app, autochecks, None, logger=lambda x: x)

        assert len(autochecks.checks) == 1
        check = autochecks.checks[0]
        assert check.get("advice") == publication_time.BELOW_THRESHOLD


    def test_02_publication_time_long(self):

        publication_time = PublicationTime()

        form = {
            "publication_time_weeks": str(publication_time_threshold + 1),
        }

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)

        autochecks = models.Autocheck()

        publication_time.check(form, app, autochecks, None, logger=lambda x: x)

        assert len(autochecks.checks) == 1
        check = autochecks.checks[0]
        assert check.get("advice") == publication_time.OVER_THRESHOLD