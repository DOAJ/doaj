from doajtest.helpers import DoajTestCase
from portality.core import app

class TestJinjaTemplateFilters(DoajTestCase):

    def setUp(self):
        super(TestJinjaTemplateFilters, self).setUp()

    def tearDown(self):
        super(TestJinjaTemplateFilters, self).tearDown()

    def test_01_form_diff_table_comparison_value(self):
        filter = app.jinja_env.filters['form_diff_table_comparison_value']

        assert list(filter(None)) == ""
        assert list(filter([])) == ""
        assert list(filter("whatever")) == "whatever"
        assert list(filter("true")) == "Yes"
        assert list(filter ("True")) == "Yes"
        assert list(filter("TrUe")) == "Yes"
        assert list(filter(True)) == "Yes"
        assert list(filter("false")) == "No"
        assert list(filter("False")) == "No"
        assert list(filter("FaLsE")) == "No"
        assert list(filter(False)) == "No"
        assert list(filter([None])) == ""
        assert list(filter(["whatever", "next"])) == "whatever, next"
        assert list(filter(["true", "True", "TrUe", True])) == "Yes, Yes, Yes, Yes"
        assert list(filter(["false", "False", "FaLsE", False])) == "No, No, No, No"

    def test_02_form_diff_table_subject_expand(self):
        filter = app.jinja_env.filters['form_diff_table_subject_expand']

        assert list(filter(None)) == ""
        assert list(filter([])) == ""
        assert list(filter("whatever")) == "whatever"
        assert list(filter("JA1-92")) == "Political science (General) [code: JA1-92]"
        assert list(filter(["whatever", "JA1-92"])) == "whatever, Political science (General) [code: JA1-92]"
        assert list(filter(["JA1-92"])) == "Political science (General) [code: JA1-92]"
        assert list(filter(["JA1-92", "D"])) == "Political science (General) [code: JA1-92], History (General) and history of Europe [code: D]"
        assert list(filter(["JA1-92", None])) == "Political science (General) [code: JA1-92]"
        assert list(filter(["JA1-92", ""])) == "Political science (General) [code: JA1-92]"
