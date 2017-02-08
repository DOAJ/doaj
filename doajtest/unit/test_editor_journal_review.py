from doajtest.helpers import DoajTestCase

import re

from portality import models
from portality.formcontext import formcontext
from portality import lcc

from werkzeug.datastructures import MultiDict

from doajtest.fixtures import JournalFixtureFactory

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

mock_lcc_choices = [
    (u'H', u'Social Sciences'),
    (u'HB1-3840', u'--Economic theory. Demography')
]

def mock_lookup_code(code):
    if code == "H": return "Social Sciences"
    if code == "HB1-3840": return "Economic theory. Demography"
    return None

JOURNAL_SOURCE = JournalFixtureFactory.make_journal_source()
JOURNAL_FORM = JournalFixtureFactory.make_journal_form()
del JOURNAL_FORM["editor_group"]
del JOURNAL_FORM["owner"]

######################################################
# Main test class
######################################################

class TestEditorJournalReview(DoajTestCase):

    def setUp(self):
        super(TestEditorJournalReview, self).setUp()

        self.editor_group_pull = models.EditorGroup.pull_by_key
        models.EditorGroup.pull_by_key = editor_group_pull

        self.old_lcc_choices = lcc.lcc_choices
        lcc.lcc_choices = mock_lcc_choices

        self.old_lookup_code = lcc.lookup_code
        lcc.lookup_code = mock_lookup_code

    def tearDown(self):
        super(TestEditorJournalReview, self).tearDown()

        models.EditorGroup.pull_by_key = self.editor_group_pull
        lcc.lcc_choices = self.old_lcc_choices

        lcc.lookup_code = self.old_lookup_code


    ###########################################################
    # Tests on the publisher's re-journal form
    ###########################################################

    def test_01_editor_review_success(self):
        """Give the editor's journal form a full workout"""

        # we start by constructing it from source
        fc = formcontext.JournalFormFactory.get_form_context(role="editor", source=models.Journal(**JOURNAL_SOURCE))
        assert isinstance(fc, formcontext.EditorJournalReview)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is None
        assert fc.template is not None

        # check that we can render the form
        # FIXME: we can't easily render the template - need to look into Flask-Testing for this
        # html = fc.render_template(edit_journal=True)
        html = fc.render_field_group("editorial") # we know all these disabled fields are in the editorial section
        assert html is not None
        assert html != ""

        # check that the fields that should be disabled are disabled
        # "editor_group"
        rx_template = '(<input [^>]*?disabled[^>]+?name="{field}"[^>]*?>)'
        eg_rx = rx_template.replace("{field}", "editor_group")

        assert re.search(eg_rx, html)

        # now construct it from form data (with a known source)
        fc = formcontext.JournalFormFactory.get_form_context(
            role="editor",
            form_data=MultiDict(JOURNAL_FORM) ,
            source=models.Journal(**JOURNAL_SOURCE)
        )

        assert isinstance(fc, formcontext.EditorJournalReview)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is not None

        # test each of the workflow components individually ...

        # pre-validate and ensure that the disabled fields get re-set
        fc.pre_validate()
        assert fc.form.editor_group.data == "editorgroup"

        # run the validation itself
        fc.form.subject.choices = mock_lcc_choices # set the choices allowed for the subject manually (part of the test)
        assert fc.validate(), fc.form.errors

        # run the crosswalk (no need to look in detail, xwalks are tested elsewhere)
        fc.form2target()
        assert fc.target is not None

        # patch the target with data from the source
        fc.patch_target()
        assert fc.target.created_date == "2000-01-01T00:00:00Z"
        assert fc.target.id == "abcdefghijk_journal"
        assert len(fc.target.notes()) == 2
        assert fc.target.owner == "Owner"
        assert fc.target.editor_group == "editorgroup"
        assert fc.target.editor == "associate"
        assert fc.target.bibjson().replaces == ["1111-1111"]
        assert fc.target.bibjson().is_replaced_by == ["2222-2222"]
        assert fc.target.bibjson().discontinued_date == "2001-01-01"

        # now do finalise (which will also re-run all of the steps above)
        fc.finalise()
        assert True # gives us a place to drop a break point later if we need it