from doajtest.helpers import DoajTestCase
# from flask.ext.testing import TestCase

import re
from copy import deepcopy

from portality import models
from portality.formcontext import formcontext

from werkzeug.datastructures import MultiDict

#####################################################################
# Source objects to be used for testing
#####################################################################


REAPPLICATION_SOURCE = {
    "id" : "abcdefghijk",
    "created_date" : "2000-01-01T00:00:00Z",
    "bibjson" : {
        # "active" : true|false,
        "title" : "The Title",
        "alternative_title" : "Alternative Title",
        "identifier": [
            {"type" : "pissn", "id" : "1234-5678"},
            {"type" : "eissn", "id" : "9876-5432"},
        ],
        "keywords" : ["word", "key"],
        "language" : ["EN", "FR"],
        "country" : "US",
        "publisher" : "The Publisher",
        "provider" : "Platform Host Aggregator",
        "institution" : "Society Institution",
        "link": [
            {"type" : "homepage", "url" : "http://journal.url"},
            {"type" : "waiver_policy", "url" : "http://waiver.policy"},
            {"type" : "editorial_board", "url" : "http://editorial.board"},
            {"type" : "aims_scope", "url" : "http://aims.scope"},
            {"type" : "author_instructions", "url" : "http://author.instructions.com"},
            {"type" : "oa_statement", "url" : "http://oa.statement"}
        ],
        "subject" : [
            {"scheme" : "LCC", "term" : "Economic theory. Demography", "code" : "HB1-3840"},
            {"scheme" : "LCC", "term" : "Social Sciences", "code" : "H"}
        ],

        "oa_start" : {
            "year" : 1980,
        },
        "apc_url" : "http://apc.com",
        "apc" : {
            "currency" : "GBP",
            "average_price" : 2
        },
        "submission_charges_url" : "http://submission.com",
        "submission_charges" : {
            "currency" : "USD",
            "average_price" : 4
        },
        "archiving_policy" : {
            "policy" : [
                "LOCKSS", "CLOCKSS",
                ["A national library", "Trinity"],
                ["Other", "A safe place"]
            ],
            "url" : "http://digital.archiving.policy"
        },
        "editorial_review" : {
            "process" : "Open peer review",
            "url" : "http://review.process"
        },
        "plagiarism_detection" : {
            "detection": True,
            "url" : "http://plagiarism.screening"
        },
        "article_statistics" : {
            "statistics" : True,
            "url" : "http://download.stats"
        },
        "deposit_policy" : ["Sherpa/Romeo", "Store it"],
        "author_copyright" : {
            "copyright" : "Sometimes",
            "url" : "http://copyright.com"
        },
        "author_publishing_rights" : {
            "publishing_rights" : "Occasionally",
            "url" : "http://publishing.rights"
        },
        "allows_fulltext_indexing" : True,
        "persistent_identifier_scheme" : ["DOI", "ARK", "PURL"],
        "format" : ["HTML", "XML", "Wordperfect"],
        "publication_time" : 8,
        "license" : [
            {
                "title" : "CC MY",
                "type" : "CC MY",
                "url" : "http://licence.url",
                "open_access": True,
                "BY": True,
                "NC": True,
                "ND": False,
                "SA": False,
                "embedded" : True,
                "embedded_example_url" : "http://licence.embedded"
            }
        ]
    },
    "suggestion" : {
        "articles_last_year" : {
            "count" : 16,
            "url" : "http://articles.last.year"
        },
        "article_metadata" : True
    },
    "admin" : {
        "application_status" : "reapplication",
        "notes" : [
            {"note" : "First Note", "date" : "2014-05-21T14:02:45Z"},
            {"note" : "Second Note", "date" : "2014-05-22T00:00:00Z"}
        ],
        "contact" : [
            {
                "email" : "contact@email.com",
                "name" : "Contact Name"
            }
        ],
        "owner" : "Owner",
        "editor_group" : "editorgroup",
        "editor" : "associate",
    }
}

######################################################################
# Complete, populated, form components
######################################################################

