from doajtest.helpers import DoajTestCase
from doajtest.fixtures import JournalFixtureFactory, ApplicationFixtureFactory

import time
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

APPLICATION_SOURCE = {
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
        "replaces" : ["1111-1111"],
        "is_replaced_by" : ["2222-2222"],
        "discontinued_date" : "2001-01-01",
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
            "known" : ["LOCKSS", "CLOCKSS"],
            "nat_lib" : "Trinity",
            "other" : "A safe place",
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
            "copyright" : "True",
            "url" : "http://copyright"
        },
        "author_publishing_rights" : {
            "publishing_rights" : "True",
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
        "suggested_on": "2014-04-09T20:43:18Z",
        "suggester": {
            "name": "Suggester Name",
            "email": "suggester@email.com"
        },
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

JOURNAL_SOURCE = JournalFixtureFactory.make_journal_source(in_doaj=True)

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
    "copyright" : "True",
    "copyright_url" : "http://copyright.com",
    "publishing_rights" : "True",
    "publishing_rights_url" : "http://publishing.rights",
    "replaces" : ["1111-1111"],
    "is_replaced_by" : ["2222-2222"],
    "discontinued_date" : "2001-01-01"
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

APPLICATION_FORMINFO = deepcopy(JOURNAL_INFO)
APPLICATION_FORMINFO.update(deepcopy(SUGGESTION))
APPLICATION_FORMINFO.update(EDITORIAL)
APPLICATION_FORMINFO.update(WORKFLOW)
APPLICATION_FORMINFO.update(SUBJECT)
APPLICATION_FORMINFO.update(SUGGESTER)
APPLICATION_FORMINFO.update(NOTES)
APPLICATION_FORMINFO.update(OWNER)

APPLICATION_FORM = deepcopy(APPLICATION_FORMINFO)
APPLICATION_FORM["keywords"] = ",".join(APPLICATION_FORM["keywords"])

notes = APPLICATION_FORM["notes"]
del APPLICATION_FORM["notes"]
i = 0
for n in notes:
    notekey = "notes-" + str(i) + "-note"
    datekey = "notes-" + str(i) + "-date"
    APPLICATION_FORM[notekey] = n.get("note")
    APPLICATION_FORM[datekey] = n.get("date")
    i += 1

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
        """Give the editor's reapplication form a full workout"""
        acc = models.Account()
        acc.set_id("richard")
        acc.add_role("admin")
        ctx = self._make_and_push_test_context(acc=acc)

        # we start by constructing it from source
        fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=models.Suggestion(**APPLICATION_SOURCE))
        assert isinstance(fc, formcontext.ManEdApplicationReview)
        assert fc.form is not None
        assert fc.source is not None
        assert fc.form_data is None
        assert fc.template is not None

        # no need to check form rendering - there are no disabled fields

        # now construct it from form data (with a known source)
        fc = formcontext.ApplicationFormFactory.get_form_context(
            role="admin",
            form_data=MultiDict(APPLICATION_FORM) ,
            source=models.Suggestion(**APPLICATION_SOURCE))

        assert isinstance(fc, formcontext.ManEdApplicationReview)
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

        time.sleep(2)

        # now check that a provenance record was recorded
        prov = models.Provenance.get_latest_by_resource_id(fc.target.id)
        assert prov is not None

        ctx.pop()

    def test_02_reapplication(self):
        acc = models.Account()
        acc.set_id("richard")
        acc.add_role("admin")
        ctx = self._make_and_push_test_context(acc=acc)

        # There needs to be an existing journal in the index for this test to work
        extant_j = models.Journal(**JOURNAL_SOURCE)
        assert extant_j.last_reapplication is None
        extant_j_created_date = extant_j.created_date
        extant_j.save()
        time.sleep(1)

        # We've added one journal, so there'll be one snapshot already
        assert models.Journal.count() == 1
        h = self.list_today_journal_history_files()
        assert len(h) == 1

        # set up an application which is a reapp on an existing journal
        s = models.Suggestion(**APPLICATION_SOURCE)
        s.set_current_journal("abcdefghijk_journal")
        s.set_application_status("submitted")

        # set up the form which "accepts" this reapplication
        fd = deepcopy(APPLICATION_FORM)
        fd["application_status"] = "accepted"
        fd = MultiDict(fd)

        # create and finalise the form context
        fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", form_data=fd, source=s)

        # with app.test_request_context():
        fc.finalise()

        # let the index catch up
        time.sleep(1)

        j = models.Journal.pull("abcdefghijk_journal")
        assert j is not None
        assert j.created_date == extant_j_created_date
        assert j.last_reapplication is not None
        assert models.Journal.count() == 1

        h = self.list_today_journal_history_files()
        assert h is not None
        assert len(h) == 2

        ctx.pop()

    def test_03_classification_required(self):
        # Check we can accept an application with a subject classification present
        ready_application = models.Suggestion(**ApplicationFixtureFactory.make_application_source())
        ready_application.set_application_status("ready")

        fc = formcontext.ApplicationFormFactory.get_form_context(role='admin', source=ready_application)

        # Make changes to the application status via the form, check it validates
        fc.form.application_status.data = "accepted"

        assert fc.validate()

        # Without a subject classification, we should not be able to set the status to 'accepted'
        no_class_application = models.Suggestion(**ApplicationFixtureFactory.make_application_source())
        del no_class_application.data['bibjson']['subject']
        fc = formcontext.ApplicationFormFactory.get_form_context(role='admin', source=no_class_application)
        # Make changes to the application status via the form
        assert fc.source.bibjson().subjects() == []
        fc.form.application_status.data = "accepted"

        assert not fc.validate()

        # However, we should be able to set it to a different status rather than 'accepted'
        fc.form.application_status.data = "in progress"

        assert fc.validate()

    def test_04_maned_review_continuations(self):
        # construct it from form data (with a known source)
        fc = formcontext.ApplicationFormFactory.get_form_context(
            role='admin',
            form_data=MultiDict(APPLICATION_FORM),
            source=models.Suggestion(**ApplicationFixtureFactory.make_application_source()))

        # check the form has the continuations data
        assert fc.form.replaces.data == ["1111-1111"]
        assert fc.form.is_replaced_by.data == ["2222-2222"]
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
        """Give the editor's reapplication form a full workout"""
        acc = models.Account()
        acc.set_id("richard")
        acc.add_role("admin")
        ctx = self._make_and_push_test_context(acc=acc)

        # construct a context from a form submission
        source = deepcopy(APPLICATION_FORM)
        source["application_status"] = "accepted"
        fd = MultiDict(source)
        fc = formcontext.ApplicationFormFactory.get_form_context(
            role="admin",
            form_data=fd,
            source=models.Suggestion(**APPLICATION_SOURCE))

        fc.finalise()
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
        """Give the editor's reapplication form a full workout"""
        acc = models.Account()
        acc.set_id("richard")
        acc.add_role("admin")
        ctx = self._make_and_push_test_context(acc=acc)

        # construct a context from a form submission
        source = deepcopy(APPLICATION_FORM)
        source["application_status"] = "rejected"
        fd = MultiDict(source)
        fc = formcontext.ApplicationFormFactory.get_form_context(
            role="admin",
            form_data=fd,
            source=models.Suggestion(**APPLICATION_SOURCE))

        fc.finalise()
        time.sleep(2)

        # now check that a provenance record was recorded
        count = 0
        for prov in models.Provenance.iterall():
            if prov.action == "edit":
                count += 1
            if prov.action == "status:rejected":
                count += 10
        assert count == 11

        ctx.pop()
