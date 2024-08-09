from doajtest.fixtures import ApplicationFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models
from portality.autocheck.checkers import no_none_value
from portality.autocheck.checkers.no_none_value import NoNoneValue
from portality.autocheck.resource_bundle import ResourceBundle
from portality.crosswalks.application_form import ApplicationFormXWalk
from portality.models import JournalLikeObject


def run_check(checker, form: dict, jla: JournalLikeObject, resources=None):
    if resources is None:
        resources = ResourceBundle()

    autochecks = models.Autocheck()
    checker.check(form, jla, autochecks, resources, logger=print)
    return autochecks


def fixture_standard_application(modify_fn=None):
    source = ApplicationFixtureFactory.make_application_source()
    app = models.Application(**source)
    modify_fn and modify_fn(app)
    form = ApplicationFormXWalk.obj2form(app)
    return form, app


class TestNoNoneValue(DoajTestCase):

    def test_check__pass(self):
        form, app = fixture_standard_application()
        autochecks = run_check(NoNoneValue(), form, app)
        assert len(autochecks.checks) == 0

    def test_check__fail_all(self):
        def modify_fn(app):
            bibjson = app.bibjson()
            bibjson.preservation["national_library"] = ['None']
            bibjson.preservation["service"] = ['None']
            bibjson.deposit_policy = ['None']
            bibjson.persistent_identifier_scheme = ['None']

        form, app = fixture_standard_application(modify_fn)

        autochecks = run_check(NoNoneValue(), form, app)
        assert len(autochecks.checks) == 4

        for check in autochecks.checks:
            print(check)
            assert check['checked_by'] == NoNoneValue.__identity__
            assert check['advice'] == no_none_value.ADVICE_NONE_VALUE_FOUND

    def test_check__fail_library(self):
        def modify_fn(app):
            bibjson = app.bibjson()
            bibjson.preservation["national_library"] = ['aaa', 'None']

        form, app = fixture_standard_application(modify_fn)
        autochecks = run_check(NoNoneValue(), form, app)
        assert len(autochecks.checks) == 1
        assert autochecks.checks[0]['field'] == 'preservation_service_library'

    def test_check__fail_deposit(self):
        def modify_fn(app):
            bibjson = app.bibjson()
            bibjson.deposit_policy = ['None']

        form, app = fixture_standard_application(modify_fn)
        autochecks = run_check(NoNoneValue(), form, app)
        assert len(autochecks.checks) == 1
        assert autochecks.checks[0]['field'] == 'deposit_policy_other'
        assert autochecks.checks[0]['original_value'] == 'None'

    def test_check__pass_deposit(self):
        def modify_fn(app):
            bibjson = app.bibjson()
            bibjson.deposit_policy = ['aa', 'None']

        form, app = fixture_standard_application(modify_fn)
        autochecks = run_check(NoNoneValue(), form, app)
        assert len(autochecks.checks) == 0
