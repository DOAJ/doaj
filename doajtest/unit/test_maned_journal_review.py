
from doajtest.helpers import DoajTestCase

from copy import deepcopy

from portality import models
from portality.formcontext import formcontext
from portality import lcc

from werkzeug.datastructures import MultiDict

#####################################################################
# Mocks required to make some of the lookups work
#####################################################################

@classmethod
def editor_group_pull(cls, field, value):
    eg = models.EditorGroup()
    eg.set_editor("eddie")
    eg.set_associates(["associate", "assan"])
    eg.set_name("Test Editor Group")
    return eg

mock_lcc_choices = [
    (u'H', u'Social Sciences'),
    (u'HB1-3840', u'--Economic theory. Demography')
]

def mock_lookup_code(code):
    if code == "H": return "Social Sciences"
    if code == "HB1-3840": return "Economic theory. Demography"
    return None

#####################################################################
# Source objects to be used for testing
#####################################################################

JOURNAL_SOURCE = {
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
            {"type" : "author_instructions", "url" : "http://author.instructions"},
            {"type" : "oa_statement", "url" : "http://oa.statement"}
        ],
        "subject" : [
            {"scheme" : "LCC", "term" : "Economic theory. Demography", "code" : "HB1-3840"},
            {"scheme" : "LCC", "term" : "Social Sciences", "code" : "H"}
        ],

        "oa_start" : {
            "year" : 1980,
        },
        "apc" : {
            "currency" : "GBP",
            "average_price" : 2
        },
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
            "url" : "http://copyright"
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
    "admin" : {
        "journal_status" : "rejournal",
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
    "processing_charges_amount" : 2,
    "processing_charges_currency" : "GBP",
    "submission_charges" : "True",
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

JOURNAL_FORMINFO = deepcopy(JOURNAL_INFO)
JOURNAL_FORMINFO.update(EDITORIAL)
JOURNAL_FORMINFO.update(SUBJECT)
JOURNAL_FORMINFO.update(NOTES)
JOURNAL_FORMINFO.update(OWNER)
JOURNAL_FORMINFO.update(JOURNAL_LEGACY)

JOURNAL_FORM = deepcopy(JOURNAL_FORMINFO)
JOURNAL_FORM["keywords"] = ",".join(JOURNAL_FORM["keywords"])

notes = JOURNAL_FORM["notes"]
del JOURNAL_FORM["notes"]
i = 0
for n in notes:
    notekey = "notes-" + str(i) + "-note"
    datekey = "notes-" + str(i) + "-date"
    JOURNAL_FORM[notekey] = n.get("note")
    JOURNAL_FORM[datekey] = n.get("date")
    i += 1

######################################################
# Main test class
######################################################

class TestManEdJournalReview(DoajTestCase):

    def setUp(self):
        super(TestManEdJournalReview, self).setUp()

        self.editor_group_pull = models.EditorGroup.pull_by_key
        models.EditorGroup.pull_by_key = editor_group_pull

        self.old_lcc_choices = lcc.lcc_choices
        lcc.lcc_choices = mock_lcc_choices

        self.old_lookup_code = lcc.lookup_code
        lcc.lookup_code = mock_lookup_code

    def tearDown(self):
        super(TestManEdJournalReview, self).tearDown()

        models.EditorGroup.pull_by_key = self.editor_group_pull
        lcc.lcc_choices = self.old_lcc_choices

        lcc.lookup_code = self.old_lookup_code

    def test_01_maned_review_success(self):
        """Give the Managing Editor's journal form a full workout"""

        # we start by constructing it from source
        fc = formcontext.JournalFormFactory.get_form_context(role="admin", source=models.Journal(**JOURNAL_SOURCE))
        assert isinstance(fc, formcontext.ManEdJournalReview)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is None
        assert fc.template is not None

        # no need to check form rendering - there are no disabled fields

        # now construct it from form data (with a known source)
        fc = formcontext.JournalFormFactory.get_form_context(
            role="admin",
            form_data=MultiDict(JOURNAL_FORM) ,
            source=models.Journal(**JOURNAL_SOURCE))

        assert isinstance(fc, formcontext.ManEdJournalReview)
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
        # everything else is overridden by the form, so no need to check it has patched

        # now do finalise (which will also re-run all of the steps above)
        fc.finalise()
        assert True # gives us a place to drop a break point later if we need it