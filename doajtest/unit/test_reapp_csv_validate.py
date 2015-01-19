from doajtest.helpers import DoajTestCase
from portality.clcsv import ClCsv
from portality import reapplication, models
from copy import deepcopy
import os, csv

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
    "BY, NC",
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
    return [models.Suggestion(**APPLICATION_SOURCE)]

@classmethod
def dont_find_by_issn(cls, *args, **kwargs):
    return []

@classmethod
def find_many_by_issn(cls, *args, **kwargs):
    return [models.Suggestion(**APPLICATION_SOURCE), models.Suggestion(**APPLICATION_SOURCE)]

@classmethod
def find_conditional_by_issn(cls, *args, **kwargs):
    source = deepcopy(APPLICATION_SOURCE)
    del source["admin"]["contact"][0]["email"]
    return [models.Suggestion(**source)]

class TestReAppCsv(DoajTestCase):

    def setUp(self):
        super(TestReAppCsv, self).setUp()

        self._make_valid_csv()
        self._random_binary()
        self._empty_sheet()
        self._wrong_questions()
        self._duplicate_issns()
        self._wrong_issn()
        self._invalid_content()

        self.old_issns_by_owner = models.Journal.issns_by_owner
        models.Journal.issns_by_owner = mock_issns_by_owner

        self.old_find_by_issn = models.Suggestion.find_by_issn
        models.Suggestion.find_by_issn = mock_find_by_issn

    def tearDown(self):
        super(TestReAppCsv, self).tearDown()

        if os.path.exists("valid.csv"):
            os.remove("valid.csv")
        if os.path.exists("random_binary"):
            os.remove("random_binary")
        if os.path.exists("empty.csv"):
            os.remove("empty.csv")
        if os.path.exists("wrong_questions.csv"):
            os.remove("wrong_questions.csv")
        if os.path.exists("duplicate_issns.csv"):
            os.remove("duplicate_issns.csv")
        if os.path.exists("wrong_issn.csv"):
            os.remove("wrong_issn.csv")
        if os.path.exists("invalid.csv"):
            os.remove("invalid.csv")

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

    def _wrong_issn(self):
        sheet = ClCsv("wrong_issn.csv")
        qs = reapplication.Suggestion2QuestionXwalk.question_list()
        sheet.set_column("", qs)

        c1 = deepcopy(APPLICATION_COL)
        c1[0] = "First Title"
        c1[3] = "6754-0000"
        c1[4] = "8776-0998"
        sheet.set_column(c1[3], c1)
        sheet.save()

    def _random_binary(self):
        with open('random_binary', 'wb') as fout:
            fout.write(os.urandom(1024))

    def _empty_sheet(self):
        with open("empty.csv", "wb") as fout:
            fout.write("")

    def _duplicate_issns(self):
        # this one is tricky - the csv library won't allow us to write a broken csv, so we have to manually build it
        qs = reapplication.Suggestion2QuestionXwalk.question_list()
        with open("duplicate_issns.csv", "wb") as f:
            writer = csv.writer(f)
            writer.writerow(["", "1234-5678", "1234-5678", "1234-5678"])
            for q in qs:
                writer.writerow([q, "", "", ""])

    def test_01_open_csv(self):
        # first try a valid csv
        sheet = reapplication.open_csv("valid.csv")
        assert sheet is not None

        headers = sheet.headers()
        assert headers == ["", "1234-5678", "2345-6789", "3456-7890"], headers

        # now try one that won't parse
        with self.assertRaises(reapplication.CsvValidationException):
            sheet = reapplication.open_csv("random_binary")

    def test_02_structure(self):
        account = models.Account(**{"id" : "12345"})

        # first try a valid csv
        sheet = reapplication.open_csv("valid.csv")
        reapplication.validate_csv_structure(sheet, account)

        # now try one without any content
        sheet = reapplication.open_csv("empty.csv")
        with self.assertRaises(reapplication.CsvValidationException):
            try:
                reapplication.validate_csv_structure(sheet, account)
            except reapplication.CsvValidationException as e:
                assert e.message == "Could not retrieve any content from the CSV; spreadsheet is invalid"
                raise e

        # now try one with the wrong questions
        sheet = reapplication.open_csv("wrong_questions.csv")
        with self.assertRaises(reapplication.CsvValidationException):
            try:
                reapplication.validate_csv_structure(sheet, account)
            except reapplication.CsvValidationException as e:
                assert e.message == "The list of questions in the csv has been modified; spreadsheet is invalid"
                raise e

        # now try one with duplicated issns
        sheet = reapplication.open_csv("duplicate_issns.csv")
        with self.assertRaises(reapplication.CsvValidationException):
            try:
                reapplication.validate_csv_structure(sheet, account)
            except reapplication.CsvValidationException as e:
                assert e.message == "There were one or more repeated ISSNs in the csv header row; spreadsheet is invalid"
                raise e

        # now try one with incorrect issns
        sheet = reapplication.open_csv("wrong_issn.csv")
        with self.assertRaises(reapplication.CsvValidationException):
            try:
                reapplication.validate_csv_structure(sheet, account)
            except reapplication.CsvValidationException as e:
                assert e.message == "The ISSN 6754-0000 is not owned by this user account; spreadsheet is invalid"
                raise e

    def test_03_contents(self):
        # first try a valid csv
        sheet = reapplication.open_csv("valid.csv")
        fcs, skip = reapplication.validate_csv_contents(sheet)
        assert len(fcs) == 3
        assert len(skip) == 0

        # check that we can't validate something with an issn we don't recognise
        sheet = reapplication.open_csv("valid.csv")
        models.Suggestion.find_by_issn = dont_find_by_issn
        with self.assertRaises(reapplication.CsvValidationException):
            try:
                fcs = reapplication.validate_csv_contents(sheet)
            except reapplication.CsvValidationException as e:
                assert e.message == "Unable to locate a reapplication with the issn 1234-5678; spreadsheet is invalid"
                raise e

        sheet = reapplication.open_csv("valid.csv")
        models.Suggestion.find_by_issn = find_many_by_issn
        with self.assertRaises(reapplication.CsvValidationException):
            try:
                fcs = reapplication.validate_csv_contents(sheet)
            except reapplication.CsvValidationException as e:
                assert e.message == "Unable to locate a unique reapplication with the issn 1234-5678; please contact an administrator"
                raise e

        sheet = reapplication.open_csv("invalid.csv")
        models.Suggestion.find_by_issn = mock_find_by_issn
        with self.assertRaises(reapplication.ContentValidationException):
            try:
                fcs = reapplication.validate_csv_contents(sheet)
            except reapplication.ContentValidationException as e:
                assert e.message == "One or more records in the CSV failed to validate"
                assert len(e.errors.keys()) == 2
                assert "1234-5678" in e.errors.keys()
                assert "2345-6789" in e.errors.keys()
                assert e.errors["1234-5678"].form.errors.keys() == ["url"]
                assert e.errors["2345-6789"].form.errors.keys() == ["country"]
                raise e

    def test_04_conditional_fields(self):
        sheet = reapplication.open_csv("valid.csv")
        models.Suggestion.find_by_issn = find_conditional_by_issn
        fcs, skip = reapplication.validate_csv_contents(sheet)
        assert len(fcs) == 3
        assert len(skip) == 0
