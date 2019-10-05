from werkzeug.datastructures import MultiDict
from wtforms import Form, StringField, validators

from portality import constants
from doajtest.helpers import DoajTestCase
from portality import models, core
from portality.formcontext import formcontext, render

#####################################################################
# Source objects to be used for testing
#####################################################################

JOURNAL_SOURCE = {
    "index": {
        "publisher": ["Centro Centroamericano de Poblaci\u00f3n"],
        "schema_subject": ["LCC:Social Sciences", "LCC:Economic theory. Demography"],
        "license": ["CC by-nc-sa"],
        "classification": ["Social Sciences", "Economic theory. Demography"],
        "title": ["Poblaci\u00f3n y Salud en Mesoam\u00e9rica"],
        "country": "Costa Rica",
        "issn": ["1659-0201"],
        "language": ["Spanish"],
        "homepage_url": "http://revistas.ucr.ac.cr/index.php/psm/index",
        "schema_code": ["LCC:HB1-3840", "LCC:H"],
        "subject": ["Central America", "public health", "demography", "population studies", "Social Sciences", "Economic theory. Demography"]
    },
    "last_updated": "2014-05-05T18:18:01Z",
    "admin": {
        "owner": "16590201",
        "in_doaj": True
    },
    "created_date": "2008-05-19T16:45:03Z",
    "id": "3f3d352f32364065ab9051b1a4b2d715",
    "bibjson": {
        "publisher": "Centro Centroamericano de Poblaci\u00f3n",
        "author_pays": "N",
        "license": [{"type": "CC by-nc-sa", "title": "CC by-nc-sa"}],
        "language": ["Spanish"],
        "title": "Poblaci\u00f3n y Salud en Mesoam\u00e9rica",
        "author_pays_url": "http://revistas.ucr.ac.cr/index.php/psm/about/submissions",
        "country": "CR",
        "alternative_title": "",
        "active": True,
        "link": [{"url": "http://revistas.ucr.ac.cr/index.php/psm/index", "type": "homepage"}],
        "oa_end": {},
        "provider": "Universidad de Costa Rica",
        "keywords": ["demography", "population studies", "public health", "Central America"],
        "oa_start": {"year": 2003},
        "identifier": [{"type": "pissn", "id": "1659-0201"}],
        "subject": [
            {"code": "HB1-3840", "term": "Economic theory. Demography", "scheme": "LCC"},
            {"code": "H", "term": "Social Sciences", "scheme": "LCC"}
        ],
        "replaces" : ["1111-1111"],
        "is_replaced_by" : ["2222-2222"],
        "discontinued_date" : "2001-01-01"
    }
}

