from doajtest.helpers import DoajTestCase
from portality import models
from datetime import datetime
from doajtest.fixtures import ApplicationFixtureFactory, JournalFixtureFactory, ArticleFixtureFactory, BibJSONFixtureFactory
import time
from portality.lib import dataobj
from portality.models import shared_structs

class TestClient(DoajTestCase):

    def test_00_structs(self):
        # shared structs
        dataobj.construct_validate(shared_structs.SHARED_BIBJSON)
        dataobj.construct_validate(shared_structs.JOURNAL_BIBJSON_EXTENSION)

        # constructed structs
        journal = models.Journal()
        dataobj.construct_validate(journal._struct)

        jbj = models.JournalBibJSON()
        dataobj.construct_validate(jbj._struct)

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
        j.set_id("abcd")
        j.set_created("2001-01-01T00:00:00Z")
        j.set_last_updated("2002-01-01T00:00:00Z")
        j.set_bibjson({"title" : "test"})
        j.set_last_reapplication("2003-01-01T00:00:00Z")
        j.set_last_manual_update("2004-01-01T00:00:00Z")
        j.set_in_doaj(True)
        j.add_contact("richard", "richard@email.com")
        j.add_note("testing", "2005-01-01T00:00:00Z")
        j.set_owner("richard")
        j.set_editor_group("worldwide")
        j.set_editor("eddie")
        j.set_current_application("0987654321")
        j.set_ticked(True)
        j.set_bulk_upload_id("abcdef")
        j.set_seal(True)

        assert j.id == "abcd"
        assert j.created_date == "2001-01-01T00:00:00Z"
        assert j.created_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") == "2001-01-01T00:00:00Z"
        assert j.last_updated == "2002-01-01T00:00:00Z"
        # assert len(j.bibjson().data.keys()) == 1
        #assert j.bibjson().data["title"] == "test"
        assert j.last_reapplication == "2003-01-01T00:00:00Z"
        assert j.last_manual_update == "2004-01-01T00:00:00Z"
        assert j.last_manual_update_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") == "2004-01-01T00:00:00Z"
        assert j.is_in_doaj() is True
        assert len(j.contacts()) == 1
        assert j.get_latest_contact_name() == "richard"
        assert j.get_latest_contact_email() == "richard@email.com"
        assert len(j.notes()) == 1
        assert j.owner == "richard"
        assert j.editor_group == "worldwide"
        assert j.editor == "eddie"
        assert j.current_application == "0987654321"
        assert j.is_ticked() is True
        assert j.has_seal() is True
        assert j.bulk_upload_id == "abcdef"

        notes = j.notes()
        j.remove_note(notes[0])
        assert len(j.notes()) == 0

        j.set_notes([{"note" : "testing", "date" : "2005-01-01T00:00:00Z"}])
        assert len(j.notes()) == 1

        j.remove_current_application()
        assert j.current_application is None

        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        j.set_last_reapplication()
        assert j.last_reapplication == now # should work, since this ought to take less than a second, but it might sometimes fail

        # do a quick by-reference check on the bibjson object
        bj = j.bibjson()
        assert bj.title == "test"
        bj.publication_time = 7

        bj2 = j.bibjson()
        assert bj2.publication_time == 7

        # now construct from a fixture
        source = JournalFixtureFactory.make_journal_source(include_obsolete_fields=True)
        j = models.Journal(**source)
        assert j is not None

        # run the remaining methods just to make sure there are no errors
        j.calculate_tick()
        j.prep()
        j.save()

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
        s.set_application_status("rejected")
        s.suggested_on = "2001-01-01T00:00:00Z"
        s.set_articles_last_year(12, "http://aly.com")
        s.article_metadata = True
        s.set_suggester("test", "test@test.com")

        assert s.data.get("admin", {}).get("current_journal") == "9876543"
        assert s.current_journal == "9876543"
        assert s.bulk_upload_id == "abcdef"
        assert s.application_status == "rejected"
        assert s.suggested_on == "2001-01-01T00:00:00Z"
        assert s.articles_last_year.get("count") == 12
        assert s.articles_last_year.get("url") == "http://aly.com"
        assert s.article_metadata is True
        assert s.suggester.get("name") == "test"
        assert s.suggester.get("email") == "test@test.com"

        s.remove_current_journal()

        assert s.current_journal is None

        s.prep()
        s.save()

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

    def test_15_archiving_policy(self):
        # a recent change to how we store archiving policy means we need the object api to continue
        # to respect the old model, while transparently converting it in and out of the object
        j = models.Journal()
        b = j.bibjson()

        b.set_archiving_policy(["LOCKSS", "CLOCKSS", ["A national library", "Trinity"], ["Other", "Somewhere else"]], "http://url")
        assert b.archiving_policy == {"url" : "http://url", "policy" : ["LOCKSS", "CLOCKSS", ["A national library", "Trinity"], ["Other", "Somewhere else"]]}

        b.add_archiving_policy("SAFE")
        assert b.archiving_policy == {"url" : "http://url", "policy" : ["LOCKSS", "CLOCKSS", "SAFE", ["A national library", "Trinity"], ["Other", "Somewhere else"]]}

        assert b.flattened_archiving_policies == ['LOCKSS', 'CLOCKSS', 'SAFE', 'A national library: Trinity', 'Other: Somewhere else']

    def test_16_generic_bibjson(self):
        source = BibJSONFixtureFactory.generic_bibjson()
        gbj = models.GenericBibJSON(source)

        assert gbj.title == "The Title"
        assert len(gbj.get_identifiers()) == 2
        assert len(gbj.get_identifiers(gbj.P_ISSN)) == 1
        assert len(gbj.get_identifiers(gbj.E_ISSN)) == 1
        assert gbj.get_one_identifier() is not None
        assert gbj.get_one_identifier(gbj.E_ISSN) == "9876-5432"
        assert gbj.get_one_identifier(gbj.P_ISSN) == "1234-5678"
        assert gbj.keywords == ["word", "key"]
        assert len(gbj.get_urls()) == 6
        assert gbj.get_urls("homepage") == ["http://journal.url"]
        assert gbj.get_single_url("waiver_policy") == "http://waiver.policy"
        assert gbj.get_single_url("random") is None
        assert len(gbj.subjects()) == 2

        gbj.title = "Updated Title"
        gbj.add_identifier("doi", "10.1234/7")
        gbj.add_keyword("test")
        gbj.add_url("http://test", "test")
        gbj.add_subject("TEST", "first", "one")

        assert gbj.title == "Updated Title"
        assert len(gbj.get_identifiers()) == 3
        assert gbj.get_one_identifier("doi") == "10.1234/7"
        assert gbj.keywords == ["word", "key", "test"]
        assert gbj.get_single_url("test") == "http://test"
        assert gbj.subjects()[2] == {"scheme" : "TEST", "term" : "first", "code" : "one"}

        gbj.remove_identifiers("doi")
        gbj.set_keywords("one")
        gbj.set_subjects({"scheme" : "TEST", "term" : "first", "code" : "one"})

        assert len(gbj.get_identifiers()) == 2
        assert gbj.get_one_identifier("doi") is None
        assert gbj.keywords == ["one"]
        assert len(gbj.subjects()) == 1

        gbj.remove_identifiers()
        gbj.remove_subjects()
        assert len(gbj.get_identifiers()) == 0
        assert len(gbj.subjects()) == 0

    def test_17_journal_bibjson(self):
        source = BibJSONFixtureFactory.journal_bibjson()
        bj = models.JournalBibJSON(source)

        assert bj.alternative_title == "Alternative Title"
        assert bj.country == "US"
        assert bj.publisher == "The Publisher"
        assert bj.provider == "Platform Host Aggregator"
        assert bj.institution == "Society Institution"
        assert bj.active is True
        assert bj.language == ["EN", "FR"]
        assert bj.get_license() is not None
        assert bj.get_license_type() == "CC MY"
        assert bj.open_access is True
        assert bj.oa_start.get("year") == 1980
        assert bj.apc_url == "http://apc.com"
        assert bj.apc.get("currency") == "GBP"
        assert bj.apc.get("average_price") == 2
        assert bj.submission_charges_url == "http://submission.com"
        assert bj.submission_charges.get("currency") == "USD"
        assert bj.submission_charges.get("average_price") == 4
        assert bj.editorial_review.get("process") == "Open peer review"
        assert bj.editorial_review.get("url") == "http://review.process"
        assert bj.plagiarism_detection.get("detection") is True
        assert bj.plagiarism_detection.get("url") == "http://plagiarism.screening"
        assert bj.article_statistics.get("statistics") is True
        assert bj.article_statistics.get("url") == "http://download.stats"
        assert bj.deposit_policy == ["Sherpa/Romeo", "Store it"]
        assert bj.author_copyright.get("copyright") == "Sometimes"
        assert bj.author_copyright.get("url") == "http://copyright.com"
        assert bj.author_publishing_rights.get("publishing_rights") == "Occasionally"
        assert bj.author_publishing_rights.get("url") == "http://publishing.rights"
        assert bj.allows_fulltext_indexing is True
        assert bj.persistent_identifier_scheme == ["DOI", "ARK", "PURL"]
        assert bj.format == ["HTML", "XML", "Wordperfect"]
        assert bj.publication_time == 8
        assert bj.replaces == ["0000-0000"]
        assert bj.is_replaced_by == ["9999-9999"]
        assert bj.discontinued_date == "2001-01-01"
        assert bj.discontinued_datestamp == datetime.strptime("2001-01-01", "%Y-%m-%d")

        bj.alternative_title = "New alternate"
        bj.country = "UK"
        bj.publisher = "Me"
        bj.provider = "The claw"
        bj.institution = "UCL"
        bj.active = False
        bj.set_language("DE")
        bj.set_license("CC BY", "CC BY")
        bj.set_open_access(False)
        bj.set_oa_start(1900)
        bj.apc_url = "http://apc2.com"
        bj.set_apc("USD", 10)
        bj.submission_charges_url = "http://sub2.com"
        bj.set_submission_charges("GBP", 20)
        bj.set_editorial_review("Whatever", "http://whatever")
        bj.set_plagiarism_detection("http://test1", False)
        bj.set_article_statistics("http://test2", False)
        bj.deposit_policy = ["Never"]
        bj.set_author_copyright("http://test3", "Occasionally")
        bj.set_author_publishing_rights("http://test4", "Often")
        bj.allows_fulltext_indexing = False
        bj.persistent_identifier_scheme = "DOI"
        bj.format = "PDF"
        bj.publication_time = 4
        bj.replaces = ["1111-1111"]
        bj.is_replaced_by = ["2222-2222"]
        bj.discontinued_date = "2002-01-01"

        assert bj.alternative_title == "New alternate"
        assert bj.country == "UK"
        assert bj.publisher == "Me"
        assert bj.provider == "The claw"
        assert bj.institution == "UCL"
        assert bj.active is False
        assert bj.language == ["DE"]
        assert bj.get_license_type() == "CC BY"
        assert bj.open_access is False
        assert bj.oa_start.get("year") == 1900
        assert bj.apc_url == "http://apc2.com"
        assert bj.apc.get("currency") == "USD"
        assert bj.apc.get("average_price") == 10
        assert bj.submission_charges_url == "http://sub2.com"
        assert bj.submission_charges.get("currency") == "GBP"
        assert bj.submission_charges.get("average_price") == 20
        assert bj.editorial_review.get("process") == "Whatever"
        assert bj.editorial_review.get("url") == "http://whatever"
        assert bj.plagiarism_detection.get("detection") is False
        assert bj.plagiarism_detection.get("url") == "http://test1"
        assert bj.article_statistics.get("statistics") is False
        assert bj.article_statistics.get("url") == "http://test2"
        assert bj.deposit_policy == ["Never"]
        assert bj.author_copyright.get("copyright") == "Occasionally"
        assert bj.author_copyright.get("url") == "http://test3"
        assert bj.author_publishing_rights.get("publishing_rights") == "Often"
        assert bj.author_publishing_rights.get("url") == "http://test4"
        assert bj.allows_fulltext_indexing is False
        assert bj.persistent_identifier_scheme == ["DOI"]
        assert bj.format == ["PDF"]
        assert bj.publication_time == 4
        assert bj.replaces == ["1111-1111"]
        assert bj.is_replaced_by == ["2222-2222"]
        assert bj.discontinued_date == "2002-01-01"
        assert bj.discontinued_datestamp == datetime.strptime("2002-01-01", "%Y-%m-%d")

        bj.add_language("CZ")
        bj.add_deposit_policy("OK")
        bj.add_persistent_identifier_scheme("Handle")
        bj.add_format("CSV")
        bj.add_replaces("3333-3333")
        bj.add_is_replaced_by("4444-4444")

        assert bj.language == ["DE", "CZ"]
        assert bj.deposit_policy == ["Never", "OK"]
        assert bj.persistent_identifier_scheme == ["DOI", "Handle"]
        assert bj.format == ["PDF", "CSV"]
        assert bj.replaces == ["1111-1111", "3333-3333"]
        assert bj.is_replaced_by == ["2222-2222", "4444-4444"]

    def test_18_continuations(self):
        journal = models.Journal()
        bj = journal.bibjson()
        bj.replaces = ["1111-1111"]
        bj.is_replaced_by = ["2222-2222"]
        bj.add_identifier(bj.E_ISSN, "0000-0000")
        journal.save()

        future1 = models.Journal()
        bjf1 = future1.bibjson()
        bjf1.replaces = ["0000-0000"]
        bjf1.is_replaced_by = ["3333-3333"]
        bjf1.add_identifier(bj.E_ISSN, "2222-2222")
        future1.save()

        future2 = models.Journal()
        bjf2 = future2.bibjson()
        bjf2.replaces = ["2222-2222"]
        bjf2.add_identifier(bj.E_ISSN, "3333-3333")
        future2.save()

        past1 = models.Journal()
        bjp1 = past1.bibjson()
        bjp1.replaces = ["4444-4444"]
        bjp1.is_replaced_by = ["0000-0000"]
        bjp1.add_identifier(bj.E_ISSN, "1111-1111")
        past1.save()

        past2 = models.Journal()
        bjp2 = past2.bibjson()
        bjp2.is_replaced_by = ["1111-1111"]
        bjp2.add_identifier(bj.E_ISSN, "4444-4444")
        past2.save()

        time.sleep(2)

        past = journal.get_past_continuations()
        future = journal.get_future_continuations()

        assert len(past) == 2
        assert past[0].bibjson().get_one_identifier(bj.E_ISSN) == "1111-1111"
        assert past[1].bibjson().get_one_identifier(bj.E_ISSN) == "4444-4444"

        assert len(future) == 2
        assert future[0].bibjson().get_one_identifier(bj.E_ISSN) == "2222-2222"
        assert future[1].bibjson().get_one_identifier(bj.E_ISSN) == "3333-3333"

    def test_19_article_bibjson(self):
        source = BibJSONFixtureFactory.article_bibjson()
        bj = models.ArticleBibJSON(source)

        assert bj.year == "1987"
        assert bj.month == "4"
        assert bj.start_page == "14"
        assert bj.end_page == "15"
        assert bj.abstract == "Some text here"
        assert bj.volume == "No 10"
        assert bj.number == "Iss. 4"
        assert bj.journal_title == "Journal of Things"
        assert bj.journal_language == ["eng"]
        assert bj.journal_country == "GB"
        assert bj.journal_issns == ["1234-5678", "9876-5432"]
        assert bj.publisher == "IEEE"
        assert bj.author[0].get("name") == "Test"
        assert bj.get_journal_license().get("title") == "CC-BY"

        bj.year = "2000"
        bj.month = "5"
        bj.start_page = "100"
        bj.end_page = "110"
        bj.abstract = "New abstract"
        bj.volume = "Four"
        bj.number = "Q1"
        bj.journal_title = "Journal of Stuff"
        bj.journal_language = "fra"
        bj.journal_country = "FR"
        bj.journal_issns = ["1111-1111", "9999-9999"]
        bj.publisher = "Elsevier"
        bj.add_author("Testing", "email@email.com", "School of Hard Knocks")
        bj.set_journal_license("CC NC", "CC NC", "http://cc.nc", False)
        assert bj.get_publication_date() is not None
        assert bj.vancouver_citation() is not None

        assert bj.year == "2000"
        assert bj.month == "5"
        assert bj.start_page == "100"
        assert bj.end_page == "110"
        assert bj.abstract == "New abstract"
        assert bj.volume == "Four"
        assert bj.number == "Q1"
        assert bj.journal_title == "Journal of Stuff"
        assert bj.journal_language == ["fra"]
        assert bj.journal_country == "FR"
        assert bj.journal_issns == ["1111-1111", "9999-9999"]
        assert bj.publisher == "Elsevier"
        assert bj.author[1].get("name") == "Testing"
        assert bj.get_journal_license().get("title") == "CC NC"

        del bj.year
        del bj.month
        bj.remove_journal_metadata()

        assert bj.year is None
        assert bj.month is None
        assert bj.journal_title is None

    def test_20_make_continuation_replaces(self):
        journal = models.Journal()
        bj = journal.bibjson()
        bj.add_identifier(bj.E_ISSN, "0000-0000")
        bj.add_identifier(bj.P_ISSN, "1111-1111")
        bj.title = "First Journal"
        journal.save()

        time.sleep(2)

        cont = journal.make_continuation("replaces", eissn="2222-2222", pissn="3333-3333", title="Second Journal")

        rep = bj.replaces
        rep.sort()
        assert rep == ["2222-2222", "3333-3333"]

        cbj = cont.bibjson()

        irb = cbj.is_replaced_by
        irb.sort()

        assert irb == ["0000-0000", "1111-1111"]
        assert cbj.title == "Second Journal"
        assert cbj.get_one_identifier(cbj.E_ISSN) == "2222-2222"
        assert cbj.get_one_identifier(cbj.P_ISSN) == "3333-3333"

        assert cont.id != journal.id

    def test_21_make_continuation_is_replaced_by(self):
        journal = models.Journal()
        bj = journal.bibjson()
        bj.add_identifier(bj.E_ISSN, "0000-0000")
        bj.add_identifier(bj.P_ISSN, "1111-1111")
        bj.title = "First Journal"
        journal.save()

        time.sleep(2)

        cont = journal.make_continuation("is_replaced_by", eissn="2222-2222", pissn="3333-3333", title="Second Journal")

        irb = bj.is_replaced_by
        irb.sort()
        assert irb == ["2222-2222", "3333-3333"]

        cbj = cont.bibjson()

        rep = cbj.replaces
        rep.sort()

        assert rep == ["0000-0000", "1111-1111"]
        assert cbj.title == "Second Journal"
        assert cbj.get_one_identifier(cbj.E_ISSN) == "2222-2222"
        assert cbj.get_one_identifier(cbj.P_ISSN) == "3333-3333"

        assert cont.id != journal.id

    def test_22_make_continuation_errors(self):
        journal = models.Journal()
        bj = journal.bibjson()
        bj.add_identifier(bj.E_ISSN, "0000-0000")
        bj.add_identifier(bj.P_ISSN, "1111-1111")
        bj.title = "First Journal"
        journal.save()

        time.sleep(2)

        with self.assertRaises(models.ContinuationException):
            cont = journal.make_continuation("sideways", eissn="2222-2222", pissn="3333-3333", title="Second Journal")

        with self.assertRaises(models.ContinuationException):
            cont = journal.make_continuation("replaces", title="Second Journal")

    def test_23_make_continuation_single_issn(self):
        # this is to cover a case where a single issn is provided during the continuations create process,
        # to make sure the behaviour is still correct
        journal = models.Journal()
        bj = journal.bibjson()
        bj.add_identifier(bj.E_ISSN, "0000-0000")
        bj.add_identifier(bj.P_ISSN, "1111-1111")
        bj.title = "First Journal"
        journal.save()

        time.sleep(2)

        # first do it with an eissn
        cont = journal.make_continuation("replaces", eissn="2222-2222", title="Second Journal")

        rep = bj.replaces
        rep.sort()
        assert rep == ["2222-2222"]

        cbj = cont.bibjson()

        irb = cbj.is_replaced_by
        irb.sort()

        assert irb == ["0000-0000", "1111-1111"]
        assert cbj.title == "Second Journal"
        assert cbj.get_one_identifier(cbj.E_ISSN) == "2222-2222"

        assert cont.id != journal.id

        # then do it with a pissn and give it a dud eissn
        cont = journal.make_continuation("replaces", pissn="3333-3333", eissn="", title="Second Journal")

        rep = bj.replaces
        rep.sort()
        assert rep == ["3333-3333"]

        cbj = cont.bibjson()

        irb = cbj.is_replaced_by
        irb.sort()

        assert irb == ["0000-0000", "1111-1111"]
        assert cbj.title == "Second Journal"
        assert cbj.get_one_identifier(cbj.P_ISSN) == "3333-3333"

        assert cont.id != journal.id


