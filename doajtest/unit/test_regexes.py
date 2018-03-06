""" Gather and test DOAJ regexes here """

from doajtest.helpers import DoajTestCase
from portality.view.forms import DOI_REGEX
from doajtest.fixtures import dois

import re


class TestRegexes(DoajTestCase):

    def setUp(self):
        super(TestRegexes, self).setUp()

    def tearDown(self):
        super(TestRegexes, self).tearDown()

    def test_01_DOI_regex(self):
        """ Check that the DOI regex (used for validating forms) accepts what we expect. """
        doi_regex = re.compile(DOI_REGEX)

        # DOI regex should match our list of valid DOIs
        for d in dois.DOI_LIST:
            assert doi_regex.match(d), d

        # And handle identifiers too
        for h in dois.HANDLE_LIST:
            assert not doi_regex.match(h), h

        # But not something unrelated to DOIs
        for x in dois.INVALID_LIST:
            assert not doi_regex.match(x), x

    # TODO: test other regexes (ISSN etc)
