from doajtest.helpers import DoajTestCase
from portality import models, reapplication, clcsv
import os, time, uuid
from copy import deepcopy
from portality.formcontext import xwalk, forms
from portality.clcsv import ClCsv

APPLICATION_SOURCE = {
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
        "suggester" : {
            "name" : "Suggester",
            "email" : "suggester@email.com"
        },
        "articles_last_year" : {
            "count" : 16,
            "url" : "http://articles.last.year"
        },
        "article_metadata" : True
    },
    "admin" : {
        "application_status" : "pending",
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

APPLICATION_COL = [
    "The Title",
    "http://journal.url",
    "Alternative Title",
    "1234-5678",
    "9876-5432",
    "The Publisher",
    "Society Institution",
    "Platform Host Aggregator",
    "Contact Name",
    "contact@email.com",
    "contact@email.com",
    "US",
    "Yes",
    2,
    "GBP",
    "Yes",
    4,
    "USD",
    16,
    "http://articles.last.year",
    "Yes",
    "http://waiver.policy",
    "LOCKSS, CLOCKSS", #, A national library, Other",
    "Trinity",
    "A safe place",
    "http://digital.archiving.policy",
    "Yes",
    "DOI, ARK, PURL",
    # "PURL",
    "Yes",
    "Yes",
    "http://download.stats",
    1980,
    "HTML, XML, Wordperfect",
    # "Wordperfect",
    "word, key",
    "EN, FR",
    "http://editorial.board",
    "Open peer review",
    "http://review.process",
    "http://aims.scope",
    "http://author.instructions.com",
    "Yes",
    "http://plagiarism.screening",
    8,
    "http://oa.statement",
    "Yes",
    "http://licence.embedded",
    # "Other",
    "CC MY",
    "Attribution, No Commercial Usage",
    "http://licence.url",
    "Yes",
    "Sherpa/Romeo, Store it",
    # "Store it",
    #"Other",
    "Sometimes",
    "http://copyright.com",
    #"Other",
    "Occasionally",
    "http://publishing.rights"
]

@classmethod
def mock_issns_by_owner(cls, *args, **kwargs):
    return ["1234-5678", "2345-6789", "3456-7890"]

@classmethod
def mock_find_by_issn(cls, *args, **kwargs):
    source = deepcopy(APPLICATION_SOURCE)
    source.update({"id" : uuid.uuid4().hex})
    return [models.Suggestion(**source)]

class TestReApplication(DoajTestCase):

    def setUp(self):
        super(TestReApplication, self).setUp()
        self._make_valid_csv()

        self.old_issns_by_owner = models.Journal.issns_by_owner
        models.Journal.issns_by_owner = mock_issns_by_owner

        self.old_find_by_issn = models.Suggestion.find_by_issn
        models.Suggestion.find_by_issn = mock_find_by_issn

    def tearDown(self):
        super(TestReApplication, self).tearDown()
        if os.path.exists("basic_reapp.csv") and os.path.isfile("basic_reapp.csv"):
            os.remove("basic_reapp.csv")
        if os.path.exists("full_reapp.csv") and os.path.isfile("full_reapp.csv"):
            os.remove("full_reapp.csv")
        if os.path.exists("valid.csv"):
            os.remove("valid.csv")

        models.Journal.issns_by_owner = self.old_issns_by_owner
        models.Suggestion.find_by_issn = self.old_find_by_issn

    def _make_valid_csv(self):
        sheet = ClCsv("valid.csv")

        # first column is the questions
        qs = reapplication.Suggestion2QuestionXwalk.question_list()
        sheet.set_column("", qs)

        # add 3 columns of results for testing purposes
        c1 = deepcopy(APPLICATION_COL)
        c1[0] = "First Title"
        c1[3] = "1234-5678"
        c1[4] = "9876-5432"
        sheet.set_column(c1[3], c1)

        c2 = deepcopy(APPLICATION_COL)
        c2[0] = "Second Title"
        c2[3] = "2345-6789"
        c2[4] = "8765-4321"
        sheet.set_column(c2[3], c2)

        c3 = deepcopy(APPLICATION_COL)
        c3[0] = "Third Title"
        c3[3] = "3456-7890"
        c3[4] = "7654-3210"
        sheet.set_column(c3[3], c3)

        sheet.save()

    def test_01_make_reapplication(self):
        # first make ourselves a journal with the key ingredients
        j = models.Journal()
        bj = j.bibjson()
        bj.title = "Journal Title"                      # some bibjson
        j.set_application_status("accepted")            # an application status of accepted
        j.add_note("An important note")                 # a note
        j.add_contact("Contact", "contact@email.com")   # contact details
        j.set_owner("theowner")                         # journal owner account
        j.set_editor_group("editorgroup")               # editorial group
        j.set_editor("associate")                       # assigned associate editor

        # save it so that it acquires an id, created_date, last_updated and an index record
        j.save()
        j.refresh()

        # now call to make the reapplication
        reapp = j.make_reapplication()
        rbj = reapp.bibjson()

        # now check that the reapplication has the properties we'd expect
        assert rbj.title == "Journal Title"
        assert reapp.id != j.id
        assert reapp.suggested_on is not None
        assert reapp.application_status == "reapplication"
        assert len(reapp.notes()) == 1
        assert len(reapp.contacts()) == 1
        assert reapp.owner == "theowner"
        assert reapp.editor_group == "editorgroup"
        assert reapp.editor == "associate"
        assert reapp.current_journal == j.id
        assert j.current_application == reapp.id
        assert reapp.created_date is not None
        assert reapp.last_updated is not None

    def test_02_make_csv_vbasic(self):
        s1 = models.Suggestion()
        bj1 = s1.bibjson()
        bj1.title = "The Title"
        bj1.add_identifier("eissn", "1245-5678")

        s2 = models.Suggestion()
        bj2 = s2.bibjson()
        bj2.title = "Second One"
        bj2.add_identifier("pissn", "9876-5432")

        reapplication.make_csv("basic_reapp.csv", [s1, s2])

        assert os.path.exists("basic_reapp.csv")

    def test_03_csv_xwalk_out(self):
        s1 = models.Suggestion(**deepcopy(APPLICATION_SOURCE))
        kvs = reapplication.Suggestion2QuestionXwalk.suggestion2question(s1)

        # don't bother to check the questions, their text may vary, and it will be a pain to keep in step with
        answers = [a for q, a in kvs]

        assert answers == APPLICATION_COL

    def test_04_make_csv_full(self):
        s1 = models.Suggestion(**deepcopy(APPLICATION_SOURCE))
        s2 = models.Suggestion(**deepcopy(APPLICATION_SOURCE))
        s3 = models.Suggestion(**deepcopy(APPLICATION_SOURCE))

        bj1 = s1.bibjson()
        bj1.remove_identifiers("pissn")
        bj1.remove_identifiers("eissn")
        bj1.add_identifier("pissn", "1234-5678")
        bj1.add_identifier("eissn", "9876-5432")
        bj1.title = "First Title"

        bj2 = s2.bibjson()
        bj2.remove_identifiers("pissn")
        bj2.remove_identifiers("eissn")
        bj2.add_identifier("pissn", "2345-6789")
        bj1.add_identifier("eissn", "9876-5431")
        bj2.title = "Second Title"

        bj3 = s3.bibjson()
        bj3.remove_identifiers("pissn")
        bj3.remove_identifiers("eissn")
        bj3.add_identifier("pissn", "3456-7890")
        bj1.add_identifier("eissn", "9876-5430")
        bj3.title = "Third Title"

        reapplication.make_csv("full_reapp.csv", [s3, s2, s1]) # send the suggestions in in the wrong order for display on purpose

        assert os.path.exists("full_reapp.csv")

        # now let's check a few things about the sheet to be sure
        sheet = clcsv.ClCsv("full_reapp.csv")

        # get the three columns out of the sheet
        issn1, vals1 = sheet.get_column(1)
        issn2, vals2 = sheet.get_column(2)
        issn3, vals3 = sheet.get_column(3)

        # check that the column headers are in the right order
        assert issn1 == "1234-5678"
        assert issn2 == "2345-6789"
        assert issn3 == "3456-7890"

        # check that the column contents are the right contents
        assert vals1[0] == "First Title"
        assert vals2[0] == "Second Title"
        assert vals3[0] == "Third Title"

        # finally check the full question list
        qs = reapplication.Suggestion2QuestionXwalk.question_list()
        _, sheetqs = sheet.get_column(0)

        assert sheetqs == qs

    def test_05_csv_xwalk_in(self):
        # convert the test answers into the form info
        forminfo_col = reapplication.Suggestion2QuestionXwalk.question2form(APPLICATION_COL)

        # convert the test object into form info
        s = models.Suggestion(**deepcopy(APPLICATION_SOURCE))
        forminfo_obj = xwalk.SuggestionFormXWalk.obj2form(s)

        # there are a bunch of fields in the object that come over to the form info that aren't in
        # the spreadsheet, so we need to remove them before we can compare
        del forminfo_obj["application_status"]
        del forminfo_obj["editor"]
        del forminfo_obj["editor_group"]
        del forminfo_obj["notes"]
        del forminfo_obj["subject"]
        del forminfo_obj["suggester_email"]
        del forminfo_obj["suggester_email_confirm"]
        del forminfo_obj["suggester_name"]
        del forminfo_obj["owner"]

        # these two objects should be the same
        assert forminfo_col == forminfo_obj

    def test_06_csv_xwalk_in_broken(self):
        # first try with too few questions
        col = deepcopy(APPLICATION_COL)
        col = col[30:] # just truncate the questions at a random point
        with self.assertRaises(reapplication.SuggestionXwalkException):
            forminfo = reapplication.Suggestion2QuestionXwalk.question2form(col)

        # now try with too many
        col = deepcopy(APPLICATION_COL)
        col.append("whatever")
        with self.assertRaises(reapplication.SuggestionXwalkException):
            forminfo = reapplication.Suggestion2QuestionXwalk.question2form(col)


    def test_07_csv_xwalk_in_advanced(self):
        # make an application with correct but oddly and variably entered data
        col = deepcopy(APPLICATION_COL)
        col[0] = "    The   Title   "               # title
        col[11] = " united   kingdom    "           # country
        col[12] = "  YEs "                          # processing charges
        col[14] = " gbp   "                         # processing_charges_currency
        col[15] = "nO "                             # submission charges
        col[17] = " pound  sterling"                # submission_charges_currency
        col[20] = " whatever "                      # waiver_policy
        col[22] = "  LOCKSS, A national library, Store it  "  # digital_archiving_policy
        col[23] = "Dublin"                          # digital_archiving_policy_library
        col[24] = "  Behind the sofa"               # digital_archiving_policy_other
        col[27] = "DOI, ARK, PURL, Flag, Other"     # article_identifiers and article_identifiers_other (with unnecessary "Other" entry)
        col[32] = "PDF, XML, Wordperfect, TeX"      # fulltext_format and fulltext_format_other
        col[33] = "a, long, list, of, keywords, more, than, six"    # keywords
        col[34] = "en, FR,  Vietnamese , Wibble"    # languages
        col[36] = "edITORial   review   "           # review_process
        col[46] = "CC BY"                           # license and license_other
        col[47] = "BY, Share Alike, Whatever"       # license_checkbox
        col[50] = "Sherpa/Romeo, Under desk, over there"    # deposit_policy and deposit_policy_other
        col[51] = "Now and again"                   # copyright
        col[53] = "almost never"                    # publishing rights


        # run the xwalk and see that it produces what we expect
        forminfo = reapplication.Suggestion2QuestionXwalk.question2form(col)
        assert forminfo.get("title") == "The Title"
        assert forminfo.get("country") == "GB"
        assert forminfo.get("processing_charges") == "True"
        assert forminfo.get("processing_charges_currency") == "GBP"
        assert forminfo.get("submission_charges") == "False"
        assert forminfo.get("submission_charges_currency") == "GBP"
        assert forminfo.get("waiver_policy") == "whatever"      # we want this to come through as is - it will then fail validation later
        assert forminfo.get("digital_archiving_policy") == ["LOCKSS", "A national library", "Other"]
        assert forminfo.get("digital_archiving_policy_library") == "Dublin"
        assert forminfo.get("digital_archiving_policy_other") == "Store it, Behind the sofa"
        assert forminfo.get("article_identifiers") == ["DOI", "ARK", "Other"]
        assert forminfo.get("article_identifiers_other") == "PURL, Flag"
        assert forminfo.get("fulltext_format") == ["PDF", "XML", "Other"]
        assert forminfo.get("fulltext_format_other") == "Wordperfect, TeX"
        assert forminfo.get("languages") == ["EN", "FR", "VI", "Wibble"]
        assert forminfo.get("review_process") == "Editorial review"
        assert forminfo.get("license") == "CC BY"
        assert forminfo.get("license_other") == ""
        assert forminfo.get("license_checkbox") == ["BY", "SA", "Whatever"]
        assert forminfo.get("deposit_policy") == ["Sherpa/Romeo", "Other"]
        assert forminfo.get("deposit_policy_other") == "Under desk, over there"
        assert forminfo.get("copyright") == "Other"
        assert forminfo.get("copyright_other") == "Now and again"
        assert forminfo.get("publishing_rights") == "Other"
        assert forminfo.get("publishing_rights_other") == "almost never"
        assert forminfo.get("keywords") == ["a", "long", "list", "of", "keywords", "more", "than", "six"]

        # run the data into the form and validate it, to check we get the validation errors we expect
        form = forms.PublisherReApplicationForm(data=forminfo)
        form.validate()

        print form.errors
        error_fields = form.errors.keys()
        assert len(error_fields) == 4
        assert "waiver_policy" in error_fields
        assert "languages" in error_fields
        assert "license_checkbox" in error_fields
        assert "keywords" in error_fields

    def test_08_ingest_csv_success(self):
        account = models.Account(**{"id" : "Owner"})
        try:
            reapplication.ingest_csv("valid.csv", account)
        except reapplication.ContentValidationException:
            assert False
        except reapplication.CsvValidationException:
            assert False

        # give the index a chance to catch up
        time.sleep(2)

        # now test that all the reapplications got made
        reapps = models.Suggestion.get_by_owner("Owner")
        assert len(reapps) == 3
        for reapp in reapps:
            assert reapp.application_status == "submitted"
            assert reapp.bibjson().title in ["First Title", "Second Title", "Third Title"]

    def test_09_ingest_upload_success(self):
        upload = models.BulkUpload()
        upload.status = "incoming"
        upload.local_filename = "valid"
        upload.filename = "mybulkreapp.csv"
        upload.owner = "Owner"

        reapplication.ingest_from_upload(upload)
