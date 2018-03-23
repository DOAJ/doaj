import time

from parameterized import parameterized, param

from portality import constants
from doajtest.fixtures import ApplicationFixtureFactory, AccountFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.models import Account, Suggestion, Provenance

CASES = [
    ["1", "None", "None", True, "ArgEx"],
    ["2", "None", "None", False, "ArgEx"],
    ["3", "None", "Permit", True, "ArgEx"],
    ["4", "None", "Permit", False, "ArgEx"],
    ["5", "None", "Forbid", True, "ArgEx"],
    ["6", "None", "Forbid", False, "ArgEx"],
    ["7", "App", "None", True, "ArgEx"],
    ["8", "App", "None", False, "ArgEx"],
    ["9", "App", "Permit", True, "rejected_prov"],
    ["10", "App", "Permit", False, "rejected_no_prov"],
    ["11", "App", "Forbid", True, "AuthEx"],
    ["12", "App", "Forbid", False, "AuthEx"]
]

def load_test_cases():

    cases = []
    for case in CASES:
        name = case[0]
        make_app = case[1]
        make_account = case[2]
        prov = case[3]
        result = case[4]

        application = None
        if make_app == "App":
            application = Suggestion(**ApplicationFixtureFactory.make_application_source())

        account = None
        if make_account == "Permit":
            account = Account(**AccountFixtureFactory.make_managing_editor_source())
        elif make_account == "Forbid":
            account = Account(**AccountFixtureFactory.make_editor_source())

        kwargs = {}
        if result == "ArgEx":
            kwargs["raises"] = exceptions.ArgumentException
        elif result == "AuthEx":
            kwargs["raises"] = exceptions.AuthoriseException
        elif result == "rejected_prov":
            kwargs["comparator"] = rejected_prov
        elif result == "rejected_no_prov":
            kwargs["comparator"] = rejected_no_prov

        cases.append(param(name, application, account, prov, **kwargs))

    return cases

def rejected_prov(application):
    assert application.application_status == constants.APPLICATION_STATUS_REJECTED
    assert application.current_journal is None
    assert application.related_journal == "123456789987654321"

    prov = Provenance.get_latest_by_resource_id(application.id)
    assert prov is not None

def rejected_no_prov(application):
    assert application.application_status == constants.APPLICATION_STATUS_REJECTED
    assert application.current_journal is None
    assert application.related_journal == "123456789987654321"

    prov = Provenance.get_latest_by_resource_id(application.id)
    assert prov is None

class TestBLRejectApplication(DoajTestCase):

    @parameterized.expand(load_test_cases)
    def test_01_reject_application(self, name, application, account, provenance, raises=None, comparator=None):
        doaj = DOAJ()
        if raises is not None:
            with self.assertRaises(raises):
                doaj.reject_application(application, account, provenance)
        elif comparator is not None:
            doaj.reject_application(application, account, provenance)
            time.sleep(1)
            comparator(application)
        else:
            assert False, "Specify either raises or comparator"
