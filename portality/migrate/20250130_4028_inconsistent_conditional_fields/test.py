from operations import enforce_consistency
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from portality import models
from copy import deepcopy

from doajtest.helpers import diff_dicts_recursive

sort_functions = {
    "[root].admin.notes": lambda x: x.get("id"),
    "[root].bibjson.language": lambda x: str(x),
    "[root].bibjson.preservation.national_library": lambda x: x
}

source = ApplicationFixtureFactory.make_application_source()
source["bibjson"]["apc"]["has_apc"] = False
source["bibjson"]["waiver"]["has_waiver"] = False
source["bibjson"]["other_charges"]["has_other_charges"] = False
compare = deepcopy(source)
application = models.Application(**source)

result = enforce_consistency(application)
rdata = result.data
assert rdata["bibjson"]["apc"]["has_apc"] == False
assert rdata["bibjson"]["waiver"]["has_waiver"] == False
assert rdata["bibjson"]["other_charges"]["has_other_charges"] == False

assert rdata["bibjson"]["apc"].get("max") is None
assert rdata["bibjson"]["waiver"].get("url") is None
assert rdata["bibjson"]["other_charges"].get("url") is None

diff_dicts_recursive(compare, rdata, "original", "corrected", sort_functions=sort_functions)


source = JournalFixtureFactory.make_journal_source(in_doaj=True)
source["bibjson"]["apc"]["has_apc"] = False
source["bibjson"]["waiver"]["has_waiver"] = False
source["bibjson"]["other_charges"]["has_other_charges"] = False
compare = deepcopy(source)
journal = models.Journal(**source)

result = enforce_consistency(journal)
rdata = result.data
assert rdata["bibjson"]["apc"]["has_apc"] == False
assert rdata["bibjson"]["waiver"]["has_waiver"] == False
assert rdata["bibjson"]["other_charges"]["has_other_charges"] == False

assert rdata["bibjson"]["apc"].get("max") is None
assert rdata["bibjson"]["waiver"].get("url") is None
assert rdata["bibjson"]["other_charges"].get("url") is None

diff_dicts_recursive(compare, rdata, "original", "corrected", sort_functions=sort_functions)