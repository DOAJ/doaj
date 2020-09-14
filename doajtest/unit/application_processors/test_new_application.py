from portality import constants
from doajtest.helpers import DoajTestCase
from portality import models, core
from portality.forms.application_forms import ApplicationFormFactory
from portality.forms.application_processors import NewApplication


from doajtest.fixtures.v2.journals import JournalFixtureFactory
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory



#####################################################################
# Source objects to be used for testing
#####################################################################

JOURNAL_SOURCE = JournalFixtureFactory.make_journal_source(in_doaj=True)
JOURNAL_FORM = JournalFixtureFactory.make_journal_form()
APPLICATION_SOURCE = ApplicationFixtureFactory.make_application_source()
APPLICATION_FORM = ApplicationFixtureFactory.make_application_form()

######################################################
# Main test class
######################################################

class TestNewApplication(DoajTestCase):

    def setUp(self):
        super(TestNewApplication, self).setUp()

    def tearDown(self):
        super(TestNewApplication, self).tearDown()

    ###########################################################
    # Tests on the public application form in detail
    # (other form contexts will get their own files)
    ###########################################################

    def test_07_public_init(self):
        """Test that we can build the most basic kind of form in its initial condition - a blank form"""

        # make ourselves a form context from the source
        formulaic_context = ApplicationFormFactory.context("public")
        fc = formulaic_context.processor()
        # fc = formcontext.ApplicationFormFactory.get_form_context()

        # first check that we got the kind of object we expected
        assert isinstance(fc, NewApplication)

        # we should have populated the source and form aspects of the object
        assert fc.form_data is None
        assert fc.source is None
        assert fc.form is not None


    def test_08_public_from_formdata(self):
        """Test that we can build the most basic kind of form from form data"""
        formulaic_context = ApplicationFormFactory.context("public")
        fc = formulaic_context.processor(formdata=APPLICATION_FORM)
        # fc = formcontext.ApplicationFormFactory.get_form_context(form_data=formdata)

        # first check that we got the kind of object we expected
        assert isinstance(fc, NewApplication)

        # we should have populated the form_data and form aspects of the object
        assert fc.form_data is not None
        assert fc.form is not None
        assert fc.source is None


    def test_09_public_form_workflow(self):
        """Test that the active functions on the public application form work"""

        old_enable_email = core.app.config.get('ENABLE_EMAIL')
        core.app.config['ENABLE_EMAIL'] = False

        # create our form from the data
        formulaic_context = ApplicationFormFactory.context("public")
        APPLICATION_FORM["alternative_title"] = "   Alternative all with spaces   "
        fc = formulaic_context.processor(formdata=APPLICATION_FORM)
        #formdata = MultiDict(APPLICATION_FORM)
        #fc = formcontext.ApplicationFormFactory.get_form_context(form_data=formdata)

        # pre validate (should do nothing)
        fc.pre_validate()

        # crosswalk
        fc.form2target()
        assert fc.target is not None

        # patch the target (should do nothing)
        fc.patch_target()

        # now, finalise (which will run all the above stuff again)
        account = models.Account()
        account.set_id("test_account")
        account.set_name("Test Person")
        account.save(blocking=True)

        fc.finalise(account)
        assert fc.target is not None
        assert fc.target.application_status == constants.APPLICATION_STATUS_PENDING
        assert fc.target.date_applied is not None
        assert fc.target.bibjson().alternative_title == "Alternative all with spaces"

        core.app.config['ENABLE_EMAIL'] = old_enable_email


