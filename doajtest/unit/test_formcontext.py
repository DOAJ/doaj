from doajtest.helpers import DoajTestCase

from portality import models
from portality.formcontext import formcontext, xwalk

from werkzeug.datastructures import MultiDict


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
        ]
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
        "application_status": "accepted",
        "in_doaj": False
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
        "archiving_policy": {"policy": ["LOCKSS"], "url": "http://cinej.pitt.edu/ojs/index.php/cinej/about/editorialPolicies#archiving"},
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
        ]
    }
}

class TestFormContext(DoajTestCase):
    def setUp(self): pass
    def tearDown(self): pass

    ###########################################################
    # Tests on the public application form
    ###########################################################

    def test_01_public_from_source(self):
        """Test that we can build the most basic kind of form from source, and that all its properties are right"""

        # make ourselves a form context from the source
        source = models.Suggestion(**APPLICATION_SOURCE)
        fc = formcontext.JournalFormFactory.get_form_context(source=source)

        # first check that we got the kind of object we expected
        assert isinstance(fc, formcontext.PublicApplicationForm)

        # we should have populated the source and form aspects of the object
        assert fc.form_data is None
        assert fc.source is not None
        assert fc.form is not None

    def test_02_public_from_formdata(self):
        """Test that we can build the most basic kind of form from form data"""

        # take the source and explicitly convert it to form data form
        # (note, we need to have tested the xwalks elsewhere)
        source = models.Suggestion(**APPLICATION_SOURCE)
        formdata = MultiDict(xwalk.SuggestionFormXWalk.obj2form(source))
        fc = formcontext.JournalFormFactory.get_form_context(form_data=formdata)

        # first check that we got the kind of object we expected
        assert isinstance(fc, formcontext.PublicApplicationForm)

        # we should have populated the source and form aspects of the object
        assert fc.form_data is not None
        assert fc.form is not None
        assert fc.source is None

    def test_03_public_form_render(self):
        """Test that we can render the basic form """
        fc = formcontext.JournalFormFactory.get_form_context()
        frag = fc.render_field_group("basic_info")

        assert frag != ""