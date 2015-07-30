from doajtest.helpers import DoajTestCase
from portality import models
from datetime import datetime
from doajtest.fixtures import ApplicationFixtureFactory, JournalFixtureFactory, ArticleFixtureFactory
import time

class TestClient(DoajTestCase):

    def test_01_imports(self):
        """import all of the model objects successfully?"""
        from portality.models import Account
        from portality.models import Article, ArticleBibJSON, ArticleQuery, ArticleVolumesQuery, DuplicateArticleQuery
        from portality.models import AtomRecord
        from portality.models import GenericBibJSON
        from portality.models import Cache
        from portality.models import EditorGroupQuery, EditorGroup, EditorGroupMemberQuery
        from portality.models import ArticleHistory, ArticleHistoryQuery, JournalHistory, JournalHistoryQuery
        from portality.models import IssnQuery, Journal, JournalBibJSON, JournalQuery, PublisherQuery, TitleQuery
        from portality.models import LCC
        from portality.models import Lock
        from portality.models import OAIPMHArticle, OAIPMHJournal, OAIPMHRecord
        from portality.models import JournalArticle, JournalArticleQuery
        from portality.models import Suggestion, SuggestionQuery
        from portality.models import JournalIssueToC, JournalVolumeToC, ToCQuery, VolumesToCQuery
        from portality.models import ExistsFileQuery, FileUpload, OwnerFileQuery, ValidFileQuery
        from portality.models import ObjectDict
        from portality.models import BulkUpload, BulkReApplication, OwnerBulkQuery

        j = models.lookup_model("journal")
        ja = models.lookup_model("journal_article")

        assert j.__type__ == "journal"
        assert ja.__type__ == "journal,article"

    def test_02_journal_model_rw(self):
        """Read and write properties into the journal model"""
        j = models.Journal()
        j.set_current_application("1234567")
        j.set_last_reapplication("2001-04-19T01:01:01Z")
        j.set_bulk_upload_id("abcdef")

        assert j.data.get("admin", {}).get("current_application") == "1234567"
        assert j.current_application == "1234567"
        assert j.last_reapplication == "2001-04-19T01:01:01Z"
        assert j.bulk_upload_id == "abcdef"

        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        j.set_last_reapplication()
        assert j.last_reapplication == now # should work, since this ought to take less than a second, but it might sometimes fail

    def test_03_suggestion_model_rw(self):
        """Read and write properties into the suggestion model"""
        s = models.Suggestion()
        s.set_current_journal("9876543")
        s.set_bulk_upload_id("abcdef")

        assert s.data.get("admin", {}).get("current_journal") == "9876543"
        assert s.current_journal == "9876543"
        assert s.bulk_upload_id == "abcdef"

    def test_04_bulk_reapplication_rw(self):
        """Read and write properties into the BulkReapplication Model"""
        br = models.BulkReApplication()
        br.set_owner("richard")
        br.set_spreadsheet_name("richard.csv")

        assert br.owner == "richard"
        assert br.spreadsheet_name == "richard.csv"

    def test_05_bulk_upload(self):
        """Read and write properties into the BulkUpload model"""
        br = models.BulkUpload()
        br.upload("richard", "reapplication.csv")

        assert br.owner == "richard"
        assert br.filename == "reapplication.csv"
        assert br.status == "incoming"

        br.failed("Broke, innit")

        assert br.status == "failed"
        assert br.error == "Broke, innit"
        assert br.processed_date is not None
        assert br.processed_timestamp is not None

        br.processed(10, 5)

        assert br.status == "processed"
        assert br.reapplied == 10
        assert br.skipped == 5
        assert br.processed_date is not None
        assert br.processed_timestamp is not None

    def test_06_make_journal(self):
        s = models.Suggestion(**ApplicationFixtureFactory.make_application_source())
        j = s.make_journal()

        assert j.id != s.id
        assert "suggestion" not in j.data
        assert j.data.get("bibjson", {}).get("active")

    def test_07_sync_owners(self):
        # suggestion with no current_journal
        s = models.Suggestion(**ApplicationFixtureFactory.make_application_source())
        s.save()

        models.Suggestion.refresh()
        s = models.Suggestion.pull(s.id)
        assert s is not None

        # journal with no current_application
        j = models.Journal(**JournalFixtureFactory.make_journal_source())
        j.save()

        models.Journal.refresh()
        j = models.Journal.pull(j.id)
        assert j is not None

        # suggestion with erroneous current_journal
        s.set_current_journal("asdklfjsadjhflasdfoasf")
        s.save()

        models.Suggestion.refresh()
        s = models.Suggestion.pull(s.id)
        assert s is not None

        # journal with erroneous current_application
        j.set_current_application("kjwfuiwqhu220952gw")
        j.save()

        models.Journal.refresh()
        j = models.Journal.pull(j.id)
        assert j is not None

        # suggestion with journal
        s.set_owner("my_new_owner")
        s.set_current_journal(j.id)
        s.save()

        models.Journal.refresh()
        j = models.Journal.pull(j.id)
        assert j.owner == "my_new_owner"

        # journal with suggestion
        j.set_owner("another_new_owner")
        j.set_current_application(s.id)
        j.save()

        models.Suggestion.refresh()
        s = models.Suggestion.pull(s.id)
        assert s.owner == "another_new_owner"

    def test_08_iterate(self):
        for jsrc in JournalFixtureFactory.make_many_journal_sources(count=99, in_doaj=True):
            j = models.Journal(**jsrc)
            j.save()
        time.sleep(1) # index all the journals
        journal_ids = []
        theqgen = models.JournalQuery()
        for j in models.Journal.iterate(q=theqgen.all_in_doaj(), page_size=10):
            journal_ids.append(j.id)
        journal_ids = list(set(journal_ids[:]))  # keep only unique ids
        assert len(journal_ids) == 99