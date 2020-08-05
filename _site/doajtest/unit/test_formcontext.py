from werkzeug.datastructures import MultiDict
from wtforms import Form, StringField, validators

from portality import constants
from doajtest.helpers import DoajTestCase
from portality import models, core
from portality.formcontext import formcontext, render

from doajtest.fixtures.journals import JournalFixtureFactory
from doajtest.fixtures.applications import ApplicationFixtureFactory

#####################################################################
# Source objects to be used for testing
#####################################################################

JOURNAL_SOURCE = JournalFixtureFactory.make_journal_source(in_doaj=True)

APPLICATION_SOURCE = ApplicationFixtureFactory.make_application_source()

APPLICATION_FORM = {
    'aims_scope_url': 'http://cinej.pitt.edu/ojs/index.php/cinej/about/editorialPolicies#focusAndScope',
    'alternative_title': None,
    'application_status': constants.APPLICATION_STATUS_ACCEPTED,
    'article_identifiers': ['DOI'],
    'article_identifiers_other': '',
    'articles_last_year': 19,
    'articles_last_year_url': 'http://cinej.pitt.edu/ojs/index.php/cinej/issue/archive',
    'confirm_contact_email': 'm.akser@ulster.ac.uk',
    'contact_email': 'm.akser@ulster.ac.uk',
    'contact_name': 'Murat Akser',
    'copyright': 'True',
    'copyright_url': 'http://cinej.pitt.edu/ojs/index.php/cinej/about/submissions#copyrightNotice',
    'country': 'US',
    'crawl_permission': 'True',
    'deposit_policy': ['Sherpa/Romeo'],
    'deposit_policy_other': '',
    'digital_archiving_policy': ['LOCKSS'],
    'digital_archiving_policy_library': '',
    'digital_archiving_policy_other': '',
    'digital_archiving_policy_url': 'http://cinej.pitt.edu/ojs/index.php/cinej/about/editorialPolicies#archiving',
    'download_statistics': 'True',
    'download_statistics_url': 'http://cinej.pitt.edu/ojs/index.php/cinej/about/editorialPolicies#custom-1',
    'editorial_board_url': 'http://cinej.pitt.edu/ojs/index.php/cinej/about/displayMembership/2',
    'eissn': '2158-8724',
    'first_fulltext_oa_year': 2011,
    'fulltext_format': ['PDF'],
    'fulltext_format_other': '',
    'instructions_authors_url': 'http://cinej.pitt.edu/ojs/index.php/cinej/about/submissions#authorGuidelines',
    'keywords': ['cinema studies','film','media','television','communication'],
    'languages': ['EN'],
    'license': 'Other',
    'license_checkbox': ['BY'],
    'license_embedded': 'True',
    'license_embedded_url': 'http://cinej.pitt.edu/ojs/index.php/cinej/about',
    'license_other': 'CC by',
    'license_url': 'http://cinej.pitt.edu/ojs/index.php/cinej/about',
    'metadata_provision': 'True',
    'notes': [{'date': '2014-05-21T14:02:45Z', 'note': 'ok/RZ'}],
    'oa_statement_url': 'http://cinej.pitt.edu/ojs/index.php/cinej/about/editorialPolicies#openAccessPolicy',
    'open_access': 'True',
    'owner': '15624730',
    'pissn': '2159-2411',
    'plagiarism_screening': 'True',
    'plagiarism_screening_url': 'http://cinej.pitt.edu/ojs/index.php/cinej/about/editorialPolicies#custom-2',
    'platform': 'D-Scribe Digital Publishing Program',
    'processing_charges': 'False',
    "processing_charges_url" : "",
    'publication_time': 12,
    'publisher': 'University of Pittsburgh',
    'publishing_rights': 'True',
    'publishing_rights_url': 'http://cinej.pitt.edu/ojs/index.php/cinej/about/submissions#copyrightNotice',
    'review_process': 'Double blind peer review',
    'review_process_url': 'http://cinej.pitt.edu/ojs/index.php/cinej/about/submissions#authorGuidelines',
    'society_institution': 'University Library Systems',
    'subject': ['N1-9211', 'P87-96'],
    'submission_charges': 'False',
    "submission_charges_url" : "",
    'suggester_email': 'm.akser@ulster.ac.uk',
    'suggester_email_confirm': 'm.akser@ulster.ac.uk',
    'suggester_name': 'Murat Akser',
    'title': 'CINEJ Cinema Journal',
    'url': 'http://cinej.pitt.edu/',
    'waiver_policy': False,
    'waiver_policy_url': None
}

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

