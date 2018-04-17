from doajtest.helpers import DoajTestCase
from portality.core import app

class TestJinjaTemplateFilters(DoajTestCase):

    def setUp(self):
        super(TestJinjaTemplateFilters, self).setUp()

    def tearDown(self):
        super(TestJinjaTemplateFilters, self).tearDown()

    def test_01_form_diff_table_comparison_value(self):
        filter = app.jinja_env.filters['form_diff_table_comparison_value']

        assert filter(None) == ""
        assert filter([]) == ""
        assert filter("whatever") == "whatever"
        assert filter("true") == "Yes"
        assert filter ("True") == "Yes"
        assert filter("TrUe") == "Yes"
        assert filter(True) == "Yes"
        assert filter("false") == "No"
        assert filter("False") == "No"
        assert filter("FaLsE") == "No"
        assert filter(False) == "No"
        assert filter([None]) == ""
        assert filter(["whatever", "next"]) == "whatever, next"
        assert filter(["true", "True", "TrUe", True]) == "Yes, Yes, Yes, Yes"
        assert filter(["false", "False", "FaLsE", False]) == "No, No, No, No"