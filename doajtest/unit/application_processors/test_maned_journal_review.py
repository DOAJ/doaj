from doajtest.helpers import DoajTestCase

from portality import models
from portality import lcc
from portality.forms.application_forms import JournalFormFactory
from portality.forms.application_processors import ManEdJournalReview

from doajtest.fixtures import JournalFixtureFactory

from copy import deepcopy

JOURNAL_SOURCE = JournalFixtureFactory.make_journal_source()
JOURNAL_FORM = JournalFixtureFactory.make_journal_form()

#####################################################################
# Mocks required to make some of the lookups work
#####################################################################

@classmethod
def editor_group_pull(cls, field, value):
    eg = models.EditorGroup()
    eg.set_editor("eddie")
    eg.set_associates(["associate", "assan"])
    eg.set_name("Test Editor Group")
    return eg

def mock_lookup_code(code):
    if code == "H": return "Social Sciences"
    if code == "HB1-3840": return "Economic theory. Demography"
    return None


class TestManEdJournalReview(DoajTestCase):

    def setUp(self):
        super(TestManEdJournalReview, self).setUp()

        self.editor_group_pull = models.EditorGroup.pull_by_key
        models.EditorGroup.pull_by_key = editor_group_pull

        self.old_lookup_code = lcc.lookup_code
        lcc.lookup_code = mock_lookup_code

    def tearDown(self):
        super(TestManEdJournalReview, self).tearDown()
        models.EditorGroup.pull_by_key = self.editor_group_pull
        lcc.lookup_code = self.old_lookup_code

    def test_01_maned_review_success(self):
        """Give the Managing Editor's journal form a full workout"""

        # we start by constructing it from source
        formulaic_context = JournalFormFactory.context("admin")
        fc = formulaic_context.processor(source=models.Journal(**JOURNAL_SOURCE))
        # fc = formcontext.JournalFormFactory.get_form_context(role="admin", source=models.Journal(**JOURNAL_SOURCE))
        assert isinstance(fc, ManEdJournalReview)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is None

        # no need to check form rendering - there are no disabled fields

        # now construct it from form data (with a known source)
        fc = formulaic_context.processor(
            formdata=JOURNAL_FORM,
            source=models.Journal(**JOURNAL_SOURCE)
        )

        assert isinstance(fc, ManEdJournalReview)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is not None

        # test each of the workflow components individually ...

        # pre-validate and ensure that the disabled fields get re-set
        fc.pre_validate()
        # no disabled fields, so just test the function runs

        # run the validation itself
        assert fc.validate(), fc.form.errors

        # run the crosswalk (no need to look in detail, xwalks are tested elsewhere)
        fc.form2target()
        assert fc.target is not None

        # patch the target with data from the source
        fc.patch_target()
        assert fc.target.created_date == "2000-01-01T00:00:00Z"
        assert fc.target.id == "abcdefghijk_journal"
        assert fc.target.current_application == "qwertyuiop"
        related = fc.target.related_applications
        assert len(related) == 2
        assert related[0].get("application_id") == "asdfghjkl"
        assert related[0].get("date_accepted") == "2018-01-01T00:00:00Z"
        assert related[1].get("application_id") == "zxcvbnm"
        assert related[1].get("date_accepted") is None
        # everything else is overridden by the form, so no need to check it has patched

        # now do finalise (which will also re-run all of the steps above)
        fc.finalise()
        assert True # gives us a place to drop a break point later if we need it

    def test_02_maned_review_optional_validation(self):
        """Test optional validation in the Managing Editor's journal form"""

        # construct it from form data (with a known source)
        formulaic_context = JournalFormFactory.context("admin")
        fc = formulaic_context.processor(
            formdata=JOURNAL_FORM,
            source=models.Journal(**JOURNAL_SOURCE)
        )

        # do not re-test the form context

        # run the validation, but make it fail by omitting a required field
        fc.form.title.data = ''
        assert not fc.validate()

        # tick the optional validation box and try again
        fc.form.make_all_fields_optional.data = True
        assert fc.validate(), fc.form.errors

        # run the crosswalk, don't test it at all in this test
        fc.form2target()

        # patch the target with data from the source
        fc.patch_target()

        # right, so let's see if we managed to get a title-less journal from this
        assert fc.target.bibjson().title is None, fc.target.bibjson().title

    def test_04_maned_review_doaj_seal(self):
        """Test the seal checkbox on the maned review form"""

        # construct it from form data (with a known source)
        formulaic_context = JournalFormFactory.context("admin")
        fc = formulaic_context.processor(
            formdata=JOURNAL_FORM,
            source=models.Journal(**JOURNAL_SOURCE)
        )

        # set the seal to False using the form
        fc.form.doaj_seal.data = False

        # run the crosswalk, don't test it at all in this test
        fc.form2target()
        # patch the target with data from the source
        fc.patch_target()

        # ensure the model has seal set to False
        assert fc.target.has_seal() is False

        # Set the seal to True in the object and check the form reflects this
        fc.source.set_seal(True)
        fc.source2form()

        assert fc.form.doaj_seal.data is True

    def test_05_maned_review_continuations(self):
        # construct it from form data (with a known source)
        formulaic_context = JournalFormFactory.context("admin")
        fc = formulaic_context.processor(
            formdata=JOURNAL_FORM,
            source=models.Journal(**JOURNAL_SOURCE)
        )

        # check the form has the continuations data
        assert fc.form.continues.data == ["1111-1111"]
        assert fc.form.continued_by.data == ["2222-2222"]
        assert fc.form.discontinued_date.data == "2001-01-01"

        # run the crosswalk, don't test it at all in this test
        fc.form2target()
        # patch the target with data from the source
        fc.patch_target()

        # ensure the model has the continuations data
        assert fc.target.bibjson().replaces == ["1111-1111"]
        assert fc.target.bibjson().is_replaced_by == ["2222-2222"]
        assert fc.target.bibjson().discontinued_date == "2001-01-01"

    def test_06_maned_review_no_continuation(self):
        source = deepcopy(JOURNAL_SOURCE)
        source["bibjson"]["replaces"] = []
        source["bibjson"]["is_replaced_by"] = []
        source["bibjson"]["discontinued_date"] = ""
        j = models.Journal(**source)
        bj = j.bibjson()    # just checking this works, as it uses an inner DataObj

        form = deepcopy(JOURNAL_FORM)
        form["continues"] = ""
        form["continued_by"] = ""
        form["discontinued_date"] = ""

        # construct it from form data (with a known source)
        formulaic_context = JournalFormFactory.context("admin")
        fc = formulaic_context.processor(
            formdata=form,
            source=j
        )

        # check the form has the continuations data
        assert fc.form.continues.data == []
        assert fc.form.continued_by.data == []
        assert fc.form.discontinued_date.data == ""

        # run the crosswalk, don't test it at all in this test
        fc.form2target()
        # patch the target with data from the source
        fc.patch_target()

        # ensure the model has the continuations data
        assert fc.target.bibjson().replaces == []
        assert fc.target.bibjson().is_replaced_by == []
        assert fc.target.bibjson().discontinued_date is None

