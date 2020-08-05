from nose.tools import assert_raises
from doajtest.helpers import DoajTestCase

from portality import models
from portality.formcontext import formcontext
from portality import lcc

from werkzeug.datastructures import MultiDict

from doajtest.fixtures import JournalFixtureFactory

#####################################################################
# Mocks required to make some of the lookups work
#####################################################################
mock_lcc_choices = [
    ('H', 'Social Sciences'),
    ('HB1-3840', '--Economic theory. Demography')
]

def mock_lookup_code(code):
    if code == "H": return "Social Sciences"
    if code == "HB1-3840": return "Economic theory. Demography"
    return None

JOURNAL_SOURCE = JournalFixtureFactory.make_journal_source()
JOURNAL_FORM = JournalFixtureFactory.make_journal_form()
del JOURNAL_FORM["owner"]
del JOURNAL_FORM["editor_group"]
del JOURNAL_FORM["editor"]

######################################################
# Main test class
######################################################

class TestReadOnlyJournal(DoajTestCase):

    def setUp(self):
        super(TestReadOnlyJournal, self).setUp()

        self.old_lcc_choices = lcc.lcc_choices
        lcc.lcc_choices = mock_lcc_choices

        self.old_lookup_code = lcc.lookup_code
        lcc.lookup_code = mock_lookup_code

    def tearDown(self):
        super(TestReadOnlyJournal, self).tearDown()

        lcc.lcc_choices = self.old_lcc_choices

        lcc.lookup_code = self.old_lookup_code


    ###########################################################
    # Tests on the publisher's re-journal form
    ###########################################################

    def test_01_readonly_journal_success(self):
        """Give the read-only journal form a full workout"""

        # we start by constructing it from source
        fc = formcontext.JournalFormFactory.get_form_context(role="readonly", source=models.Journal(**JOURNAL_SOURCE))
        assert isinstance(fc, formcontext.ReadOnlyJournal)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is None
        assert fc.template is not None

        # check that we can render the form
        # FIXME: we can't easily render the template - need to look into Flask-Testing for this
        # html = fc.render_template(edit_journal=True)
        html = fc.render_field_group("editorial")  # these fields should not appear at all
        assert html == ""

        html = fc.render_field_group("owner")  # these fields should not appear at all
        assert html == ""

        # now construct it from form data (with a known source)
        journal_obj = models.Journal(**JOURNAL_SOURCE)
        journal_bibjson_obj = journal_obj.bibjson()
        fc = formcontext.JournalFormFactory.get_form_context(
            role="readonly",
            form_data=MultiDict(JOURNAL_FORM),
            source=journal_obj
        )

        assert isinstance(fc, formcontext.ReadOnlyJournal)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is not None

        # see that form has the correct info from an object (after all, that's the only point of having the form)
        assert fc.form.title.data == journal_bibjson_obj.title
        assert fc.form.pissn.data == journal_bibjson_obj.get_one_identifier(idtype=journal_bibjson_obj.P_ISSN)
        assert fc.form.eissn.data == journal_bibjson_obj.get_one_identifier(idtype=journal_bibjson_obj.E_ISSN)

        # test each of the workflow components individually ...

        # run the validation
        fc.form.subject.choices = mock_lcc_choices # set the choices allowed for the subject manually (part of the test)
        assert fc.validate(), fc.form.errors

        # run the crosswalk (no need to look in detail, xwalks are tested elsewhere)
        fc.form2target()
        assert fc.target is None  # can't edit data using this form

        # patch the target with data from the source
        fc.patch_target()
        assert fc.target is None  # can't edit data using this form

        # shouldn't be able to finalise, can't edit data using this form
        assert_raises(formcontext.FormContextException, fc.finalise)