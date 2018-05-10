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

    def test_02_form_diff_table_subject_expand(self):
        filter = app.jinja_env.filters['form_diff_table_subject_expand']

        assert filter(None) == ""
        assert filter([]) == ""
        assert filter("whatever") == "whatever"
        assert filter("JA1-92") == "Political science (General) [code: JA1-92]"
        assert filter(["whatever", "JA1-92"]) == "whatever, Political science (General) [code: JA1-92]"
        assert filter(["JA1-92"]) == "Political science (General) [code: JA1-92]"
        assert filter(["JA1-92", "D"]) == "Political science (General) [code: JA1-92], History (General) and history of Europe [code: D]"
        assert filter(["JA1-92", None]) == "Political science (General) [code: JA1-92]"
        assert filter(["JA1-92", ""]) == "Political science (General) [code: JA1-92]"