APPLICATION_SOURCE = {
    "index": {
        "oa_statement_url": "http://cinej.pitt.edu/ojs/index.php/cinej/about/editorialPolicies#openAccessPolicy",
        "publisher": ["University Library Systems", "University of Pittsburgh"],
        "schema_subject": ["LCC:Visual arts", "LCC:Communication. Mass media"],
        "license": ["CC by"],
        "classification": ["Visual arts", "Communication. Mass media"],
        "title": ["CINEJ Cinema Journal"],
        "country": "United States",
        "issn": ["2158-8724", "2159-2411"],
        "language": ["EN"],
        "homepage_url": "http://cinej.pitt.edu/",
        "aims_scope_url": "http://cinej.pitt.edu/ojs/index.php/cinej/about/editorialPolicies#focusAndScope",
        "schema_code": ["LCC:N1-9211", "LCC:P87-96"],
        "author_instructions_url": "http://cinej.pitt.edu/ojs/index.php/cinej/about/submissions#authorGuidelines",
        "editorial_board_url": "http://cinej.pitt.edu/ojs/index.php/cinej/about/displayMembership/2",
        "subject": ["Visual arts", "television", "cinema studies", "media", "communication", "Communication. Mass media", "film"]
    },
    "last_updated": "2014-05-21T14:02:45Z",
    "admin": {
        "owner": "15624730",
        "notes": [{"date": "2014-05-21T14:02:45Z", "note": "ok/RZ"}],
        "contact": [{"name": "Murat Akser", "email": "m.akser@ulster.ac.uk"}],
        "application_status": constants.APPLICATION_STATUS_ACCEPTED
    },
    "suggestion": {
        "articles_last_year": {"count": 19, "url": "http://cinej.pitt.edu/ojs/index.php/cinej/issue/archive"},
        "suggested_on": "2014-04-09T20:43:18Z",
        "suggester": {"name": "Murat Akser", "email": "m.akser@ulster.ac.uk"},
        "article_metadata": True
    },
    "created_date": "2014-04-09T20:43:18Z",
    "id": "248c57960a3940e59bdca3f7296c89b2",
    "bibjson": {
        "allows_fulltext_indexing": True,
        "archiving_policy": {
            "known": ["LOCKSS"],
            "url": "http://cinej.pitt.edu/ojs/index.php/cinej/about/editorialPolicies#archiving"
        },
        "persistent_identifier_scheme": ["DOI"],
        "keywords": ["cinema studies", "film", "media", "television", "communication"],
        "subject": [
            {"code": "N1-9211", "term": "Visual arts", "scheme": "LCC"},
            {"code": "P87-96", "term": "Communication. Mass media", "scheme": "LCC"}
        ],
        "article_statistics": {"url": "http://cinej.pitt.edu/ojs/index.php/cinej/about/editorialPolicies#custom-1", "statistics": True},
        "title": "CINEJ Cinema Journal",
        "publication_time": 12,
        "provider": "D-Scribe Digital Publishing Program",
        "format": ["PDF"],
        "plagiarism_detection": {"detection": True, "url": "http://cinej.pitt.edu/ojs/index.php/cinej/about/editorialPolicies#custom-2"},
        "link": [
            {"url": "http://cinej.pitt.edu/", "type": "homepage"},
            {"url": "http://cinej.pitt.edu/ojs/index.php/cinej/about/displayMembership/2", "type": "editorial_board"},
            {"url": "http://cinej.pitt.edu/ojs/index.php/cinej/about/editorialPolicies#focusAndScope", "type": "aims_scope"},
            {"url": "http://cinej.pitt.edu/ojs/index.php/cinej/about/submissions#authorGuidelines", "type": "author_instructions"},
            {"url": "http://cinej.pitt.edu/ojs/index.php/cinej/about/editorialPolicies#openAccessPolicy", "type": "oa_statement"}
        ],
        "oa_start": {"year": 2011},
        "editorial_review": {"process": "Double blind peer review", "url": "http://cinej.pitt.edu/ojs/index.php/cinej/about/submissions#authorGuidelines"},
        "author_copyright": {"url": "http://cinej.pitt.edu/ojs/index.php/cinej/about/submissions#copyrightNotice", "copyright": True},
        "institution": "University Library Systems",
        "deposit_policy": ["Sherpa/Romeo"],
        "language": ["EN"],
        "license": [
            {
                "open_access": True,
                 "embedded": True,
                 "title": "CC by",
                 "url": "http://cinej.pitt.edu/ojs/index.php/cinej/about",
                 "NC": False,
                 "ND": False,
                 "embedded_example_url": "http://cinej.pitt.edu/ojs/index.php/cinej/about",
                 "SA": False,
                 "type": "CC by",
                 "BY": True
            }
        ],
        "country": "US",
        "publisher": "University of Pittsburgh",
        "author_publishing_rights": {"url": "http://cinej.pitt.edu/ojs/index.php/cinej/about/submissions#copyrightNotice", "publishing_rights": True},
        "identifier": [
            {"type": "pissn", "id": "2159-2411"},
            {"type": "eissn", "id": "2158-8724"}
        ],
        "replaces" : ["1111-1111"],
        "is_replaced_by" : ["2222-2222"],
        "discontinued_date" : "2001-01-01"
    }
}

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