class TestForm(Form):
    one = StringField("One", [FailValidation()])
    two = StringField("Two")

class TestRenderer(render.Renderer):
    def __init__(self):
        super(TestRenderer, self).__init__()
        self.FIELD_GROUPS = {
            "test" : [
                {"one" : {}},
                {"two" : {}}
            ]
        }

class TestContext(formcontext.FormContext):
    def data2form(self):
        self.form = TestForm(formdata=self.form_data)

    def source2form(self):
        self.form = TestForm(data=self.source)

    def blank_form(self):
        self.form = TestForm()

    def form2target(self):
        self.add_alert("xwalking")
        self.target = {"three" : "three"}

    def patch_target(self):
        self.add_alert("finalising")
        self.target.update({"four" : "four"})

    def make_renderer(self):
        self.renderer = TestRenderer()

    def set_template(self):
        self.template = "test_template.html"

    def pre_validate(self):
        self.did_pre_validation = True

######################################################
# Main test class
######################################################

class TestFormContext(DoajTestCase):

    def setUp(self):
        super(TestFormContext, self).setUp()

    def tearDown(self):
        super(TestFormContext, self).tearDown()

    ###########################################################
    # Tests on the base classes
    ###########################################################

    def test_01_formcontext_init(self):
        fc = formcontext.FormContext()
        assert fc.source is None
        assert fc.form_data is None
        assert fc.target is None

        fc = formcontext.FormContext(form_data=MultiDict(TEST_SOURCE))
        assert fc.source is None
        assert fc.form_data is not None
        assert fc.target is None

        fc = formcontext.FormContext(source=TEST_SOURCE)
        assert fc.source is not None
        assert fc.form_data is None
        assert fc.target is None

        fc = formcontext.FormContext(form_data=MultiDict(TEST_SOURCE), source=TEST_SOURCE)
        assert fc.source is not None
        assert fc.form_data is not None
        assert fc.target is None

    def test_02_formcontext_subclass_init(self):
        fc = TestContext()
        assert fc.form["one"].data is None
        assert fc.form["two"].data is None

        fc = TestContext(form_data=MultiDict(TEST_SOURCE))
        assert fc.form["one"].data == "one"
        assert fc.form["two"].data == "two"

        fc = TestContext(source=TEST_SOURCE2)
        assert fc.form["one"].data == "three"
        assert fc.form["two"].data == "four"

        # this shows that the form data takes precedence over the source
        fc = TestContext(form_data=MultiDict(TEST_SOURCE), source=TEST_SOURCE2)
        assert fc.form["one"].data == "one"
        assert fc.form["two"].data == "two"

        assert isinstance(fc.renderer, TestRenderer)
        assert fc.template == "test_template.html"

    def test_03_formcontext_subclass_finalise(self):
        fc = TestContext(source=TEST_SOURCE)
        fc.finalise()

        assert fc.target["three"] == "three"
        assert fc.target["four"] == "four"

        assert len(fc.alert) == 2
        assert "xwalking" in fc.alert
        assert "finalising" in fc.alert

    def test_04_formcontext_validate(self):
        fc = TestContext(source=TEST_SOURCE)
        valid = fc.validate()

        assert not valid
        assert fc.did_pre_validation
        assert len(fc.renderer.error_fields) == 1
        assert "one" in fc.renderer.error_fields
        assert fc.errors

    def test_05_formcontext_subclass_render(self):
        fc = TestContext(source=TEST_SOURCE)
        html = fc.render_field_group("test")

        assert html is not None
        assert html != ""
        assert '<input id="one"' in html
        assert '<input id="two"' in html


    ###########################################################
    # Tests on the factory
    ###########################################################

    def test_06_formcontext_factory(self):
        fc = formcontext.ApplicationFormFactory.get_form_context()
        assert isinstance(fc, formcontext.PublicApplication)
        assert fc.form is not None
        assert fc.form_data is None
        assert fc.source is None

        fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=models.Suggestion(**APPLICATION_SOURCE))
        assert isinstance(fc, formcontext.ManEdApplicationReview)
        assert fc.form is not None
        assert fc.form_data is None
        assert fc.source is not None

        fc = formcontext.ApplicationFormFactory.get_form_context(role="editor", source=models.Suggestion(**APPLICATION_SOURCE), form_data=MultiDict(APPLICATION_FORM))
        assert isinstance(fc, formcontext.EditorApplicationReview)
        assert fc.form is not None
        assert fc.form_data is not None
        assert fc.source is not None

        fc = formcontext.ApplicationFormFactory.get_form_context("associate_editor", source=models.Suggestion(**APPLICATION_SOURCE), form_data=MultiDict(APPLICATION_FORM))
        assert isinstance(fc, formcontext.AssEdApplicationReview)
        assert fc.form is not None
        assert fc.form_data is not None
        assert fc.source is not None

        fc = formcontext.ApplicationFormFactory.get_form_context("publisher", source=models.Suggestion(**APPLICATION_SOURCE), form_data=MultiDict(APPLICATION_FORM))
        assert isinstance(fc, formcontext.PublisherUpdateRequest)
        assert fc.form is not None
        assert fc.form_data is not None
        assert fc.source is not None

    ###########################################################
    # Tests on the public application form in detail
    # (other form contexts will get their own files)
    ###########################################################

    def test_07_public_init(self):
        """Test that we can build the most basic kind of form in its initial condition - a blank form"""

        # make ourselves a form context from the source
        fc = formcontext.ApplicationFormFactory.get_form_context()

        # first check that we got the kind of object we expected
        assert isinstance(fc, formcontext.PublicApplication)

        # we should have populated the source and form aspects of the object
        assert fc.form_data is None
        assert fc.source is None
        assert fc.form is not None

        # check that the other implementation aspects of the context have been populated (but let's not get too specific about what they are)
        assert fc.renderer is not None
        assert isinstance(fc.renderer, render.Renderer) # the parent class of renderers
        assert fc.template is not None and fc.template != ""

    def test_08_public_from_formdata(self):
        """Test that we can build the most basic kind of form from form data"""

        formdata = MultiDict(APPLICATION_FORM)
        fc = formcontext.ApplicationFormFactory.get_form_context(form_data=formdata)

        # first check that we got the kind of object we expected
        assert isinstance(fc, formcontext.PublicApplication)

        # we should have populated the form_data and form aspects of the object
        assert fc.form_data is not None
        assert fc.form is not None
        assert fc.source is None


    def test_09_public_form_workflow(self):
        """Test that the active functions on the public application form work"""

        old_enable_email = core.app.config.get('ENABLE_EMAIL')
        core.app.config['ENABLE_EMAIL'] = False

        # create our form from the data
        formdata = MultiDict(APPLICATION_FORM)
        fc = formcontext.ApplicationFormFactory.get_form_context(form_data=formdata)

        # pre validate (should do nothing)
        fc.pre_validate()

        # crosswalk
        fc.form2target()
        assert fc.target is not None

        # patch the target (should do nothing)
        fc.patch_target()

        # now, finalise (which will run all the above stuff again)
        fc.finalise()
        assert fc.target is not None
        assert fc.target.application_status == constants.APPLICATION_STATUS_PENDING
        assert fc.target.suggested_on is not None

        core.app.config['ENABLE_EMAIL'] = old_enable_email


    def test_10_public_form_render(self):
        """Test that we can render the basic form """
        fc = formcontext.ApplicationFormFactory.get_form_context()
        frag = fc.render_field_group("basic_info")
        assert frag != ""


