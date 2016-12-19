from doajtest.helpers import DoajTestCase
from portality import models, reapplication, clcsv
import os, time, uuid
from doajtest.fixtures import ApplicationFixtureFactory
from copy import deepcopy
from portality.formcontext import xwalk, forms
from portality.clcsv import ClCsv

REAPP1_SOURCE = ApplicationFixtureFactory.make_reapp_source()
REAPP2_UNICODE_SOURCE = ApplicationFixtureFactory.make_reapp_unicode_source()


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
        "replaces" : ["1111-1111"],
        "is_replaced_by" : ["2222-2222"],
        "discontinued_date" : "2001-01-01",
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
        "archiving_policy": {
            "known" : ["LOCKSS", "CLOCKSS"],
            "other" : "A safe place",
            "nat_lib" : "Trinity",
            "url": "http://digital.archiving.policy"
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
            "url" : "http://copyright.com"
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
        "seal" : False,
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
    "http://apc.com",
    2,
    "GBP",
    "Yes",
    "http://submission.com",
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
    "True",
    "http://copyright.com",
    #"Other",
    "True",
    "http://publishing.rights"
]

@classmethod
def mock_issns_by_owner(cls, *args, **kwargs):
    issns = ["1234-5678", "2345-6789", "3456-7890", "4567-8901"]
    for c_num in range(5, 80):
        c_num = str(c_num)
        issn = "6529-540" if len(c_num) == 1 else "6529-54"
        issn += c_num
        issns.append(issn)
    return issns

@classmethod
def mock_find_by_issn(cls, *args, **kwargs):
    source = deepcopy(APPLICATION_SOURCE)
    source.update({"id" : uuid.uuid4().hex})
    return [models.Suggestion(**source)]

@classmethod
def mock_account_pull(cls, username, *arsg, **kwargs):
    if username == "none":
        return None
    return models.Account(**{"id" : username, "email" : "richard@cottagelabs.com"})

