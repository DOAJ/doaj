from doajtest.helpers import DoajTestCase
from portality import models
import os, time, uuid
from doajtest.fixtures import ApplicationFixtureFactory
from copy import deepcopy

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

        self.old_issns_by_owner = models.Journal.issns_by_owner
        models.Journal.issns_by_owner = mock_issns_by_owner

        self.old_find_by_issn = models.Suggestion.find_by_issn
        models.Suggestion.find_by_issn = mock_find_by_issn

        self.old_account_pull = models.Account.pull
        models.Account.pull = mock_account_pull

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
        assert len(reapp.notes) == 1
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

