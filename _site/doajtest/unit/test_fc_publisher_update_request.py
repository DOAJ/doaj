import re
from copy import deepcopy

from werkzeug.datastructures import MultiDict

from portality import constants
from doajtest.fixtures import JournalFixtureFactory, ApplicationFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models
from portality.formcontext import formcontext

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
        fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", source=models.Suggestion(**UPDATE_REQUEST_SOURCE))
        assert isinstance(fc, formcontext.PublisherUpdateRequest)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is None
        assert fc.template is not None

        # check that we can render the form
        # FIXME: we can't easily render the template - need to look into Flask-Testing for this
        # html = fc.render_template(edit_suggestion=True)
        html = fc.render_field_group("basic_info") # we know all these disabled fields are in the basic info section
        assert html is not None
        assert html != ""

        # check that the fields that should be disabled are disabled
        # "pissn", "eissn", "contact_name", "contact_email", "confirm_contact_email"
        rx_template = '(<input [^>]*?disabled[^>]+?name="{field}"[^>]*?>)'
        pissn_rx = rx_template.replace("{field}", "pissn")
        eissn_rx = rx_template.replace("{field}", "eissn")
        contact_name_rx = rx_template.replace("{field}", "contact_name")
        contact_email_rx = rx_template.replace("{field}", "contact_email")
        confirm_contact_email_rx = rx_template.replace("{field}", "confirm_contact_email")

        assert re.search(pissn_rx, html)
        assert re.search(eissn_rx, html)
        assert re.search(contact_name_rx, html)
        assert re.search(contact_email_rx, html)
        assert re.search(confirm_contact_email_rx, html)

        # now construct it from form data (with a known source)
        source = models.Suggestion(**UPDATE_REQUEST_SOURCE)
        acc = models.Account()
        acc.set_id(source.owner)
        acc.set_name("Test Owner")
        acc.set_email("test@example.com")
        acc.save(blocking=True)
        fc = formcontext.ApplicationFormFactory.get_form_context(
            role="publisher",
            form_data=MultiDict(UPDATE_REQUEST_FORM) ,
            source=source)

        assert isinstance(fc, formcontext.PublisherUpdateRequest)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is not None

        # test each of the workflow components individually ...

        # pre-validate and ensure that the disbaled fields get re-set
        fc.pre_validate()
        assert fc.form.pissn.data == "1234-5678"
        assert fc.form.eissn.data == "9876-5432"
        assert fc.form.contact_name.data == "Contact Name"
        assert fc.form.contact_email.data == "contact@email.com"
        assert fc.form.confirm_contact_email.data == "contact@email.com"

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
        assert fc.target.owner == "Owner"
        assert fc.target.editor_group == "editorgroup"
        assert fc.target.editor == "associate"
        assert fc.target.application_status == constants.APPLICATION_STATUS_UPDATE_REQUEST # because it hasn't been finalised yet
        assert fc.target.suggester['name'] == "Test Owner"
        assert fc.target.suggester['email'] == "test@example.com"
        assert fc.target.bibjson().replaces == ["1111-1111"]
        assert fc.target.bibjson().is_replaced_by == ["2222-2222"]
        assert fc.target.bibjson().discontinued_date == "2001-01-01"
        assert fc.target.current_journal == "123456789987654321"
        assert fc.target.related_journal == "987654321123456789"
        assert fc.target.bibjson().subjects() == fc.source.bibjson().subjects()

        # now do finalise (which will also re-run all of the steps above)
        fc.finalise()
        assert fc.target.application_status == constants.APPLICATION_STATUS_UPDATE_REQUEST

        j2 = models.Journal.pull(journal.id)
        assert j2.current_application == fc.target.id
        assert fc.target.current_journal == j2.id

    def test_02_conditional_disabled(self):
        s = models.Suggestion(**deepcopy(UPDATE_REQUEST_SOURCE))

        # source only, all fields disabled
        fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", source=s)
        assert "pissn" in fc.renderer.disabled_fields
        assert "eissn" in fc.renderer.disabled_fields
        assert "contact_name" in fc.renderer.disabled_fields
        assert "contact_email" in fc.renderer.disabled_fields
        assert "confirm_contact_email" in fc.renderer.disabled_fields
        assert fc.validate()

        # source only, no contact details, so those fields not disabled
        del s.data["admin"]["contact"]
        fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", source=s)
        assert "pissn" in fc.renderer.disabled_fields
        assert "eissn" in fc.renderer.disabled_fields
        assert "contact_name" not in fc.renderer.disabled_fields
        assert "contact_email" not in fc.renderer.disabled_fields
        assert "confirm_contact_email" not in fc.renderer.disabled_fields
        assert not fc.validate()

        # source + form data, everything complete from source, so all fields disabled
        s = models.Suggestion(**deepcopy(UPDATE_REQUEST_SOURCE))
        fd = MultiDict(deepcopy(UPDATE_REQUEST_FORM))
        fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", source=s, form_data=fd)
        assert "pissn" in fc.renderer.disabled_fields
        assert "eissn" in fc.renderer.disabled_fields
        assert "contact_name" in fc.renderer.disabled_fields
        assert "contact_email" in fc.renderer.disabled_fields
        assert "confirm_contact_email" in fc.renderer.disabled_fields
        assert fc.validate()

        # source + form data, both source and form missing some values, but disabled fields only draw from source
        del s.data["admin"]["contact"]
        rf = deepcopy(UPDATE_REQUEST_FORM)
        rf["contact_name"] = "Contact Name"
        fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", source=s, form_data=fd)
        assert "pissn" in fc.renderer.disabled_fields
        assert "eissn" in fc.renderer.disabled_fields
        assert "contact_name" not in fc.renderer.disabled_fields
        assert "contact_email" not in fc.renderer.disabled_fields
        assert "confirm_contact_email" not in fc.renderer.disabled_fields
        assert not fc.validate()
