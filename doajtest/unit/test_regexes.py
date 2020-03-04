""" Gather and test DOAJ regexes here """

from doajtest.helpers import DoajTestCase
from portality.view.forms import ISSN_REGEX
from portality.formcontext.forms import DOI_REGEX
from doajtest.fixtures import dois, issns

import re


class TestRegexes(DoajTestCase):

    def setUp(self):
        pass                                                                               # no need to set up the index

    def tearDown(self):
        pass

    def test_01_DOI_regex(self):
        """ Check that the DOI regex (used for validating forms) accepts what we expect. """
        doi_regex = re.compile(DOI_REGEX)

        # DOI regex should match our list of valid DOIs
        for d in dois.DOI_LIST:
            assert doi_regex.match(d), d

        # And handle identifiers too
        for h in dois.HANDLE_LIST:
            assert doi_regex.match(h), h

        # But not something unrelated to DOIs
        for x in dois.INVALID_DOI_LIST:
            assert not doi_regex.match(x), x

    def test_02_ISSN_regex(self):
        """ Check that the ISSN regex performs correctly. """
        issn_regex = re.compile(ISSN_REGEX)

        for i in issns.ISSN_LIST:
            assert issn_regex.match(i), i

        for x in issns.INVLAID_ISSN_LIST:
            assert not issn_regex.match(x), x