JOURNAL_INFO = {
    "title" : "The Title",
    "url" : "http://journal.url",
    "alternative_title" : "Alternative Title",
    "pissn" : "1234-5678",
    "eissn" : "9876-5432",
    "publisher" : "The Publisher",
    "society_institution" : "Society Institution",
    "platform" : "Platform Host Aggregator",
    "contact_name" : "Contact Name",
    "contact_email" : "contact@email.com",
    "confirm_contact_email" : "contact@email.com",
    "country" : "US",
    "processing_charges" : "True",
    "processing_charges_url" : "http://apc.com",
    "processing_charges_amount" : 2,
    "processing_charges_currency" : "GBP",
    "submission_charges" : "True",
    "submission_charges_url" : "http://submission.com",
    "submission_charges_amount" : 4,
    "submission_charges_currency" : "USD",
    "waiver_policy" : "True",
    "waiver_policy_url" : "http://waiver.policy",
    "digital_archiving_policy" : ["LOCKSS", "CLOCKSS", "A national library", "Other"],
    "digital_archiving_policy_other" : "A safe place",
    "digital_archiving_policy_library" : "Trinity",
    "digital_archiving_policy_url" : "http://digital.archiving.policy",
    "crawl_permission" : "True",
    "article_identifiers" : ["DOI", "ARK", "Other"],
    "article_identifiers_other" : "PURL",
    "download_statistics" : "True",
    "download_statistics_url" : "http://download.stats",
    "first_fulltext_oa_year" : 1980,
    "fulltext_format" : ["HTML", "XML", "Other"],
    "fulltext_format_other" : "Wordperfect",
    "keywords" : ["word", "key"],
    "languages" : ["EN", "FR"],
    "editorial_board_url" : "http://editorial.board",
    "review_process" : "Open peer review",
    "review_process_url" : "http://review.process",
    "aims_scope_url" : "http://aims.scope",
    "instructions_authors_url" : "http://author.instructions.com",
    "plagiarism_screening" : "True",
    "plagiarism_screening_url" : "http://plagiarism.screening",
    "publication_time" : 8,
    "oa_statement_url" : "http://oa.statement",
    "license_embedded" : "True",
    "license_embedded_url" : "http://licence.embedded",
    "license" : "Other",
    "license_other" : "CC MY",
    "license_checkbox" : ["BY", "NC"],
    "license_url" : "http://licence.url",
    "open_access" : "True",
    "deposit_policy" : ["Sherpa/Romeo", "Other"],
    "deposit_policy_other" : "Store it",
    "copyright" : "Other",
    "copyright_other" : "Sometimes",
    "copyright_url" : "http://copyright.com",
    "publishing_rights" : "Other",
    "publishing_rights_other" : "Occasionally",
    "publishing_rights_url" : "http://publishing.rights"
}

SUGGESTION = {
    "articles_last_year" : 16,
    "articles_last_year_url" : "http://articles.last.year",
    "metadata_provision" : "True"
}

SUGGESTER = {
    "suggester_name" : "Suggester",
    "suggester_email" : "suggester@email.com",
    "suggester_email_confirm" : "suggester@email.com"
}

NOTES = {
    'notes': [
        {'date': '2014-05-21T14:02:45Z', 'note': 'First Note'},
        {'date': '2014-05-22T00:00:00Z', 'note': 'Second Note'}
    ]
}

SUBJECT = {
    "subject" : ['HB1-3840', 'H']
}

JOURNAL_LEGACY = {
    "author_pays" : "Y",
    "author_pays_url" : "http://author.pays",
    "oa_end_year" : 1991
}

OWNER = {
    "owner" : "Owner"
}

EDITORIAL = {
    "editor_group" : "editorgroup",
    "editor" : "associate"
}

WORKFLOW = {
    "application_status" : "pending"
}

REAPPLICATION_FORMINFO = deepcopy(JOURNAL_INFO)
REAPPLICATION_FORMINFO.update(deepcopy(SUGGESTION))

