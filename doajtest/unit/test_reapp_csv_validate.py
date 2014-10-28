from doajtest.helpers import DoajTestCase
from portality.clcsv import ClCsv
from portality import reapplication, models
from copy import deepcopy
import os, csv

@classmethod
def mock_issns_by_owner(cls, *args, **kwargs):
    return ["1234-5678", "2345-6789", "3456-7890"]

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
    "LOCKSS, CLOCKSS, A national library, Other",
    "Trinity",
    "A safe place",
    "http://digital.archiving.policy",
    "Yes",
    "DOI, ARK, Other",
    "PURL",
    "Yes",
    "Yes",
    "http://download.stats",
    1980,
    "HTML, XML, Other",
    "Wordperfect",
    "word, key",
    "EN, FR",
    "http://editorial.board",
    "Open peer review",
    "http://review.process",
    "http://aims.scope",
    "http://author.instructions",
    "Yes",
    "http://plagiarism.screening",
    8,
    "http://oa.statement",
    "Yes",
    "http://licence.embedded",
    "Other",
    "CC MY",
    "BY, NC",
    "http://licence.url",
    "Yes",
    "Sherpa/Romeo, Other",
    "Store it",
    "Other",
    "Sometimes",
    "http://copyright",
    "Other",
    "Occasionally",
    "http://publishing.rights"
]

class TestReAppCsv(DoajTestCase):

    def setUp(self):
        super(TestReAppCsv, self).setUp()
        self._make_valid_csv()
        self._random_binary()
        self._empty_sheet()
        self._wrong_questions()
        self._duplicate_issns()
        self.old_issns_by_owner = models.Journal.issns_by_owner
        models.Journal.issns_by_owner = mock_issns_by_owner

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
        models.Journal.issns_by_owner = self.old_issns_by_owner

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
                writer.writerow([q, "", ""])

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

    def test_03_contents(self):
        pass
