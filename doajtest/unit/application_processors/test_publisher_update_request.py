import time
from copy import deepcopy

from portality import constants
from doajtest.fixtures import JournalFixtureFactory, ApplicationFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models

from portality.forms.application_forms import ApplicationFormFactory
from portality.forms.application_processors import PublisherUpdateRequest

#####################################################################
# Source objects to be used for testing
#####################################################################

UPDATE_REQUEST_SOURCE = ApplicationFixtureFactory.make_update_request_source()
UPDATE_REQUEST_SOURCE["admin"]["application_status"] = constants.APPLICATION_STATUS_UPDATE_REQUEST
UPDATE_REQUEST_FORM = ApplicationFixtureFactory.make_application_form(role="publisher")

######################################################
# Main test class
######################################################

class TestPublisherUpdateRequestFormContext(DoajTestCase):

    def setUp(self):
        super(TestPublisherUpdateRequestFormContext, self).setUp()

    def tearDown(self):
        super(TestPublisherUpdateRequestFormContext, self).tearDown()


    ###########################################################
    # Tests on the publisher's update request form
    ###########################################################

    def test_01_publisher_update_request_success(self):
        """Give the publisher update request a full workout"""
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_id("123456789987654321")
        journal.save(blocking=True)

        # we start by constructing it from source
        formulaic_context = ApplicationFormFactory.context("update_request")
        fc = formulaic_context.processor(source=models.Application(**UPDATE_REQUEST_SOURCE))
        # fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", source=models.Suggestion(**UPDATE_REQUEST_SOURCE))
        assert isinstance(fc, PublisherUpdateRequest)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is None

        # now construct it from form data (with a known source)
        source = models.Application(**UPDATE_REQUEST_SOURCE)
        acc = models.Account()
        acc.set_id(source.owner)
        acc.set_name("Test Owner")
        acc.set_email("test@example.com")
        acc.save(blocking=True)
        fc =formulaic_context.processor(
            formdata=UPDATE_REQUEST_FORM,
            source=source)

        assert isinstance(fc, PublisherUpdateRequest)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is not None

        # test each of the workflow components individually ...

        # pre-validate and ensure that the disbaled fields get re-set
        fc.pre_validate()
        assert fc.form.pissn.data == "1234-5678"
        assert fc.form.eissn.data == "9876-5432"

        # run the validation itself
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
        assert fc.target.application_status == constants.APPLICATION_STATUS_UPDATE_REQUEST # because it hasn't been finalised yet
        assert fc.target.bibjson().replaces == ["1111-1111"]
        assert fc.target.bibjson().is_replaced_by == ["2222-2222"]
        assert fc.target.bibjson().discontinued_date == "2001-01-01"
        assert fc.target.current_journal == "123456789987654321"
        assert fc.target.related_journal == "987654321123456789"
        assert fc.target.bibjson().subject == fc.source.bibjson().subject

        # now do finalise (which will also re-run all of the steps above)
        fc.finalise()
        assert fc.target.application_status == constants.APPLICATION_STATUS_UPDATE_REQUEST

        j2 = models.Journal.pull(journal.id)
        assert j2.current_application == fc.target.id
        assert fc.target.current_journal == j2.id

    def test_02_conditional_disabled(self):
        s = models.Suggestion(**deepcopy(UPDATE_REQUEST_SOURCE))

        # source only, all fields disabled
        formulaic_context = ApplicationFormFactory.context("update_request")
        fc = formulaic_context.processor(source=s)
        assert formulaic_context.get("pissn").get("disabled", False)
        assert formulaic_context.get("eissn").get("disabled", False)
        assert fc.validate()


    ##############################################
    # suite of tests for unrejecting an update request
    #############################################

    def test_03_reject_unreject_accept(self):
        """Check that submitting an update request, then rejecting it, then unrejecting it and then accepting
        it only results in a single resulting journal"""

        # make the journal to update
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_id("123456789987654321")    # this id is the one the UR fixture uses for current_journal
        journal.save(blocking=True)

        acc = models.Account()
        acc.set_id("testadmin")
        acc.set_role("admin")
        acc.save(blocking=True)
        ctx = self._make_and_push_test_context(acc=acc)

        pub = models.Account()
        pub.set_id("publisher")
        pub.set_email("publisher@example.com")
        pub.save(blocking=True)

        # create an update request
        ur = models.Application(**UPDATE_REQUEST_SOURCE)
        formulaic_context = ApplicationFormFactory.context("update_request")
        fc = formulaic_context.processor(source=ur)
        fc.finalise()

        # get a handle on the update request
        ur = fc.target

        # reject that update request
        admin_context = ApplicationFormFactory.context("admin")
        afc = admin_context.processor(source=ur)
        afc.form.application_status.data = constants.APPLICATION_STATUS_REJECTED
        afc.finalise(account=acc)

        # unreject the update request
        ur = models.Application.pull(ur.id)
        urfc = admin_context.processor(source=ur)
        urfc.form.application_status.data = constants.APPLICATION_STATUS_PENDING
        urfc.finalise(account=acc)

        # accept the update request
        ur = models.Application.pull(ur.id)
        acfc = admin_context.processor(source=ur)
        acfc.form.application_status.data = constants.APPLICATION_STATUS_ACCEPTED
        afc.finalise(account=acc)

        # check that we only have one journal
        time.sleep(2)
        assert len(models.Journal.all()) == 1