REAPPLICATION_FORM = deepcopy(REAPPLICATION_FORMINFO)
REAPPLICATION_FORM["keywords"] = ",".join(REAPPLICATION_FORM["keywords"])
del REAPPLICATION_FORM["pissn"]
del REAPPLICATION_FORM["eissn"]
del REAPPLICATION_FORM["contact_name"]
del REAPPLICATION_FORM["contact_email"]
del REAPPLICATION_FORM["confirm_contact_email"]

######################################################
# Main test class
######################################################

class TestPublisherReApplication(DoajTestCase):

    # FIXME: abortive attempt to incorporate Flask-Testing.  May revisit if time permits
    #def create_app(self):
    #    from portality.core import app
    #    return app

    def setUp(self):
        super(TestPublisherReApplication, self).setUp()

    def tearDown(self):
        super(TestPublisherReApplication, self).tearDown()


    ###########################################################
    # Tests on the publisher's reapplication form
    ###########################################################

    def test_01_publisher_reapplication_success(self):
        """Give the publisher reapplication a full workout"""

        # we start by constructing it from source
        fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", source=models.Suggestion(**REAPPLICATION_SOURCE))
        assert isinstance(fc, formcontext.PublisherReApplication)
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
        fc = formcontext.ApplicationFormFactory.get_form_context(
            role="publisher",
            form_data=MultiDict(REAPPLICATION_FORM) ,
            source=models.Suggestion(**REAPPLICATION_SOURCE))

        assert isinstance(fc, formcontext.PublisherReApplication)
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
        assert len(fc.target.notes()) == 2
        assert fc.target.owner == "Owner"
        assert fc.target.editor_group == "editorgroup"
        assert fc.target.editor == "associate"
        assert fc.target.application_status == "reapplication" # because it hasn't been finalised yet
        assert fc.target.suggester['name'] == fc.form.contact_name.data
        assert fc.target.suggester['email'] == fc.form.contact_email.data

        # now do finalise (which will also re-run all of the steps above)
        fc.finalise()
        assert fc.target.application_status == "submitted"

    def test_02_conditional_disabled(self):
        s = models.Suggestion(**deepcopy(REAPPLICATION_SOURCE))

        # source only, all fields disabled
        fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", source=s)
        assert "pissn" in fc.renderer.disabled_fields
        assert "eissn" in fc.renderer.disabled_fields
        assert "contact_name" in fc.renderer.disabled_fields
        assert "contact_email" in fc.renderer.disabled_fields
        assert "confirm_contact_email" in fc.renderer.disabled_fields
        # should validate
        assert fc.validate()

        # source only, no contact details, so those fields not disabled
        del s.data["admin"]["contact"]
        fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", source=s)
        assert "pissn" in fc.renderer.disabled_fields
        assert "eissn" in fc.renderer.disabled_fields
        assert "contact_name" not in fc.renderer.disabled_fields
        assert "contact_email" not in fc.renderer.disabled_fields
        assert "confirm_contact_email" not in fc.renderer.disabled_fields
        # should fail to validate
        assert not fc.validate()

        # source + form data, everything complete from source, so all fields disabled
        s = models.Suggestion(**deepcopy(REAPPLICATION_SOURCE))
        fd = MultiDict(deepcopy(REAPPLICATION_FORM))
        fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", source=s, form_data=fd)
        assert "pissn" in fc.renderer.disabled_fields
        assert "eissn" in fc.renderer.disabled_fields
        assert "contact_name" in fc.renderer.disabled_fields
        assert "contact_email" in fc.renderer.disabled_fields
        assert "confirm_contact_email" in fc.renderer.disabled_fields
        # should validate
        assert fc.validate()

        # source + form data, both source and form missing some values, but disabled fields only draw from source
        del s.data["admin"]["contact"]
        rf = deepcopy(REAPPLICATION_FORM)
        rf["contact_name"] = "Contact Name"
        fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", source=s, form_data=fd)
        assert "pissn" in fc.renderer.disabled_fields
        assert "eissn" in fc.renderer.disabled_fields
        assert "contact_name" not in fc.renderer.disabled_fields
        assert "contact_email" not in fc.renderer.disabled_fields
        assert "confirm_contact_email" not in fc.renderer.disabled_fields
        # should fail to validate
        assert not fc.validate()
