from doajtest.helpers import DoajTestCase
from portality.clcsv import ClCsv
from portality import reapplication
from copy import deepcopy
import os

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

    def tearDown(self):
        super(TestReAppCsv, self).tearDown()
        if os.path.exists("valid.csv"):
            os.remove("valid.csv")
        if os.path.exists("random_binary"):
            os.remove("random_binary")

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

    def _random_binary(self):
        with open('random_binary', 'wb') as fout:
            fout.write(os.urandom(1024))

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
        pass

    def test_03_contents(self):
        pass
