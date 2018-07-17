from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets
from unittest import TestCase

from portality.lib.paths import rel2abs
from portality.lib.normalise import normalise_url

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "lib_normalise_url"), "normalise_url", "test_id",
                               {"test_id" : []})

EXCEPTIONS = {
    "ValueError" : ValueError
}

class TestLibNormaliseURL(TestCase):

    def setUp(self):
        super(TestLibNormaliseURL, self).setUp()

    def tearDown(self):
        super(TestLibNormaliseURL, self).tearDown()

    @parameterized.expand(load_cases)
    def test_01_normalise_url(self, name, kwargs):

        url_arg = kwargs.get("url")
        scheme_arg = kwargs.get("scheme")
        whitespace_arg = kwargs.get("whitespace")

        raises_arg = kwargs.get("raises")
        raises = EXCEPTIONS.get(raises_arg)

        ###############################################
        ## set up

        rawUrl = None
        if url_arg != "none":
            rawUrl = "//example.com/path;p=1?query=one&two=three#frag"

        url = rawUrl
        if scheme_arg not in ["-", "invalid", "none"]:
            url = scheme_arg + ":" + url
        elif scheme_arg == "invalid":
            url = "somerubbish" + url
        elif scheme_arg == "unknown":
            url = "unknown:" + url

        if whitespace_arg == "yes":
            url = "   " + url + "\t\n"

        ###########################################################
        # Execution

        if raises is not None:
            with self.assertRaises(raises):
                norm = normalise_url(url)
        else:
            norm = normalise_url(url)
            assert norm == rawUrl
