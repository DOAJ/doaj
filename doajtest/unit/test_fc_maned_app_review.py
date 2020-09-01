import time
from copy import deepcopy

from nose.tools import assert_raises
from werkzeug.datastructures import MultiDict

from portality import constants
from doajtest.fixtures import JournalFixtureFactory, ApplicationFixtureFactory, AccountFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import lcc
from portality import models
from portality.forms.application_forms import ApplicationFormFactory
from portality.forms.application_processors import AdminApplication


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
APPLICATION_FORM = ApplicationFixtureFactory.make_application_form(role="maned")

######################################################
# Main test class
######################################################


class TestManEdAppReview(DoajTestCase):

    def setUp(self):
        super(TestManEdAppReview, self).setUp()

        self.editor_group_pull = models.EditorGroup.pull_by_key
        models.EditorGroup.pull_by_key = editor_group_pull

        self.old_lcc_choices = lcc.lcc_choices
        lcc.lcc_choices = mock_lcc_choices

        self.old_lookup_code = lcc.lookup_code
        lcc.lookup_code = mock_lookup_code

    def tearDown(self):
        super(TestManEdAppReview, self).tearDown()

        models.EditorGroup.pull_by_key = self.editor_group_pull
        lcc.lcc_choices = self.old_lcc_choices

        lcc.lookup_code = self.old_lookup_code

    def test_01_maned_review_success(self):
        """Give the editor's application form a full workout"""
        acc = models.Account()
        acc.set_id("aga")
        acc.add_role("admin")
        ctx = self._make_and_push_test_context(acc=acc)

        # Pre-existing applications will have an owner
        owner = models.Account(**AccountFixtureFactory.make_publisher_source())
        owner.save(blocking=True)

        # we start by constructing it from source
        formulaic_context = ApplicationFormFactory.context("admin")
        fc = formulaic_context.processor(source=models.Application(**APPLICATION_SOURCE))
        assert isinstance(fc, AdminApplication)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is None

        # now construct it from form data (with a known source)
        fc = formulaic_context.processor(
            formdata=MultiDict(APPLICATION_FORM),
            source=models.Suggestion(**APPLICATION_SOURCE))

        assert isinstance(fc, AdminApplication)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is not None

        # test each of the workflow components individually ...

        # pre-validate and ensure that the disabled fields get re-set
        fc.pre_validate()
        # no disabled fields, so just test the function runs

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
        assert fc.target.current_journal == "123456789987654321"
        assert fc.target.related_journal == "987654321123456789"
        # everything else is overridden by the form, so no need to check it has patched

        # now do finalise (which will also re-run all of the steps above)
        fc.finalise(acc)

        time.sleep(2)

        # now check that a provenance record was recorded
        prov = models.Provenance.get_latest_by_resource_id(fc.target.id)
        assert prov is not None

        ctx.pop()

    def test_02_update_request(self):
        acc = models.Account()
        acc.set_id("richard")
        acc.add_role("admin")
        ctx = self._make_and_push_test_context(acc=acc)

        # Pre-existing applications will have an owner
        owner = models.Account(**AccountFixtureFactory.make_publisher_source())
        owner.save(blocking=True)

        # There needs to be an existing journal in the index for this test to work
        jsource = JournalFixtureFactory.make_journal_source()
        del jsource["admin"]["related_applications"]
        extant_j = models.Journal(**jsource)
        assert extant_j.last_update_request is None
        extant_j_created_date = extant_j.created_date
        extant_j.save()
        time.sleep(1)

        # We've added one journal, so there'll be one snapshot already
        assert models.Journal.count() == 1
        h = self.list_today_journal_history_files()
        assert len(h) == 1

        # set up an application which is an update on an existing journal
        s = models.Application(**APPLICATION_SOURCE)
        s.set_current_journal(extant_j.id)
        s.set_application_status(constants.APPLICATION_STATUS_UPDATE_REQUEST)

        # set up the form which "accepts" this update request
        fd = deepcopy(APPLICATION_FORM)
        fd["application_status"] = constants.APPLICATION_STATUS_ACCEPTED
        fd = MultiDict(fd)

        # create and finalise the form context
        formulaic_context = ApplicationFormFactory.context("admin")
        fc = formulaic_context.processor(source=s, formdata=fd)

        # with app.test_request_context():
        fc.finalise(acc)

        # let the index catch up
        time.sleep(1)

        j = models.Journal.pull(extant_j.id)
        assert j is not None
        assert j.created_date == extant_j_created_date
        assert j.last_update_request is not None
        assert models.Journal.count() == 1

        h = self.list_today_journal_history_files()
        assert h is not None
        assert len(h) == 2

        ctx.pop()

    def test_03_classification_required(self):
        acc = models.Account()
        acc.set_id("steve")
        acc.add_role("admin")
        ctx = self._make_and_push_test_context(acc=acc)

        # Check we can accept an application with a subject classification present
        ready_application = models.Application(**ApplicationFixtureFactory.make_application_source())
        ready_application.set_application_status(constants.APPLICATION_STATUS_READY)

        formulaic_context = ApplicationFormFactory.context("admin")
        fc = formulaic_context.processor(source=ready_application)

        # Make changes to the application status via the form, check it validates
        fc.form.application_status.data = constants.APPLICATION_STATUS_ACCEPTED

        assert fc.validate(), fc.form.errors

        # Without a subject classification, we should not be able to set the status to 'accepted'
        no_class_application = models.Suggestion(**ApplicationFixtureFactory.make_application_source())
        del no_class_application.data['bibjson']['subject']

        formulaic_context = ApplicationFormFactory.context("admin")
        fc = formulaic_context.processor(source=no_class_application)
        # Make changes to the application status via the form
        assert fc.source.bibjson().subjects() == []
        fc.form.application_status.data = constants.APPLICATION_STATUS_ACCEPTED

        assert not fc.validate()

        # TODO: this behaviour has changed to be 'required' in all statuses according to form config (remove on verify)
        # However, we should be able to set it to a different status rather than 'accepted'
        #fc.form.application_status.data = constants.APPLICATION_STATUS_IN_PROGRESS
        #assert fc.validate(), fc.form.errors

        ctx.pop()

    def test_04_maned_review_continuations(self):
        acc = models.Account()
        acc.set_id("steve")
        acc.add_role("admin")
        ctx = self._make_and_push_test_context(acc=acc)

        # construct it from form data (with a known source)
        formulaic_context = ApplicationFormFactory.context("admin")
        fc = formulaic_context.processor(
            source=models.Application(**ApplicationFixtureFactory.make_application_source()),
            formdata=MultiDict(APPLICATION_FORM)
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

    def test_05_maned_review_accept(self):
        """Give the editor's application form a full workout"""
        acc = models.Account()
        acc.set_id("richard")
        acc.add_role("admin")
        ctx = self._make_and_push_test_context(acc=acc)

        # Pre-existing applications will have an owner
        owner = models.Account(**AccountFixtureFactory.make_publisher_source())
        owner.save(blocking=True)

        # construct a context from a form submission
        source = deepcopy(APPLICATION_FORM)
        source["application_status"] = constants.APPLICATION_STATUS_ACCEPTED
        fd = MultiDict(source)

        formulaic_context = ApplicationFormFactory.context("admin")
        fc = formulaic_context.processor(
            source=models.Application(**APPLICATION_SOURCE),
            formdata=fd
        )

        fc.finalise(acc)
        time.sleep(2)

        # now check that a provenance record was recorded
        count = 0
        for prov in models.Provenance.iterall():
            if prov.action == "edit":
                count += 1
            if prov.action == "status:accepted":
                count += 10
        assert count == 11

        ctx.pop()

    def test_06_maned_review_reject(self):
        """Give the editor's application form a full workout"""
        acc = models.Account()
        acc.set_id("richard")
        acc.add_role("admin")
        ctx = self._make_and_push_test_context(acc=acc)

        # Pre-existing applications will have an owner
        owner = models.Account(**AccountFixtureFactory.make_publisher_source())
        owner.save(blocking=True)

        # construct a context from a form submission
        form_source = deepcopy(APPLICATION_FORM)
        form_source["application_status"] = constants.APPLICATION_STATUS_REJECTED
        fd = MultiDict(form_source)
        formulaic_context = ApplicationFormFactory.context("admin")
        fc = formulaic_context.processor(
            source=models.Application(**APPLICATION_SOURCE),
            formdata=fd
        )

        fc.finalise(acc)
        time.sleep(2)

        # now check that a provenance record was recorded
        count = 0
        for prov in models.Provenance.iterall():
            if prov.action == "edit":
                count += 1
            if prov.action == "status:rejected":
                count += 10
        assert count == 11

        assert len(fc.alert) == 1

        ctx.pop()

    def test_07_disallowed_statuses(self):
        """ Check that managing editors can access applications in any status """

        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("admin")
        ctx = self._make_and_push_test_context(acc=acc)

        # Pre-existing applications will have an owner
        owner = models.Account(**AccountFixtureFactory.make_publisher_source())
        owner.save(blocking=True)

        # Check that an accepted application can't be regressed by a managing editor
        accepted_source = APPLICATION_SOURCE.copy()
        accepted_source['admin']['application_status'] = constants.APPLICATION_STATUS_ACCEPTED

        completed_form = APPLICATION_FORM.copy()
        completed_form['application_status'] = constants.APPLICATION_STATUS_COMPLETED

        # Construct the formcontext from form data (with a known source)
        formulaic_context = ApplicationFormFactory.context("admin")
        fc = formulaic_context.processor(
            source=models.Application(**accepted_source),
            formdata=MultiDict(completed_form)
        )

        assert isinstance(fc, AdminApplication)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is not None

        # Finalise the formcontext. This should raise an exception because the application has already been accepted.
        assert_raises(Exception, fc.finalise)

        # Check that an application status can when on hold.
        held_source = APPLICATION_SOURCE.copy()
        held_source['admin']['application_status'] = constants.APPLICATION_STATUS_ON_HOLD

        progressing_form = APPLICATION_FORM.copy()
        progressing_form['application_status'] = constants.APPLICATION_STATUS_IN_PROGRESS

        # Construct the formcontext from form data (with a known source)
        formulaic_context = ApplicationFormFactory.context("admin")
        fc = formulaic_context.processor(
            source=models.Application(**held_source),
            formdata=MultiDict(progressing_form)
        )

        assert isinstance(fc, AdminApplication)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is not None

        # Finalise the formcontext. This should not raise an exception.
        fc.finalise(acc)

        # Check that an application status can be brought backwards in the review process
        pending_source = APPLICATION_SOURCE.copy()

        progressing_form = APPLICATION_FORM.copy()
        progressing_form['application_status'] = constants.APPLICATION_STATUS_IN_PROGRESS

        # Construct the formcontext from form data (with a known source)
        formulaic_context = ApplicationFormFactory.context("admin")
        fc = formulaic_context.processor(
            source=models.Application(**pending_source),
            formdata=MultiDict(progressing_form)
        )

        # Finalise the formcontext. This should not raise an exception.
        fc.finalise(acc)

        ctx.pop()
