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
        from portality.models import ArticleHistory, JournalHistory
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

    def test_03_article_model_rw(self):
            """Read and write properties into the article model"""
            a = models.Article()
            assert not a.is_in_doaj()

            a.set_in_doaj(True)
            a.set_publisher_record_id("abcdef")
            a.set_upload_id("zyxwvu")

            assert a.data.get("admin", {}).get("publisher_record_id") == "abcdef"
            assert a.is_in_doaj()
            assert a.upload_id() == "zyxwvu"

    def test_04_suggestion_model_rw(self):
        """Read and write properties into the suggestion model"""
        s = models.Suggestion()
        s.set_current_journal("9876543")
        s.set_bulk_upload_id("abcdef")

        assert s.data.get("admin", {}).get("current_journal") == "9876543"
        assert s.current_journal == "9876543"
        assert s.bulk_upload_id == "abcdef"

    def test_05_bulk_reapplication_rw(self):
        """Read and write properties into the BulkReapplication Model"""
        br = models.BulkReApplication()
        br.set_owner("richard")
        br.set_spreadsheet_name("richard.csv")

        assert br.owner == "richard"
        assert br.spreadsheet_name == "richard.csv"

    def test_06_bulk_upload(self):
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

    def test_07_make_journal(self):
        s = models.Suggestion(**ApplicationFixtureFactory.make_application_source())
        j = s.make_journal()

        assert j.id != s.id
        assert "suggestion" not in j.data
        assert j.data.get("bibjson", {}).get("active")

    def test_08_sync_owners(self):
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

    def test_09_article_deletes(self):
        # populate the index with some articles
        for i in range(5):
            a = models.Article()
            a.set_in_doaj(True)
            bj = a.bibjson()
            bj.title = "Test Article {x}".format(x=i)
            bj.add_identifier(bj.P_ISSN, "{x}000-0000".format(x=i))
            bj.publisher = "Test Publisher {x}".format(x=i)
            a.save()

            # make sure the last updated dates are suitably different
            time.sleep(1)
        time.sleep(1)

        # now hit the key methods involved in article deletes
        query = {
            "query" : {
                "bool" : {
                    "must" : [
                        {"term" : {"bibjson.title.exact" : "Test Article 0"}}
                    ]
                }
            }
        }
        count = models.Article.hit_count(query)
        assert count == 1

        count = models.Article.count_by_issns(["1000-0000", "2000-0000"])
        assert count == 2

        models.Article.delete_selected(query)
        time.sleep(2)
        assert len(models.Article.all()) == 4
        assert len(self.list_today_article_history_files()) == 1

        models.Article.delete_by_issns(["2000-0000", "3000-0000"])
        time.sleep(2)
        assert len(models.Article.all()) == 2
        assert len(self.list_today_article_history_files()) == 3

    def test_10_journal_deletes(self):
        # tests the various methods that are key to journal deletes

        # populate the index with some journals
        for i in range(5):
            j = models.Journal()
            j.set_in_doaj(True)
            bj = j.bibjson()
            bj.title = "Test Journal {x}".format(x=i)
            bj.add_identifier(bj.P_ISSN, "{x}000-0000".format(x=i))
            bj.publisher = "Test Publisher {x}".format(x=i)
            bj.add_url("http://homepage.com/{x}".format(x=i), "homepage")
            j.save()

            # make sure the last updated dates are suitably different
            time.sleep(1)

        # populate the index with some articles
        for i in range(5):
            a = models.Article()
            a.set_in_doaj(True)
            bj = a.bibjson()
            bj.title = "Test Article {x}".format(x=i)
            bj.add_identifier(bj.P_ISSN, "{x}000-0000".format(x=i))
            bj.publisher = "Test Publisher {x}".format(x=i)
            a.save()

            # make sure the last updated dates are suitably different
            time.sleep(1)

        # now hit the key methods involved in journal deletes
        query = {
            "query" : {
                "bool" : {
                    "must" : [
                        {"term" : {"bibjson.title.exact" : "Test Journal 1"}}
                    ]
                }
            }
        }
        count = models.Journal.hit_count(query)
        assert count == 1

        issns = models.Journal.issns_by_query(query)
        assert len(issns) == 1
        assert "1000-0000" in issns

        models.Journal.delete_selected(query, articles=True)
        time.sleep(2)

        assert len(models.Article.all()) == 4
        assert len(self.list_today_article_history_files()) == 1

        assert len(models.Journal.all()) == 4
        assert len(self.list_today_journal_history_files()) == 6    # Because all journals are snapshot at create time

    def test_11_iterate(self):
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
        assert len(self.list_today_journal_history_files()) == 99

    def test_12_account(self):
        # Make a new account
        acc = models.Account.make_account(
            username='mrs_user',
            email='user@example.com',
            roles=['api', 'associate_editor'],
        )

        # Check the new user has the right roles
        assert acc.has_role('api')
        assert acc.has_role('associate_editor')
        assert not acc.has_role('admin')

        # check the api key has been generated
        assert acc.api_key is not None

        # Make another account with no API access
        acc2 = models.Account.make_account(
            username='mrs_user2',
            email='user@example.com',
            roles=['editor'],
        )
        assert not acc2.has_role('api')

        # Ensure we don't get an api key
        assert not acc2.api_key
        assert acc2.data.get('api_key', None) is None

        # now add the api role and check we get a key generated
        acc2.add_role('api')
        assert acc2.api_key is not None

        # remove the api_key from the object and ask for it again
        del acc2.data['api_key']
        assert acc2.api_key is None

        acc2.generate_api_key()
        acc2.save()
        assert acc2.api_key is not None

    def test_13_block(self):
        a = models.Article()
        a.save()
        models.Article.block(a.id, a.last_updated)
        a = models.Article.pull(a.id)
        assert a is not None

    def test_14_article_model_index(self):
        """Check article indexes generate"""
        a = models.Article(**ArticleFixtureFactory.make_article_source())
        assert a.data.get('index', None) is None

        # Generate the index
        a.prep()
        assert a.data.get('index', None) is not None
