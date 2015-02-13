from doajtest.helpers import DoajTestCase
from portality.formcontext import render, formcontext
from wtforms import Form, StringField, SelectMultipleField, widgets

################################################################
# Form context for basic test
################################################################

class TestForm(Form):
    one = StringField("One")
    two = StringField("Two")

class TestRenderer(render.Renderer):
    def __init__(self):
        super(TestRenderer, self).__init__()
        self.FIELD_GROUPS = {
            "test" : [
                {"one" : {"class" : "first"}},
                {"two" : {"class" : "second"}}
            ]
        }

class TestContext(formcontext.FormContext):
    def data2form(self):
        self.form = TestForm(formdata=self.form_data)

    def source2form(self):
        self.form = TestForm(data=self.source)

    def blank_form(self):
        self.form = TestForm()

    def make_renderer(self):
        self.renderer = TestRenderer()

    def set_template(self):
        self.template = "test_template.html"

################################################################
# Form context for extra fields test
################################################################

class ExtraFieldsForm(Form):
    one = StringField("One")
    two = StringField("Two")
    extra = SelectMultipleField('Extra', choices = [("alpha", "alpha"), ("beta", "beta")],
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False)
    )

class ExtraFieldsRenderer(render.Renderer):
    def __init__(self):
        super(ExtraFieldsRenderer, self).__init__()
        self.FIELD_GROUPS = {
            "test" : [
                {
                    "extra" : {
                        "extra_input_fields" : {
                            "alpha" : "one",
                            "beta" : "two"
                        }
                    }
                }
            ]
        }

class ExtraFieldsContext(formcontext.FormContext):
    def data2form(self):
        self.form = ExtraFieldsForm(formdata=self.form_data)

    def source2form(self):
        self.form = ExtraFieldsForm(data=self.source)

    def blank_form(self):
        self.form = ExtraFieldsForm()

    def make_renderer(self):
        self.renderer = ExtraFieldsRenderer()

    def set_template(self):
        self.template = "test_template.html"


class TestRender(DoajTestCase):
    def setUp(self): pass
    def tearDown(self): pass

    def test_01_base_render_init(self):
        r = render.Renderer()
        assert len(r.disabled_fields) == 0
        assert len(r.error_fields) == 0

        r.set_error_fields(["one", "two"])
        r.set_disabled_fields(["three", "four"])

        assert len(r.error_fields) == 2
        assert "one" in r.error_fields
        assert "two" in r.error_fields

        assert len(r.disabled_fields) == 2
        assert "three" in r.disabled_fields
        assert "four" in r.disabled_fields

    def test_02_subclass_render_field_group(self):
        r = TestRenderer()
        fc = TestContext()
        assert "test" in r.FIELD_GROUPS

        html = r.render_field_group(fc, "test")

        assert 'name="one"' in html
        assert 'name="two"' in html
        assert 'class="first"' in html
        assert 'class="second"' in html
        assert "disabled" not in html

        r.set_disabled_fields(["two"])
        html = r.render_field_group(fc, "test")
        assert "disabled" in html

    def test_03_subclass_extra_fields(self):
        r = ExtraFieldsRenderer()
        fc = ExtraFieldsContext()

        # first test the extra fields stuff directly
        rewritten = r._rewrite_extra_fields(fc, r.FIELD_GROUPS.get("test")[0].get("extra"))
        alpha = rewritten.get("extra_input_fields").get("alpha")
        beta = rewritten.get("extra_input_fields").get("beta")

        assert isinstance(alpha, StringField)
        assert alpha.short_name == "one"
        assert isinstance(beta, StringField)
        assert beta.short_name == "two"

        # now test it indirectly through the render function
        html = r.render_field_group(fc, "test")
        assert 'name="one"' in html
        assert 'name="two"' in html

    def test_04_application_renderer(self):
        r = render.ApplicationRenderer()
        assert len(r.disabled_fields) == 0
        assert len(r.error_fields) == 0
        assert len(r.NUMBERING_ORDER) == 6
        assert len(r.NUMBERING_ORDER) == len(r.ERROR_CHECK_ORDER)
        assert len(r.FIELD_GROUPS.keys()) == 6

        # number the questions
        r.number_questions()

        # check the numbering is what we'd expect it to be
        q = 1
        for g in r.NUMBERING_ORDER:
            cfg = r.FIELD_GROUPS.get(g)
            for obj in cfg:
                field = obj.keys()[0]
                assert obj[field].get("q_num") == str(q), (field, obj[field].get("q_num"), q)
                q += 1
        assert q == 59, q # checks that we checked everything (58 questions, plus an extra 1 from the end of the loop)

        # try setting some error fields
        r.set_error_fields(["publisher", "copyright_url"])
        assert "publisher" in r.error_fields
        assert "copyright_url" in r.error_fields
        assert len(r.error_fields) == 2

        # go and look for the first error (we'd expect it to be "publisher")
        q = 1
        for g in r.ERROR_CHECK_ORDER:
            cfg = r.FIELD_GROUPS.get(g)
            for obj in cfg:
                field = obj.keys()[0]
                if field == "publisher":
                    assert obj[field].get("first_error", False)
                else:
                    assert not obj[field].get("first_error", False)
                q += 1
        assert q == 59 # makes sure we've checked all the fields (58 questions, plus an extra 1 from the end of the loop)

    def test_05_insert_fields(self):
        r = TestRenderer()
        r.insert_field_after(
            field_to_insert={"inserted_in_middle": {}},
            after_this_field='one',
            field_group='test'
        )
        r.insert_field_after(
            field_to_insert={"inserted_last": {}},
            after_this_field='two',
            field_group='test'
        )
        assert len(r.FIELD_GROUPS['test']) == 4
        assert r.FIELD_GROUPS['test'][0].keys()[0] == 'one'
        assert r.FIELD_GROUPS['test'][1].keys()[0] == 'inserted_in_middle'
        assert r.FIELD_GROUPS['test'][2].keys()[0] == 'two'
        assert r.FIELD_GROUPS['test'][3].keys()[0] == 'inserted_last'