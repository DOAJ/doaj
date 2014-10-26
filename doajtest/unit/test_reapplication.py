from doajtest.helpers import DoajTestCase
from portality import models, reapplication, clcsv
import os
from copy import deepcopy

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

class TestReApplication(DoajTestCase):

    def setUp(self):
        super(TestReApplication, self).setUp()

    def tearDown(self):
        super(TestReApplication, self).tearDown()
        if os.path.exists("basic_reapp.csv") and os.path.isfile("basic_reapp.csv"):
            os.remove("basic_reapp.csv")
        if os.path.exists("full_reapp.csv") and os.path.isfile("full_reapp.csv"):
            os.remove("full_reapp.csv")

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

    def test_03_csv_xwalk(self):
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
        bj1.title = "First Title"

        bj2 = s2.bibjson()
        bj2.remove_identifiers("pissn")
        bj2.remove_identifiers("eissn")
        bj2.add_identifier("pissn", "2345-6789")
        bj2.title = "Second Title"

        bj3 = s3.bibjson()
        bj3.remove_identifiers("pissn")
        bj3.remove_identifiers("eissn")
        bj3.add_identifier("pissn", "3456-7890")
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