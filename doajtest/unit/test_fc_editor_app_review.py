import re
import time
from copy import deepcopy

from nose.tools import assert_raises
from werkzeug.datastructures import MultiDict

from portality import constants
from doajtest.fixtures import ApplicationFixtureFactory, AccountFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import lcc
from portality import models

from portality.forms.application_forms import ApplicationFormFactory
from portality.forms.application_processors import EditorApplication


#####################################################################
# Mocks required to make some of the lookups work
#####################################################################

@classmethod
def editor_group_pull(cls, field, value):
    eg = models.EditorGroup()
    eg.set_editor("eddie")
    eg.set_associates(["associate", "assan"])
    eg.set_name("editorgroup")
    return eg

mock_lcc_choices = [
    ('H', 'Social Sciences'),
    ('HB1-3840', '--Economic theory. Demography')
]


def mock_lookup_code(code):
    if code == "H": return "Social Sciences"
    if code == "HB1-3840": return "Economic theory. Demography"
    return None

#####################################################################
# Source objects to be used for testing
#####################################################################

APPLICATION_SOURCE = ApplicationFixtureFactory.make_update_request_source()
APPLICATION_FORM = ApplicationFixtureFactory.make_application_form(role="editor")

######################################################
# Main test class
######################################################

class TestEditorAppReview(DoajTestCase):

    def setUp(self):
        super(TestEditorAppReview, self).setUp()

        self.editor_group_pull = models.EditorGroup.pull_by_key
        models.EditorGroup.pull_by_key = editor_group_pull

        self.old_lcc_choices = lcc.lcc_choices
        lcc.lcc_choices = mock_lcc_choices

        self.old_lookup_code = lcc.lookup_code
        lcc.lookup_code = mock_lookup_code

    def tearDown(self):
        super(TestEditorAppReview, self).tearDown()

        models.EditorGroup.pull_by_key = self.editor_group_pull
        lcc.lcc_choices = self.old_lcc_choices

        lcc.lookup_code = self.old_lookup_code

    ###########################################################
    # Tests on the editor's application form
    ###########################################################

    def test_01_editor_review_success(self):
        """Give the editor's application form a full workout"""
        acc = models.Account()
        acc.set_id("richard")
        acc.add_role("editor")
        ctx = self._make_and_push_test_context(acc=acc)

        # we start by constructing it from source
        formulaic_context = ApplicationFormFactory.context("editor")
        fc = formulaic_context.processor(source=models.Application(**APPLICATION_SOURCE))
        assert isinstance(fc, EditorApplication)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is None
        #assert fc.template is not None

        # TODO: we are no longer testing the render here - should we move this?
        """
        # check that we can render the form
        # FIXME: we can't easily render the template - need to look into Flask-Testing for this
        # html = fc.render_template(edit_suggestion=True)
        html = fc.render_field_group("editorial") # we know all these disabled fields are in the editorial section
        assert html is not None
        assert html != ""

        # check that the fields that should be disabled are disabled
        # "editor_group"
        rx_template = '(<input [^>]*?disabled[^>]+?name="{field}"[^>]*?>)'
        eg_rx = rx_template.replace("{field}", "editor_group")

        assert re.search(eg_rx, html)
        """

        # now construct it from form data (with a known source)
        formulaic_context = ApplicationFormFactory.context("editor")
        fc = formulaic_context.processor(formdata=MultiDict(APPLICATION_FORM),
                                         source=models.Application(**APPLICATION_SOURCE))

        assert isinstance(fc, EditorApplication)
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
        assert fc.target.id == "abcdefghijk"
        assert len(fc.target.notes) == 2
        assert fc.target.owner == "Owner"
        assert fc.target.editor_group == "editorgroup"
        assert fc.target.editor == "associate"
        assert fc.target.application_status == constants.APPLICATION_STATUS_PENDING, fc.target.application_status # is updated by the form
        assert fc.target.bibjson().replaces == ["1111-1111"]
        assert fc.target.bibjson().is_replaced_by == ["2222-2222"]
        assert fc.target.bibjson().discontinued_date == "2001-01-01"
        assert fc.target.current_journal == "123456789987654321"
        assert fc.target.related_journal == "987654321123456789"

        # now do finalise (which will also re-run all of the steps above)
        fc.finalise()

        time.sleep(1.5)

        # now check that a provenance record was recorded
        prov = models.Provenance.get_latest_by_resource_id(fc.target.id)
        assert prov is not None

        ctx.pop()

    def test_02_classification_required(self):
        # Check we can mark an application 'ready' with a subject classification present
        in_progress_application = models.Suggestion(**ApplicationFixtureFactory.make_update_request_source())
        in_progress_application.set_application_status(constants.APPLICATION_STATUS_IN_PROGRESS)

        formulaic_context = ApplicationFormFactory.context("editor")
        fc = formulaic_context.processor(source=in_progress_application)

        # Make changes to the application status via the form, check it validates
        fc.form.application_status.data = constants.APPLICATION_STATUS_READY

        assert fc.validate()

        # Without a subject classification, we should not be able to set the status to 'ready'
        no_class_application = models.Application(**ApplicationFixtureFactory.make_update_request_source())
        del no_class_application.data['bibjson']['subject']

        formulaic_context = ApplicationFormFactory.context("editor")
        fc = formulaic_context.processor(source=no_class_application)
        # Make changes to the application status via the form
        assert fc.source.bibjson().subjects() == []
        fc.form.application_status.data = constants.APPLICATION_STATUS_READY

        assert not fc.validate()

        # TODO: this behaviour has changed to be 'required' in all statuses according to form config (remove on verify)
        # However, we should be able to set it to a different status rather than 'ready'
        # fc.form.application_status.data = constants.APPLICATION_STATUS_PENDING
        # assert fc.validate(), fc.form.errors

    def test_03_editor_review_ready(self):
        """Give the editor's application form a full workout"""
        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("editor")
        ctx = self._make_and_push_test_context(acc=acc)

        eg = models.EditorGroup()
        eg.set_name(APPLICATION_SOURCE["admin"]["editor_group"])
        eg.set_editor("contextuser")
        eg.save()

        time.sleep(1.5)

        # construct a context from a form submission
        source = deepcopy(APPLICATION_FORM)
        source["application_status"] = constants.APPLICATION_STATUS_READY
        fd = MultiDict(source)
        formulaic_context = ApplicationFormFactory.context("editor")
        fc = formulaic_context.processor(formdata=fd,
                                         source=models.Application(**APPLICATION_SOURCE))
        fc.finalise()
        time.sleep(1.5)

        # now check that a provenance record was recorded
        count = 0
        for prov in models.Provenance.iterall():
            if prov.action == "edit":
                count += 1
            if prov.action == "status:ready":
                count += 10
        assert count == 11

        ctx.pop()

    def test_04_editor_review_disallowed_statuses(self):
        """ Check that editors can't access applications beyond their review process """

        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("editor")
        ctx = self._make_and_push_test_context(acc=acc)

        # Check that an accepted application can't be regressed by an editor
        accepted_source = APPLICATION_SOURCE.copy()
        accepted_source['admin']['application_status'] = constants.APPLICATION_STATUS_ACCEPTED

        ready_form = APPLICATION_FORM.copy()
        ready_form['application_status'] = constants.APPLICATION_STATUS_READY

        # Construct the formcontext from form data (with a known source)
        formulaic_context = ApplicationFormFactory.context("editor")
        fc = formulaic_context.processor(formdata=MultiDict(ready_form),
                                         source=models.Application(**accepted_source))

        assert isinstance(fc, EditorApplication)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is not None

        # Finalise the form processor. This should raise an exception because the application has already been accepted.
        assert_raises(Exception, fc.finalise)

        # Check that an application status can't be edited by editors when on hold,
        # since this status must have been set by a managing editor.
        held_source = APPLICATION_SOURCE.copy()
        held_source['admin']['application_status'] = constants.APPLICATION_STATUS_ON_HOLD

        progressing_form = APPLICATION_FORM.copy()
        progressing_form['application_status'] = constants.APPLICATION_STATUS_IN_PROGRESS

        # Construct the formulaic context from form data (with a known source)
        formulaic_context = ApplicationFormFactory.context("editor")
        fc = formulaic_context.processor(formdata=MultiDict(progressing_form),
                                         source=models.Application(**held_source))

        assert isinstance(fc, EditorApplication)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is not None

        # Finalise the formcontext. This should raise an exception because the application status is out of bounds.
        assert_raises(Exception, fc.finalise)

        # Check that an application status can't be brought backwards in the review process
        pending_source = APPLICATION_SOURCE.copy()

        progressing_form = APPLICATION_FORM.copy()
        progressing_form['application_status'] = constants.APPLICATION_STATUS_IN_PROGRESS

        # Construct the formcontext from form data (with a known source)
        formulaic_context = ApplicationFormFactory.context("editor")
        fc = formulaic_context.processor(formdata=MultiDict(progressing_form),
                                         source=models.Application(**pending_source))

        # Finalise the formcontext. This should raise an exception because the application status can't go backwards.
        assert_raises(Exception, fc.finalise)

        ctx.pop()

    def test_05_editor_revert_to_in_progress(self):
        """ Check that editors are permitted to revert applications from 'completed' to 'in progress' """

        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("editor")
        ctx = self._make_and_push_test_context(acc=acc)

        # There should be an associate editor to receive an email when the status is changed
        associate_account = models.Account(**AccountFixtureFactory.make_assed1_source())
        associate_account.save(blocking=True)

        # Check that an editor can change from 'completed' to 'in progress' after a failed review
        completed_source = APPLICATION_SOURCE.copy()
        completed_source['admin']['application_status'] = constants.APPLICATION_STATUS_COMPLETED

        in_progress_form = APPLICATION_FORM.copy()
        in_progress_form['application_status'] = constants.APPLICATION_STATUS_IN_PROGRESS

        # Construct the formcontext from form data (with a known source)
        formulaic_context = ApplicationFormFactory.context("editor")
        fc = formulaic_context.processor(formdata=MultiDict(in_progress_form),
                                         source=models.Application(**completed_source))

        assert isinstance(fc, EditorApplication)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is not None

        # Finalise the formcontext. This should raise an exception because the application has already been accepted.
        fc.finalise()

        time.sleep(1.5)

        # now check that a provenance record was recorded
        prov = models.Provenance.get_latest_by_resource_id(fc.target.id)
        assert prov is not None

        ctx.pop()
