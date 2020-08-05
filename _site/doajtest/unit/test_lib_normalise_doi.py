from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets
from unittest import TestCase

from portality.lib.paths import rel2abs
from portality.lib.normalise import normalise_doi

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "lib_normalise_doi"), "normalise_doi", "test_id",
                               {"test_id" : []})

EXCEPTIONS = {
    "ValueError" : ValueError
}

class TestLibNormaliseDOI(TestCase):

    def setUp(self):
        super(TestLibNormaliseDOI, self).setUp()

    def tearDown(self):
        super(TestLibNormaliseDOI, self).tearDown()

    @parameterized.expand(load_cases)
    def test_01_normalise_doi(self, name, kwargs):

        doi_arg = kwargs.get("doi")
        prefix_arg = kwargs.get("prefix")
        whitespace_arg = kwargs.get("whitespace")

        raises_arg = kwargs.get("raises")
        raises = EXCEPTIONS.get(raises_arg)

        ###############################################
        ## set up

        rawDOI = None
        if doi_arg != "none":
            rawDOI = "10.1234/abc/122"

        doi = rawDOI
        if prefix_arg not in ["-", "invalid", "none"]:
            doi = prefix_arg + doi
        elif prefix_arg == "invalid":
            doi = "somerubbish" + doi

        if whitespace_arg == "yes":
            doi = "   " + doi + "\t\n"

        ###########################################################
        # Execution

        if raises is not None:
            with self.assertRaises(raises):
                norm = normalise_doi(doi)
        else:
            norm = normalise_doi(doi)
            assert norm == rawDOI
