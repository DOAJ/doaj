import time
from copy import deepcopy

from werkzeug.datastructures import MultiDict

from portality import constants
from doajtest.fixtures import ApplicationFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import lcc
from portality import models

from portality.forms.application_forms import ApplicationFormFactory
from portality.forms.application_processors import AssociateApplication


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
    ('HB1-3840', '--Economic theory. Demography'),
    ('SF600-1100', 'Veterinary medicine')
]


def mock_lookup_code(code):
    if code == "H": return "Social Sciences"
    if code == "HB1-3840": return "Economic theory. Demography"
    if code == "SF600-1100": return 'Veterinary medicine'
    return None


APPLICATION_SOURCE = ApplicationFixtureFactory.make_update_request_source()
APPLICATION_FORM = ApplicationFixtureFactory.make_application_form(role="assed")

######################################################
# Main test class
######################################################        data = data.decode("utf-8")


class TestAssedAppReview(DoajTestCase):

    def setUp(self):
        super(TestAssedAppReview, self).setUp()

        self.editor_group_pull = models.EditorGroup.pull_by_key
        models.EditorGroup.pull_by_key = editor_group_pull

        self.old_lcc_choices = lcc.lcc_choices
        lcc.lcc_choices = mock_lcc_choices

        self.old_lookup_code = lcc.lookup_code
        lcc.lookup_code = mock_lookup_code

    def tearDown(self):
        super(TestAssedAppReview, self).tearDown()

        models.EditorGroup.pull_by_key = self.editor_group_pull
        lcc.lcc_choices = self.old_lcc_choices

        lcc.lookup_code = self.old_lookup_code


    ###########################################################
    # Tests on the associate editor's application form
    ###########################################################
    def test_01_editor_review_success(self):
        """Give the associate editor's application form a full workout"""
        acc = models.Account()
        acc.set_id("richard")
        acc.add_role("associate_editor")
        ctx = self._make_and_push_test_context(acc=acc)

        # we start by constructing it from source
        formulaic_context = ApplicationFormFactory.context("associate_editor")
        fc = formulaic_context.processor(source=models.Application(**APPLICATION_SOURCE))

        assert isinstance(fc, AssociateApplication)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is None
        #assert fc.template is not None

        # TODO: we are no longer testing the render here - should we move this?
        """
        # check that we can render the form
        # FIXME: we can't easily render the template - need to look into Flask-Testing for this
        # html = fc.render_template(edit_suggestion=True)
        html = fc.render_field_group("status")
        assert html is not None
        assert html != ""
        """

        # now construct it from form data (with a known source)
        formulaic_context = ApplicationFormFactory.context("associate_editor")
        fc = formulaic_context.processor(source=models.Application(**APPLICATION_SOURCE),
                                         formdata=MultiDict(APPLICATION_FORM))

        assert isinstance(fc, AssociateApplication)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is not None

        # test each of the workflow components individually ...

        # pre-validate and check this doesn't cause errors
        fc.pre_validate()

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
        assert fc.target.owner == "publisher"
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

        time.sleep(2)

        # now check that a provenance record was recorded
        prov = models.Provenance.get_latest_by_resource_id(fc.target.id)
        assert prov is not None

        ctx.pop()

    def test_02_classification_required(self):
        # Check we can mark an application 'completed' with a subject classification present
        in_progress_application = models.Suggestion(**ApplicationFixtureFactory.make_update_request_source())
        in_progress_application.set_application_status(constants.APPLICATION_STATUS_IN_PROGRESS)

        formulaic_context = ApplicationFormFactory.context("associate_editor")
        fc = formulaic_context.processor(source=in_progress_application)

        # Make changes to the application status via the form, check it validates
        fc.form.application_status.data = constants.APPLICATION_STATUS_COMPLETED

        assert fc.validate()

        # Without a subject classification, we should not be able to set the status to 'completed'
        no_class_application = models.Suggestion(**ApplicationFixtureFactory.make_update_request_source())
        del no_class_application.data['bibjson']['subject']

        formulaic_context = ApplicationFormFactory.context("associate_editor")
        fc = formulaic_context.processor(source=no_class_application)
        # Make changes to the application status via the form
        assert fc.source.bibjson().subjects() == []
        fc.form.application_status.data = constants.APPLICATION_STATUS_COMPLETED

        assert not fc.validate()

        # TODO: this behaviour has changed to be 'required' in all statuses according to form config (remove on verify)
        # However, we should be able to set it to a different status rather than 'completed'
        # fc.form.application_status.data = constants.APPLICATION_STATUS_PENDING
        # assert fc.validate()

    def test_03_associate_review_complete(self):
        """Give the editor's application form a full workout"""
        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("associate_editor")
        ctx = self._make_and_push_test_context(acc=acc)

        editor = models.Account()
        editor.set_id("editor")
        editor.set_email("email@example.com")
        editor.save()

        eg = models.EditorGroup()
        eg.set_name(APPLICATION_SOURCE["admin"]["editor_group"])
        eg.set_editor("editor")
        eg.add_associate("contextuser")
        eg.save()

        time.sleep(2)

        # construct a context from a form submission
        source = deepcopy(APPLICATION_FORM)
        source["application_status"] = constants.APPLICATION_STATUS_COMPLETED
        fd = MultiDict(source)

        formulaic_context = ApplicationFormFactory.context("associate_editor")
        fc = formulaic_context.processor(source=models.Application(**APPLICATION_SOURCE), formdata=fd)

        fc.finalise()
        time.sleep(2)

        # now check that a provenance record was recorded
        count = 0
        for prov in models.Provenance.iterall():
            if prov.action == "edit":
                count += 1
            if prov.action == "status:completed":
                count += 10
        assert count == 11

        ctx.pop()

    def test_04_associate_review_disallowed_statuses(self):
        """ Check that associate editors can't access applications beyond their review process """

        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("associate_editor")
        ctx = self._make_and_push_test_context(acc=acc)

        # Check that an accepted application can't be regressed by an associate editor
        accepted_source = APPLICATION_SOURCE.copy()
        accepted_source['admin']['application_status'] = constants.APPLICATION_STATUS_ACCEPTED

        completed_form = APPLICATION_FORM.copy()
        completed_form['application_status'] = constants.APPLICATION_STATUS_COMPLETED

        # Construct the formcontext from form data (with a known source)
        formulaic_context = ApplicationFormFactory.context("associate_editor")
        fc = formulaic_context.processor(source=models.Application(**accepted_source),
                                         formdata=MultiDict(completed_form))

        assert isinstance(fc, AssociateApplication)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is not None

        # Finalise the formcontext. This should raise an exception because the application has already been accepted.
        self.assertRaises(Exception, fc.finalise)

        # Check that an application status can't be edited by associates when on hold,
        # since this status must have been set by a managing editor.
        held_source = APPLICATION_SOURCE.copy()
        held_source['admin']['application_status'] = constants.APPLICATION_STATUS_ON_HOLD

        progressing_form = APPLICATION_FORM.copy()
        progressing_form['application_status'] = constants.APPLICATION_STATUS_IN_PROGRESS

        # Construct the formcontext from form data (with a known source)
        formulaic_context = ApplicationFormFactory.context("associate_editor")
        fc = formulaic_context.processor(source=models.Application(**held_source), formdata=MultiDict(progressing_form))

        assert isinstance(fc, AssociateApplication)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is not None

        # Finalise the formcontext. This should raise an exception because the application status is out of bounds.
        self.assertRaises(Exception, fc.finalise)

        # Check that an application status can't be brought backwards in the review process
        pending_source = APPLICATION_SOURCE.copy()

        progressing_form = APPLICATION_FORM.copy()
        progressing_form['application_status'] = constants.APPLICATION_STATUS_IN_PROGRESS

        # Construct the formcontext from form data (with a known source)
        formulaic_context = ApplicationFormFactory.context("associate_editor")
        fc = formulaic_context.processor(source=models.Application(**pending_source),
                                         formdata=MultiDict(progressing_form))

        # Finalise the formcontext. This should raise an exception because the application status can't go backwards.
        self.assertRaises(Exception, fc.finalise)

        ctx.pop()
