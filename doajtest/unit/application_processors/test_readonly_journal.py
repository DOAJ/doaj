from doajtest.helpers import DoajTestCase

from portality import models
from portality.forms.application_forms import JournalFormFactory
from portality.forms.application_processors import ReadOnlyJournal
from portality import lcc

from doajtest.fixtures import JournalFixtureFactory


#####################################################################
# Mocks required to make some of the lookups work
#####################################################################
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

        self.old_lookup_code = lcc.lookup_code
        lcc.lookup_code = mock_lookup_code

    def tearDown(self):
        super(TestReadOnlyJournal, self).tearDown()
        lcc.lookup_code = self.old_lookup_code

    def test_01_unknown_context(self):
        """ Pulling the wrong context gives an exception """

        with self.assertRaises(AttributeError):
            formulaic_context = JournalFormFactory.context("readonly")
            fc = formulaic_context.processor(source=models.Journal(**JOURNAL_SOURCE))

    def test_02_editor_readonly_journal(self):
        """ Tests on the editor's read-only journal form """

        # we start by constructing it from source
        formulaic_context = JournalFormFactory.context("editor_readonly")
        fc = formulaic_context.processor(source=models.Journal(**JOURNAL_SOURCE))
        assert isinstance(fc, ReadOnlyJournal)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is None

        # now construct it from form data (with a known source)
        journal_obj = models.Journal(**JOURNAL_SOURCE)
        journal_bibjson_obj = journal_obj.bibjson()
        fc = formulaic_context.processor(
            formdata=JOURNAL_FORM,
            source=journal_obj
        )

        assert isinstance(fc, ReadOnlyJournal)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is not None

        # see that form has the correct info from an object (after all, that's the only point of having the form)
        assert fc.form.title.data == journal_bibjson_obj.title
        assert fc.form.pissn.data == journal_bibjson_obj.pissn
        assert fc.form.eissn.data == journal_bibjson_obj.eissn

        # test each of the workflow components individually ...

        # run the validation
        assert fc.validate(), fc.form.errors

        # run the crosswalk (no need to look in detail, xwalks are tested elsewhere)
        fc.form2target()
        assert fc.target is None  # can't edit data using this form

        # patch the target with data from the source
        fc.patch_target()
        assert fc.target is None  # can't edit data using this form

        # shouldn't be able to finalise, can't edit data using this form
        self.assertRaises(Exception, fc.finalise)

    def test_03_maned_readonly_journal(self):
        """ Tests on the managing editor's read-only journal form """

        # we start by constructing it from source
        formulaic_context = JournalFormFactory.context("admin_readonly")
        fc = formulaic_context.processor(source=models.Journal(**JOURNAL_SOURCE))
        assert isinstance(fc, ReadOnlyJournal)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is None

        # now construct it from form data (with a known source)
        journal_obj = models.Journal(**JOURNAL_SOURCE)
        journal_bibjson_obj = journal_obj.bibjson()
        fc = formulaic_context.processor(
            formdata=JOURNAL_FORM,
            source=journal_obj
        )

        assert isinstance(fc, ReadOnlyJournal)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is not None

        # see that form has the correct info from an object (after all, that's the only point of having the form)
        assert fc.form.title.data == journal_bibjson_obj.title
        assert fc.form.pissn.data == journal_bibjson_obj.pissn
        assert fc.form.eissn.data == journal_bibjson_obj.eissn

        # test each of the workflow components individually ...

        # run the validation
        assert fc.validate(), fc.form.errors

        # run the crosswalk (no need to look in detail, xwalks are tested elsewhere)
        fc.form2target()
        assert fc.target is None  # can't edit data using this form

        # patch the target with data from the source
        fc.patch_target()
        assert fc.target is None  # can't edit data using this form

        # shouldn't be able to finalise, can't edit data using this form
        self.assertRaises(Exception, fc.finalise)