class TestReApplication(DoajTestCase):

    def setUp(self):
        super(TestReApplication, self).setUp()
        self._make_valid_csv()
        self._wrong_questions()
        self._invalid_content()

        self.old_issns_by_owner = models.Journal.issns_by_owner
        models.Journal.issns_by_owner = mock_issns_by_owner

        self.old_find_by_issn = models.Suggestion.find_by_issn
        models.Suggestion.find_by_issn = mock_find_by_issn

        self.old_account_pull = models.Account.pull
        models.Account.pull = mock_account_pull

        self.old_reapp_upload_dir = self.app_test.config.get("REAPPLICATION_UPLOAD_DIR")
        self.app_test.config["REAPPLICATION_UPLOAD_DIR"] = os.path.dirname(os.path.realpath(__file__))

    def tearDown(self):
        super(TestReApplication, self).tearDown()
        if os.path.exists("basic_reapp.csv") and os.path.isfile("basic_reapp.csv"):
            os.remove("basic_reapp.csv")
        if os.path.exists("full_app.csv") and os.path.isfile("full_app.csv"):
            os.remove("full_app.csv")
        if os.path.exists("full_reapp.csv") and os.path.isfile("full_reapp.csv"):
            os.remove("full_reapp.csv")
        if os.path.exists("full_reapp_unicode.csv") and os.path.isfile("full_reapp_unicode.csv"):
            os.remove("full_reapp_unicode.csv")
        if os.path.exists("valid.csv"):
            os.remove("valid.csv")
        if os.path.exists("wrong_questions.csv"):
            os.remove("wrong_questions.csv")
        if os.path.exists("invalid.csv"):
            os.remove("invalid.csv")

        models.Journal.issns_by_owner = self.old_issns_by_owner
        models.Suggestion.find_by_issn = self.old_find_by_issn
        models.Account.pull = self.old_account_pull

        self.app_test.config["REAPPLICATION_UPLOAD_DIR"] = self.old_reapp_upload_dir

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

    def _wrong_questions(self):
        sheet = ClCsv("wrong_questions.csv")
        sheet.set_column("", ["Q" + str(i) for i in range(56)])
        c1 = deepcopy(APPLICATION_COL)
        c1[0] = "First Title"
        c1[3] = "1234-5678"
        c1[4] = "9876-5432"
        sheet.set_column(c1[3], c1)
        sheet.save()

    def _invalid_content(self):
        sheet = ClCsv("invalid.csv")

        # first column is the questions
        qs = reapplication.Suggestion2QuestionXwalk.question_list()
        sheet.set_column("", qs)

        # add 3 columns of results for testing purposes
        c1 = deepcopy(APPLICATION_COL)
        c1[0] = "First Title"
        c1[1] = "This isn't a URL (but it should be)"
        c1[3] = "1234-5678"
        c1[4] = "9876-5432"
        sheet.set_column(c1[3], c1)

        c2 = deepcopy(APPLICATION_COL)
        c2[0] = "Second Title"
        c2[3] = "2345-6789"
        c2[4] = "8765-4321"
        c2[11] = "" # This field is required (country)
        sheet.set_column(c2[3], c2)

        c3 = deepcopy(APPLICATION_COL)
        c3[0] = "Third Title"
        c3[3] = "3456-7890"
        c3[4] = "7654-3210"
        sheet.set_column(c3[3], c3)

        c4 = deepcopy(APPLICATION_COL)
        c4[0] = "Fourth Title"
        c4[3] = "4567-8901"
        c4[4] = "6543-2109"
        c4[54] = "invalid url"
        sheet.set_column(c4[3], c4)

        for c_num in range(5, 80):  # columns 1-4 are defined already, and we need, say, 26 * 3 columns for test 16 (so we can comfortably pick one from the middle and have it be > 27th column), so roughly 78, so why not 79?
            c_num = str(c_num)
            col = deepcopy(APPLICATION_COL)
            col[0] = c_num + " Title"
            col[3] = "6529-540" if len(c_num) == 1 else "6529-54"
            col[3] += c_num
            col[54] = "invalid url"
            sheet.set_column(col[3], col)

        sheet.save()

    def test_01_make_reapplication(self):
        # first make ourselves a journal with the key ingredients
        j = models.Journal()
        bj = j.bibjson()
        bj.title = "Journal Title"                      # some bibjson
        j.add_note("An important note")                 # a note
        j.add_contact("Contact", "contact@email.com")   # contact details
        j.set_owner("theowner")                         # journal owner account
        j.set_editor_group("editorgroup")               # editorial group
        j.set_editor("associate")                       # assigned associate editor
        bj.add_language("ES")

        # save it so that it acquires an id, created_date, last_updated and an index record
        j.save()
        j.refresh()

        # now call to make the reapplication
        reapp = j.make_reapplication()
        rbj = reapp.bibjson()

        # now check that the reapplication has the properties we'd expect
        assert reapp.contacts()[0].get("name") == "Contact"
        assert reapp.contacts()[0].get("email") == "contact@email.com"
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
        assert reapp.suggester.get("name") == "Contact"
        assert reapp.suggester.get("email") == "contact@email.com"

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
        bj1.add_language("ES")
        bj1.add_language("Spanish") # which is not allowed, you know!  (should be "Spanish; Castillian")

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

        reapplication.make_csv("full_app.csv", [s3, s2, s1]) # send the suggestions in in the wrong order for display on purpose

        assert os.path.exists("full_app.csv")

        # now let's check a few things about the sheet to be sure
        sheet = clcsv.ClCsv("full_app.csv")

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

        # check that the disallowed language got stripped
        assert "Spanish" not in vals1[34]

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
        del forminfo_obj["doaj_seal"]
        del forminfo_obj["replaces"]
        del forminfo_obj["is_replaced_by"]
        del forminfo_obj["discontinued_date"]

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
        col[15] = " gbp   "                         # processing_charges_currency
        col[16] = "nO "                             # submission charges
        col[19] = " pound  sterling"                # submission_charges_currency
        col[22] = " whatever "                      # waiver_policy
        col[24] = "  LOCKSS, A national library, Store it  "  # digital_archiving_policy
        col[25] = "Dublin"                          # digital_archiving_policy_library
        col[26] = "  Behind the sofa"               # digital_archiving_policy_other
        col[29] = "DOI, ARK, PURL, Flag, Other"     # article_identifiers and article_identifiers_other (with unnecessary "Other" entry)
        col[34] = "PDF, XML, Wordperfect, TeX"      # fulltext_format and fulltext_format_other
        col[35] = "a, long, list, of, keywords, more, than, six"    # keywords
        col[36] = "en, FR,  Vietnamese , Wibble"    # languages
        col[38] = "edITORial   review   "           # review_process
        col[48] = "CC BY"                           # license and license_other
        col[49] = "BY, Share Alike, Whatever"       # license_checkbox
        col[52] = "Sherpa/Romeo, Under desk, over there"    # deposit_policy and deposit_policy_other
        col[53] = "True"                   # copyright
        col[55] = "True"                    # publishing rights


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
        assert forminfo.get("copyright") == "True"
        assert forminfo.get("publishing_rights") == "True", forminfo.get("publishing_rights")
        assert forminfo.get("keywords") == ["a", "long", "list", "of", "keywords", "more", "than", "six"]

        # run the data into the form and validate it, to check we get the validation errors we expect
        form = forms.PublisherReApplicationForm(data=forminfo)
        form.validate()

        error_fields = form.errors.keys()
        assert len(error_fields) == 4
        assert "waiver_policy" in error_fields
        assert "languages" in error_fields
        assert "license_checkbox" in error_fields
        assert "keywords" in error_fields

    def test_08_ingest_csv_success(self):
        account = models.Account(**{"id" : "Owner"})
        try:
            result = reapplication.ingest_csv("valid.csv", account)
            assert result["reapplied"] == 3
            assert result["skipped"] == 0
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
        upload.upload("Owner", "mybulkreapp.csv")
        upload.set_id("valid")

        reapplication.ingest_from_upload(upload)

    def test_10_ingest_upload_broke(self):
        # no account
        upload = models.BulkUpload()
        upload.upload("none", "mybulkreapp.csv")
        upload.set_id("valid")
        with self.assertRaises(reapplication.CsvIngestException):
            reapplication.ingest_from_upload(upload)

        # structural problem
        upload = models.BulkUpload()
        upload.upload("Owner", "mybulkreapp.csv")
        upload.set_id("wrong_questions")
        reapplication.ingest_from_upload(upload)
        assert upload.status == "failed"
        assert upload.error is not None

        # content problem
        upload = models.BulkUpload()
        upload.upload("Owner", "mybulkreapp.csv")
        upload.set_id("invalid")
        reapplication.ingest_from_upload(upload)
        assert upload.status == "failed"
        assert upload.error is not None

    def test_11_generate_error_report(self):
        account = models.Account(**{"id" : "Owner"})

        # provide our own callback to check the report generation
        def callback(report):
            assert report is not None
            assert "1234-5678" in report
            assert "C13" in report

        with self.assertRaises(reapplication.ContentValidationException):
            reapplication.ingest_csv("invalid.csv", account, callback)

        # this will use the default callback, which will try to send me an email
        upload = models.BulkUpload()
        upload.upload("Owner", "mybulkreapp.csv")
        upload.set_id("invalid")
        upload.save()
        reapplication.ingest_from_upload(upload)

    def test_12_make_csv_reapp(self):
        s1 = models.Suggestion(**deepcopy(REAPP1_SOURCE))

        reapplication.make_csv("full_reapp.csv", [s1])

        assert os.path.exists("full_reapp.csv")

        # now let's check a few things about the sheet to be sure
        sheet = clcsv.ClCsv("full_reapp.csv")

        # get the three columns out of the sheet
        issn1, vals1 = sheet.get_column(1)

        # check that the column headers are in the right order
        assert issn1 == "1234-5678"

        # check that the column contents are the right contents
        assert vals1[0] == "The Title"

        # finally check the full question list
        qs = reapplication.Suggestion2QuestionXwalk.question_list()
        _, sheetqs = sheet.get_column(0)

        assert sheetqs == qs

    def test_13_make_csv_reapp_unicode(self):
        s1 = models.Suggestion(**deepcopy(REAPP2_UNICODE_SOURCE))

        reapplication.make_csv("full_reapp_unicode.csv", [s1])

        assert os.path.exists("full_reapp_unicode.csv")

        # now let's check a few things about the sheet to be sure
        sheet = clcsv.ClCsv("full_reapp_unicode.csv")

        # get the three columns out of the sheet
        issn1, vals1 = sheet.get_column(1)

        # check that the column headers are in the right order
        assert issn1 == "1234-5678"

        # check that the column contents are the right contents
        assert vals1[0] == "The Title"

        # finally check the full question list
        qs = reapplication.Suggestion2QuestionXwalk.question_list()
        _, sheetqs = sheet.get_column(0)

        assert sheetqs == qs

    def test_14_make_journal_from_reapp(self):
        j = models.Journal()
        j.set_id("1234567")
        j.set_created("2001-01-01T00:00:00Z")
        j.save()

        s = models.Suggestion(**ApplicationFixtureFactory.make_application_source())
        s.set_current_journal("1234567")

        time.sleep(1)
        j = s.make_journal()
        j.save()

        assert j.id == "1234567"
        assert "suggestion" not in j.data
        assert j.last_reapplication is not None
        assert j.data.get("bibjson", {}).get("active")
        assert j.current_application is None
        assert j.data.get("admin", {}).get("current_journal") is None
        assert j.created_date == "2001-01-01T00:00:00Z"

        # without history
        j = models.Journal()
        j.set_id("1234567")
        j.set_created("2001-01-01T00:00:00Z")
        j.save()

        s = models.Suggestion(**ApplicationFixtureFactory.make_application_source())
        s.set_current_journal("1234567")

        time.sleep(1)
        j = s.make_journal()
        j.save()

        assert j.id == "1234567"
        assert "suggestion" not in j.data
        assert j.last_reapplication is not None
        assert j.data.get("bibjson", {}).get("active")
        assert j.current_application is None
        assert j.data.get("admin", {}).get("current_journal") is None
        assert j.created_date == "2001-01-01T00:00:00Z"

    def test_15_error_report_cell_refs_rows(self):
        sheet = reapplication.open_csv("invalid.csv")

        with self.assertRaises(reapplication.ContentValidationException):
            try:
                fcs, skip = reapplication.validate_csv_contents(sheet)
            except reapplication.ContentValidationException as e:
                report = reapplication.generate_spreadsheet_error_object(sheet, e)

                assert report["4567-8901"].has_key(56), report["4567-8901"]
                assert report["4567-8901"][56] == (
                            "4567-8901",
                            "53) Enter the URL where this information can be found **",
                            56,
                            "E",
                            "Invalid URL."
                       ), report["4567-8901"][56]
                raise e

    def test_16_error_report_cell_refs_columns(self):
        sheet = reapplication.open_csv("invalid.csv")

        with self.assertRaises(reapplication.ContentValidationException):
            try:
                fcs, skip = reapplication.validate_csv_contents(sheet)
            except reapplication.ContentValidationException as e:
                report = reapplication.generate_spreadsheet_error_object(sheet, e)

                assert report["6529-5440"].has_key(56), report["6529-5440"]
                assert report["6529-5440"][56] == (
                            "6529-5440",
                            "53) Enter the URL where this information can be found **",
                            56,
                            "AO",  # the 41st column should be AO. AA is the 27th, AO is 14 after that (O is the 15th letter in the alphabet)
                            "Invalid URL."
                       ), report["6529-5440"][56]
                raise e

    def test_17_num2col(self):
        assert reapplication.num2col(0) == 'A', reapplication.num2col(0)
        assert reapplication.num2col(1) == 'B', reapplication.num2col(1)
        assert reapplication.num2col(26) == 'AA', reapplication.num2col(26)
        assert reapplication.num2col(40) == 'AO', reapplication.num2col(40)
        assert reapplication.num2col(18277) == 'ZZZ', reapplication.num2col(18277)
        assert reapplication.num2col(18278) == 'AAAA', reapplication.num2col(18278)
