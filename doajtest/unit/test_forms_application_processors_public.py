from werkzeug.datastructures import MultiDict
from wtforms import Form, StringField, validators

from portality import constants
from doajtest.helpers import DoajTestCase
from portality import models, core
from portality.lib.formulaic import FormProcessor
from portality.forms.application_forms import ApplicationFormFactory
from portality.forms.application_processors import NewApplication

from doajtest.fixtures.v2.journals import JournalFixtureFactory
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory

#####################################################################
# Source objects to be used for testing
#####################################################################

JOURNAL_SOURCE = JournalFixtureFactory.make_journal_source(in_doaj=True)
APPLICATION_SOURCE = ApplicationFixtureFactory.make_application_source()
APPLICATION_FORM = ApplicationFixtureFactory.make_application_form()

######################################################
# Extensions of base form context classes for use in
# testing
######################################################

TEST_SOURCE = {"one" : "one", "two" : "two"}
TEST_SOURCE2 = {"one" : "three", "two" : "four"}


class FailValidation(object):
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, form, field):
        raise validators.ValidationError("validation failed")


######################################################
# Main test class
######################################################

class TestPublicApplicationProcessor(DoajTestCase):

    def setUp(self):
        super(TestPublicApplicationProcessor, self).setUp()

    def tearDown(self):
        super(TestPublicApplicationProcessor, self).tearDown()

    ###########################################################
    # Tests on the public application form in detail
    # (other form contexts will get their own files)
    ###########################################################

    def test_07_public_init(self):
        """Test that we can build the most basic kind of form in its initial condition - a blank form"""

        # make ourselves a form context from the source
        fc = ApplicationFormFactory.context("public")
        processor = fc.processor()

        # first check that we got the kind of object we expected
        assert isinstance(processor, NewApplication)

        # we should have populated the source and form aspects of the object
        assert processor.form_data is None
        assert processor.source is None
        assert processor.form is not None

    def test_08_public_from_formdata(self):
        """Test that we can build the most basic kind of form from form data"""

        formdata = MultiDict(APPLICATION_FORM)
        fc = ApplicationFormFactory.context("public")
        processor = fc.processor(formdata=formdata)

        # first check that we got the kind of object we expected
        assert isinstance(processor, NewApplication)

        # we should have populated the form_data and form aspects of the object
        assert processor.form_data is not None
        assert processor.form is not None
        assert processor.source is None


    def test_09_public_form_workflow(self):
        """Test that the active functions on the public application form work"""

        old_enable_email = core.app.config.get('ENABLE_EMAIL')
        core.app.config['ENABLE_EMAIL'] = False

        account = models.Account()
        account.set_name("Test Account")
        account.set_email("account@example.com")
        account.save(blocking=True)

        # create our form from the data
        formdata = MultiDict(APPLICATION_FORM)
        fc = ApplicationFormFactory.context("public")
        processor = fc.processor(formdata=formdata)

        # pre validate (should do nothing)
        processor.pre_validate()

        processor.validate()

        # crosswalk
        processor.form2target()
        assert processor.target is not None

        # patch the target (should do nothing)
        processor.patch_target()

        # now, finalise (which will run all the above stuff again)
        processor.finalise(account)
        assert processor.target is not None
        assert processor.target.application_status == constants.APPLICATION_STATUS_PENDING
        assert processor.target.date_applied is not None
        assert processor.target.owner == account.id

        core.app.config['ENABLE_EMAIL'] = old_enable_email

