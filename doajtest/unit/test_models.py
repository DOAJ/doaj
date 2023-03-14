import json
import time

from doajtest.fixtures import ApplicationFixtureFactory, JournalFixtureFactory, ArticleFixtureFactory, \
    BibJSONFixtureFactory, ProvenanceFixtureFactory, BackgroundFixtureFactory, AccountFixtureFactory
from doajtest.helpers import DoajTestCase, patch_history_dir
from portality import constants
from portality import models
from portality.lib import dataobj
from portality.lib import seamless
from portality.models import shared_structs
from portality.models.v1.bibjson import GenericBibJSON


class TestModels(DoajTestCase):

    def test_00_structs(self):
        # shared structs
        try:
            seamless.Construct(shared_structs.JOURNAL_BIBJSON, None, None).validate()
        except seamless.SeamlessException as e:
            raise Exception(e.message)

        try:
            seamless.Construct(shared_structs.SHARED_JOURNAL_LIKE, None, None).validate()
        except seamless.SeamlessException as e:
            raise Exception(e.message)

        # constructed structs
        journal = models.Journal()
        try:
            journal.__seamless_struct__.validate()
        except seamless.SeamlessException as e:
            raise Exception(e.message)

        application = models.Application()
        try:
            application.__seamless_struct__.validate()
        except seamless.SeamlessException as e:
            raise Exception(e.message)

    def test_01_imports(self):
        """import all of the model objects successfully?"""

        j = models.lookup_model("journal")
        ja = models.lookup_model("journal_article")

        assert j.__type__ == "journal"
        assert ja.__type__ == "journal,article"

    def test_02_journal_model_rw(self):
        """Read and write properties into the journal model"""
        j = models.Journal()

        # check some properties of empty objects
        assert not j.has_been_manually_updated()
        assert not j.has_seal()
        assert not j.is_in_doaj()
        assert not j.is_ticked()

        # methods for all journal-like objects
        j.set_id("abcd")
        j.set_created("2001-01-01T00:00:00Z")
        j.set_last_updated("2002-01-01T00:00:00Z")
        j.set_last_manual_update("2004-01-01T00:00:00Z")
        j.set_seal(True)
        j.set_owner("richard")
        j.set_editor_group("worldwide")
        j.set_editor("eddie")
        j.add_contact("richard", "richard@email.com")
        j.add_note("testing", "2005-01-01T00:00:00Z")
        j.set_bibjson({"title": "test"})

        assert j.id == "abcd"
        assert j.created_date == "2001-01-01T00:00:00Z"
        assert j.created_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") == "2001-01-01T00:00:00Z"
        assert j.last_updated == "2002-01-01T00:00:00Z"
        assert j.last_updated_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") == "2002-01-01T00:00:00Z"
        assert j.last_manual_update == "2004-01-01T00:00:00Z"
        assert j.last_manual_update_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") == "2004-01-01T00:00:00Z"
        assert j.has_been_manually_updated() is True
        assert j.has_seal() is True
        assert j.owner == "richard"
        assert j.editor_group == "worldwide"
        assert j.editor == "eddie"
        # assert len(j.contacts()) == 1
        assert j.get_latest_contact_name() == "richard"
        assert j.get_latest_contact_email() == "richard@email.com"
        assert len(j.notes) == 1
        assert j.bibjson().title == "test"

        j.remove_owner()
        j.remove_editor_group()
        j.remove_editor()
        j.remove_contact()

        assert j.owner is None
        assert j.editor_group is None
        assert j.editor is None
        # assert len(j.contacts()) == 0

        j.add_note("another note", "2019-01-01T00:00:00Z", "1234567890")
        assert len(j.notes) == 2
        first = True
        for n in j.ordered_notes:
            if first:
                assert n.get("note") == "another note"
                assert n.get("date") == "2019-01-01T00:00:00Z"
                assert n.get("id") == "1234567890"
                first = False
            else:
                assert n.get("note") == "testing"
                assert n.get("date") == "2005-01-01T00:00:00Z"
                assert n.get("id") is not None
        notes = j.notes
        j.remove_note(notes[0])
        assert len(j.notes) == 1
        j.set_notes([{"note": "testing", "date": "2005-01-01T00:00:00Z"}])
        assert len(j.notes) == 1
        j.remove_notes()
        assert len(j.notes) == 0

        # journal specific methods
        j.bibjson().eissn = "1111-1111"
        j.bibjson().pissn = "2222-2222"

        j.set_in_doaj(True)
        j.set_ticked(True)
        j.set_current_application("0987654321")
        j.add_related_application("123456789", "2003-01-01T00:00:00Z")
        j.add_related_application("987654321", "2002-01-01T00:00:00Z")

        assert j.toc_id == "1111-1111"
        assert j.is_in_doaj() is True
        assert j.is_ticked() is True
        assert j.current_application == "0987654321"
        assert j.last_update_request == "2003-01-01T00:00:00Z"

        j.remove_current_application()
        assert j.current_application is None

        del j.bibjson().eissn
        assert j.toc_id == "2222-2222"
        del j.bibjson().pissn
        assert j.toc_id == "abcd"

        # check over the related_applications management functions
        related = j.related_applications
        assert related is not None
        assert j.latest_related_application_id() == "123456789"
        j.remove_related_applications()
        assert len(j.related_applications) == 0
        j.set_related_applications(related)
        assert len(j.related_applications) == 2
        j.add_related_application("123456789", "2005-01-01T00:00:00Z")  # duplicate id, should be overwritten
        assert len(j.related_applications) == 2
        rar = j.related_application_record("123456789")
        assert rar.get("application_id") == "123456789"
        assert rar.get("date_accepted") == "2005-01-01T00:00:00Z"
        j.add_related_application("123456789", "2005-01-01T00:00:00Z", "deleted")  # update as if being deleted
        rar = j.related_application_record("123456789")
        assert rar.get("application_id") == "123456789"
        assert rar.get("date_accepted") == "2005-01-01T00:00:00Z"
        assert rar.get("status") == "deleted"

        # do a quick by-reference check on the bibjson object
        bj = j.bibjson()
        assert bj.title == "test"
        bj.publication_time = 7

        bj2 = j.bibjson()
        assert bj2.publication_time == 7

        # check over ordered note reading
        j.add_note("testing", "2005-01-01T00:00:00Z")
        j.add_note("another note", "2010-01-01T00:00:00Z")
        j.add_note("an old note", "2001-01-01T00:00:00Z")
        ons = j.ordered_notes
        assert len(ons) == 3
        assert ons[2]["note"] == "an old note"
        assert ons[1]["note"] == "testing"
        assert ons[0]["note"] == "another note"

        # now construct from a fixture
        source = JournalFixtureFactory.make_journal_source()
        try:
            j = models.Journal(**source)
        except seamless.SeamlessException as e:
            raise Exception(e.message)
        assert j is not None

        # run the remaining methods just to make sure there are no errors
        j.calculate_tick()
        try:
            j.prep()
        except seamless.SeamlessException as e:
            raise Exception(e.message)
        j.save()

    def test_03_article_model_rw(self):
        """Read and write properties into the article model"""
        a = models.Article()
        assert not a.is_in_doaj()
        assert not a.has_seal()

        a.set_in_doaj(True)
        a.set_seal(True)
        a.set_publisher_record_id("abcdef")
        a.set_upload_id("zyxwvu")

        assert a.data.get("admin", {}).get("publisher_record_id") == "abcdef"
        assert a.is_in_doaj()
        assert a.has_seal()
        assert a.upload_id() == "zyxwvu"

    def test_04_suggestion_model_rw(self):
        """Read and write properties into the suggestion model"""
        s = models.Application()

        # check some properties of empty objects
        assert not s.has_been_manually_updated()
        assert not s.has_seal()

        # methods for all journal-like objects
        s.set_id("abcd")
        s.set_created("2001-01-01T00:00:00Z")
        s.set_last_updated("2002-01-01T00:00:00Z")
        s.set_last_manual_update("2004-01-01T00:00:00Z")
        s.set_seal(True)
        s.set_owner("richard")
        s.set_editor_group("worldwide")
        s.set_editor("eddie")
        s.add_contact("richard", "richard@email.com")
        s.add_note("testing", "2005-01-01T00:00:00Z")
        s.set_bibjson({"title": "test"})

        assert s.id == "abcd"
        assert s.created_date == "2001-01-01T00:00:00Z"
        assert s.created_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") == "2001-01-01T00:00:00Z"
        assert s.last_updated == "2002-01-01T00:00:00Z"
        assert s.last_updated_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") == "2002-01-01T00:00:00Z"
        assert s.last_manual_update == "2004-01-01T00:00:00Z"
        assert s.last_manual_update_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") == "2004-01-01T00:00:00Z"
        assert s.has_been_manually_updated() is True
        assert s.has_seal() is True
        assert s.owner == "richard"
        assert s.editor_group == "worldwide"
        assert s.editor == "eddie"
        # assert len(s.contacts()) == 1
        assert s.get_latest_contact_name() == "richard"
        assert s.get_latest_contact_email() == "richard@email.com"
        assert len(s.notes) == 1
        assert s.bibjson().title == "test"

        s.remove_owner()
        s.remove_editor_group()
        s.remove_editor()
        s.remove_contact()

        assert s.owner is None
        assert s.editor_group is None
        assert s.editor is None
        # assert len(s.contacts()) == 0

        s.add_note("another note", "2019-01-01T00:00:00Z", "1234567890")
        assert len(s.notes) == 2
        first = True
        for n in s.ordered_notes:
            if first:
                assert n.get("note") == "another note"
                assert n.get("date") == "2019-01-01T00:00:00Z"
                assert n.get("id") == "1234567890"
                first = False
            else:
                assert n.get("note") == "testing"
                assert n.get("date") == "2005-01-01T00:00:00Z"
                assert n.get("id") is not None
        notes = s.notes
        s.remove_note(notes[0])
        assert len(s.notes) == 1
        s.set_notes([{"note": "testing", "date": "2005-01-01T00:00:00Z"}])
        assert len(s.notes) == 1
        s.remove_notes()
        assert len(s.notes) == 0

        # application specific methods
        s.set_current_journal("9876543")
        s.set_related_journal("123456789")
        s.set_application_status(constants.APPLICATION_STATUS_REJECTED)
        s.date_applied = "2001-01-01T00:00:00Z"

        assert s.current_journal == "9876543"
        assert s.related_journal == "123456789"
        assert s.application_status == constants.APPLICATION_STATUS_REJECTED
        assert s.date_applied == "2001-01-01T00:00:00Z"

        # check over ordered note reading
        s.add_note("another note", "2010-01-01T00:00:00Z")
        s.add_note("an old note", "2001-01-01T00:00:00Z")
        ons = s.ordered_notes
        assert len(ons) == 2
        assert ons[1]["note"] == "an old note"
        assert ons[0]["note"] == "another note"

        s.prep()
        d = s.__seamless__.data
        assert 'index' in d, d
        assert 'application_type' in d['index'], d['index']
        # assert d['index']['application_type'] == constants.INDEX_RECORD_TYPE_UPDATE_REQUEST_FINISHED
        # FIXME: temporary partial reversion for 1779
        assert d['index']['application_type'] == "update request"

        s.remove_current_journal()
        assert s.current_journal is None
        s.set_is_update_request(False)
        s.prep()
        d = s.__seamless__.data
        assert 'index' in d, d
        assert 'application_type' in d['index'], d['index']
        # assert d['index']['application_type'] == constants.INDEX_RECORD_TYPE_NEW_APPLICATION_FINISHED
        # FIXME: temporary partial reversion for 1779
        assert d['index']['application_type'] == "finished application/update"

        s.set_application_status(constants.APPLICATION_STATUS_PENDING)
        s.prep()
        d = s.__seamless__.data
        # assert d['index']['application_type'] == constants.INDEX_RECORD_TYPE_NEW_APPLICATION_UNFINISHED
        # FIXME: temporary partial reversion for 1779
        assert d['index']['application_type'] == "new application"

        s.save()

        s.remove_current_journal()
        s.remove_related_journal()
        assert s.current_journal is None
        assert s.related_journal is None

        # check deprecated methods (they still need to work)
        s.suggested_on = "2003-01-01T00:00:00Z"
        assert s.suggested_on == "2003-01-01T00:00:00Z"

    def test_05_sync_owners(self):
        # suggestion with no current_journal
        s = models.Suggestion(**ApplicationFixtureFactory.make_application_source())
        s.save(blocking=True)
        s = models.Suggestion.pull(s.id)
        assert s is not None

        # journal with no current_application
        j = models.Journal(**JournalFixtureFactory.make_journal_source())
        j.save(blocking=True)
        j = models.Journal.pull(j.id)
        assert j is not None

        # suggestion with erroneous current_journal
        s.set_current_journal("asdklfjsadjhflasdfoasf")
        s.save(blocking=True)
        s = models.Suggestion.pull(s.id)
        assert s is not None

        # journal with erroneous current_application
        j.set_current_application("kjwfuiwqhu220952gw")
        j.save(blocking=True)
        j = models.Journal.pull(j.id)
        assert j is not None

        # suggestion with journal
        s.set_owner("my_new_owner")
        s.set_current_journal(j.id)
        s.save(blocking=True)

        j = models.Journal.pull(j.id)
        assert j.owner == "my_new_owner"

        # journal with suggestion
        j.set_owner("another_new_owner")
        j.set_current_application(s.id)
        j.save(blocking=True)

        s = models.Suggestion.pull(s.id)
        assert s.owner == "another_new_owner"

    @patch_history_dir("ARTICLE_HISTORY_DIR")
    def test_06_article_deletes(self):
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
            time.sleep(0.66)

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
        time.sleep(1)
        assert len(models.Article.all()) == 4
        assert len(self.list_today_article_history_files()) == 1

        models.Article.delete_by_issns(["2000-0000", "3000-0000"])
        time.sleep(1)
        assert len(models.Article.all()) == 2
        assert len(self.list_today_article_history_files()) == 3

    @patch_history_dir("ARTICLE_HISTORY_DIR")
    @patch_history_dir('JOURNAL_HISTORY_DIR')
    def test_07_journal_deletes(self):
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
            time.sleep(0.66)

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
            time.sleep(0.66)

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
        time.sleep(1)

        assert len(models.Article.all()) == 4
        assert len(self.list_today_article_history_files()) == 1

        assert len(models.Journal.all()) == 4
        assert len(self.list_today_journal_history_files()) == 6    # Because all journals are snapshot at create time

    @patch_history_dir('JOURNAL_HISTORY_DIR')
    def test_08_iterate(self):
        for jsrc in JournalFixtureFactory.make_many_journal_sources(count=99, in_doaj=True):
            j = models.Journal(**jsrc)
            j.save()
        time.sleep(2) # index all the journals
        journal_ids = []
        theqgen = models.JournalQuery()
        for j in models.Journal.iterate(q=theqgen.all_in_doaj(), page_size=10):
            journal_ids.append(j.id)
        journal_ids = list(set(journal_ids[:]))  # keep only unique ids
        assert len(journal_ids) == 99
        assert len(self.list_today_journal_history_files()) == 99

    def test_09_account(self):
        # Make a new account
        acc = models.Account.make_account(email='user@example.com', username='mrs_user',
                                          roles=['api', 'associate_editor'])

        # Check the new user has the right roles
        assert acc.has_role('api')
        assert acc.has_role('associate_editor')
        assert not acc.has_role('admin')
        assert acc.marketing_consent is None

        # check the api key has been generated
        assert acc.api_key is not None

        # Make another account with no API access
        acc2 = models.Account.make_account(email='user@example.com', username='mrs_user2', roles=['editor'])
        assert not acc2.has_role('api')

        # Ensure we don't get an api key
        assert not acc2.api_key
        assert acc2.data.get('api_key', None) is None

        # now add the api role and check we get a key generated
        acc2.add_role('api')
        assert acc2.api_key is not None

        # Set marketing consent to True
        acc2.set_marketing_consent(True)
        assert acc2.marketing_consent is True

        # Now set marketing consent to false
        acc2.set_marketing_consent(False)
        assert acc2.marketing_consent is False

        # remove the api_key from the object and ask for it again
        del acc2.data['api_key']
        assert acc2.api_key is None

        acc2.generate_api_key()
        acc2.save()
        assert acc2.api_key is not None

    def test_10_block(self):
        a = models.Article()
        a.save()
        models.Article.block(a.id, a.last_updated)
        a = models.Article.pull(a.id)
        assert a is not None

    def test_11_article_model_index(self):
        """Check article indexes generate"""
        a = models.Article(**ArticleFixtureFactory.make_article_source())
        assert a.data.get('index', None) is None

        # Generate the index
        a.prep()
        assert a.data.get('index', None) is not None

    def test_12_archiving_policy(self):
        # a recent change to how we store archiving policy means we need the object api to continue
        # to respect the old model, while transparently converting it in and out of the object
        j = models.Journal()
        b = j.bibjson()

        b.set_archiving_policy(["LOCKSS", "CLOCKSS", ["A national library", "Trinity"], "Somewhere else"], "http://url")
        assert b.preservation_url == "http://url"
        assert b.preservation_summary == ["LOCKSS", "CLOCKSS", "Somewhere else", ["A national library", "Trinity"]]

        b.add_archiving_policy("SAFE")
        assert b.preservation_summary == ["LOCKSS", "CLOCKSS", "Somewhere else", "SAFE", ["A national library", "Trinity"]]

        assert b.flattened_archiving_policies == ['LOCKSS', 'CLOCKSS', "Somewhere else", 'SAFE', 'A national library: Trinity'], b.flattened_archiving_policies

    def test_13_generic_bibjson(self):
        source = BibJSONFixtureFactory.generic_bibjson()
        gbj = GenericBibJSON(source)

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
        gbj.add_keyword("ONE") # make sure keywords are stored in lowercase
        keyword = None  # make sure None keyword doesn't cause error
        gbj.add_keyword(keyword)
        gbj.add_url("http://test", "test")
        gbj.add_subject("TEST", "first", "one")

        assert gbj.title == "Updated Title"
        assert len(gbj.get_identifiers()) == 3
        assert gbj.get_one_identifier("doi") == "10.1234/7"
        assert gbj.keywords == ["word", "key", "test", "one"]
        assert gbj.get_single_url("test") == "http://test"
        assert gbj.subjects()[2] == {"scheme" : "TEST", "term" : "first", "code" : "one"}

        gbj.remove_identifiers("doi")
        gbj.set_keywords("TwO") # make sure keywords are stored in lowercase
        gbj.set_subjects({"scheme" : "TEST", "term" : "first", "code" : "one"})
        assert gbj.keywords == ["two"]

        keywords = []
        gbj.set_keywords(keywords)
        keywords = None
        gbj.set_keywords(keywords)

        assert len(gbj.get_identifiers()) == 2
        assert gbj.get_one_identifier("doi") is None

        assert len(gbj.subjects()) == 1

        gbj.remove_identifiers()
        gbj.remove_subjects()
        assert len(gbj.get_identifiers()) == 0
        assert len(gbj.subjects()) == 0

    def test_14_journal_like_bibjson(self):
        source = BibJSONFixtureFactory.journal_bibjson()
        bj = models.JournalLikeBibJSON(source)

        assert bj.alternative_title == "Alternative Title"
        assert bj.boai is True
        assert bj.discontinued_date == "2001-01-01"
        assert bj.discontinued_datestamp.strftime("%Y-%m-%d") == "2001-01-01"
        assert bj.eissn == "9876-5432"
        assert bj.pissn == "1234-5678"
        assert bj.publication_time_weeks == 8
        assert bj.title == "The Title"
        assert bj.is_replaced_by == ["2222-2222"]
        assert bj.keywords == ["word", "key"]
        assert bj.language == ["ENG", "FRE"]
        assert len(bj.licences) == 1
        assert bj.replaces == ["1111-1111"]
        assert len(bj.subject) == 2
        assert len(bj.apc) == 1
        assert bj.apc[0].get("currency") == "GBP"
        assert bj.apc[0].get("price") == 2
        assert bj.apc_url == "http://apc.com"
        assert bj.has_apc is True
        assert bj.article_license_display == ["Embed"]
        assert bj.article_license_display_example_url == "http://licence.embedded"
        assert bj.article_orcid is True
        assert bj.article_i4oc_open_citations is False
        assert bj.author_retains_copyright is True
        assert bj.copyright_url == "http://copyright.com"
        assert bj.deposit_policy == ["Sherpa/Romeo", "Store it"]
        assert bj.has_deposit_policy is True
        assert bj.deposit_policy_url == "http://deposit.policy"
        assert bj.editorial_review_process == ["Open peer review", "some bloke checks it out"]
        assert bj.editorial_review_url == "http://review.process"
        assert bj.editorial_board_url == "http://editorial.board"
        assert bj.institution == "Society Institution"
        assert bj.institution_country == "USA"
        assert bj.has_other_charges is True
        assert bj.other_charges_url == "http://other.charges"
        assert bj.pid_scheme == ["DOI", "ARK", "PURL", "PIDMachine"]
        assert bj.plagiarism_detection is True
        assert bj.plagiarism_url == "http://plagiarism.screening"
        assert bj.preservation is not None
        assert bj.preservation_summary == ["LOCKSS", "CLOCKSS", "A safe place", ["A national library", "Trinity"], ["A national library", "Imperial"]]
        assert bj.preservation_url == "http://digital.archiving.policy"
        assert bj.publisher_name == "The Publisher"
        assert bj.publisher_country == "USA"
        assert bj.oa_statement_url == "http://oa.statement"
        assert bj.journal_url == "http://journal.url"
        assert bj.aims_scope_url == "http://aims.scope"
        assert bj.author_instructions_url == "http://author.instructions.com"
        assert bj.license_terms_url == "http://licence.url"
        assert bj.has_waiver is True
        assert bj.waiver_url == "http://waiver.policy"

        bj.alternative_title = "New alternate"
        bj.boai = False
        bj.discontinued_date = "2002-01-01"
        bj.eissn = "0000-000x"
        bj.pissn = "1111-111x"
        bj.publication_time_weeks = 4
        bj.title = "Another title"
        bj.keywords = ["new", "terms"]
        bj.is_replaced_by = ["4444-4444"]
        bj.language = ["ITA"]
        bj.replaces = ["3333-3333"]
        bj.subject = [{"scheme": "TEST", "term": "first", "code": "one"}]
        bj.apc_url = "http://apc2.com"
        bj.article_license_display = "No"
        bj.article_license_display_example_url = "http://licence2.embedded"
        bj.article_orcid = False
        bj.article_i4oc_open_citations = False
        bj.author_retains_copyright = False
        bj.copyright_url = "http://copyright2.url"
        bj.deposit_policy = ["Never"]
        bj.deposit_policy_url = "http://other.policy"
        bj.has_deposit_policy = False
        bj.set_editorial_review("Whatever", "http://whatever", "http://board2.url")
        bj.institution = "UCL"
        bj.institution_country = "FR"
        bj.has_other_charges = False
        bj.other_charges_url = "http://other2.url"
        bj.pid_scheme = "Handle"
        bj.set_plagiarism_detection("http://test1", False)
        bj.set_preservation(["LOCKSS", ["a national library", "UCL"]], "http://preservation")
        bj.publisher_name = "Me"
        bj.publisher_country = "GBR"
        bj.oa_statement_url = "http://oa2.statement"
        bj.journal_url = "http://journal2.url"
        bj.aims_scope_url = "http://aims2.url"
        bj.author_instructions_url = "http://inst2.url"
        bj.license_terms_url = "http://terms2.url"
        bj.has_waiver = False
        bj.waiver_url = "http://waiver2.url"

        assert bj.alternative_title == "New alternate"
        assert bj.boai is False
        assert bj.discontinued_date == "2002-01-01"
        assert bj.eissn == "0000-000X"
        assert bj.pissn == "1111-111X"
        assert bj.publication_time_weeks == 4
        assert bj.title == "Another title"
        assert bj.is_replaced_by == ["4444-4444"]
        assert bj.keywords == ["new", "terms"]
        assert bj.language == ["ITA"]
        assert len(bj.licences) == 1
        assert bj.replaces == ["3333-3333"]
        assert len(bj.subject) == 1
        assert bj.apc_url == "http://apc2.com"
        assert bj.article_license_display == ["No"]
        assert bj.article_license_display_example_url == "http://licence2.embedded"
        assert bj.article_orcid is False
        assert bj.article_i4oc_open_citations is False
        assert bj.author_retains_copyright is False
        assert bj.copyright_url == "http://copyright2.url"
        assert bj.deposit_policy == ["Never"]
        assert bj.has_deposit_policy is False
        assert bj.deposit_policy_url == "http://other.policy"
        assert bj.editorial_review_process == ["Whatever"]
        assert bj.editorial_review_url == "http://whatever"
        assert bj.editorial_board_url == "http://board2.url"
        assert bj.institution == "UCL"
        assert bj.institution_country == "FRA"
        assert bj.has_other_charges is False
        assert bj.other_charges_url == "http://other2.url"
        assert bj.pid_scheme == ["Handle"]
        assert bj.plagiarism_detection is False
        assert bj.plagiarism_url == "http://test1"
        assert bj.preservation is not None
        assert bj.preservation_summary == ["LOCKSS", ["A national library", "UCL"]]
        assert bj.preservation_url == "http://preservation"
        assert bj.publisher_name == "Me"
        assert bj.publisher_country == "GBR"
        assert bj.oa_statement_url == "http://oa2.statement"
        assert bj.journal_url == "http://journal2.url"
        assert bj.aims_scope_url == "http://aims2.url"
        assert bj.author_instructions_url == "http://inst2.url"
        assert bj.license_terms_url == "http://terms2.url"
        assert bj.has_waiver is False
        assert bj.waiver_url == "http://waiver2.url"

        bj.preservation_url = "http://preservation3"
        assert bj.preservation_url == "http://preservation3"

        bj.add_is_replaced_by("4321-4321")
        bj.add_keyword("keyword")
        bj.add_language("CES")
        bj.add_license("CC YOUR", "http://cc.your", True, True, True, False)
        bj.add_replaces("1234-1234")
        bj.add_subject("SCH", "TERM", "CDE")
        bj.add_apc("USD", 7)
        bj.add_deposit_policy("OK")
        bj.add_pid_scheme("PURL")
        bj.add_preservation("MOUNTAIN")
        bj.add_preservation(libraries="LSE")

        assert bj.is_replaced_by == ["4444-4444", "4321-4321"]
        assert bj.keywords == ["new", "terms", "keyword"]
        assert bj.language == ["ITA", "CES"]
        assert len(bj.licences) == 2
        assert bj.replaces == ["3333-3333", "1234-1234"]
        assert len(bj.subject) == 2
        assert len(bj.apc) == 2
        assert bj.deposit_policy == ["Never", "OK"]
        assert bj.pid_scheme == ["Handle", "PURL"]
        assert bj.preservation_summary == ["LOCKSS", "MOUNTAIN", ["A national library", "UCL"], ["A national library", "LSE"]]

        # special methods
        assert bj.issns() == ["1111-111X", "0000-000X"], bj.issns()
        assert bj.publisher_country_name() == "United Kingdom", bj.publisher_country_name()
        assert "Italian" in bj.language_name(), bj.language_name()
        assert bj.get_preferred_issn() == "0000-000X", bj.get_preferred_issn()

        bj.set_unregistered_journal_policy("http://unregistered.policy")
        assert bj.deposit_policy_url == "http://unregistered.policy"
        assert bj.has_deposit_policy is True

        with self.assertRaises(seamless.SeamlessException):
            bj.article_license_display = "notallowedvalue"

        # deprecated methods (they still need to work)
        bj.publication_time = 3
        assert bj.publication_time == 3
        assert bj.publication_time_weeks == 3

        bj.set_keywords(["one", "two"])
        assert bj.keywords == ["one", "two"]

        bj.set_language("de")
        assert bj.language == ["GER"]

        bj.persistent_identifier_scheme = ["ARK"]
        assert bj.persistent_identifier_scheme == ["ARK"]
        assert bj.pid_scheme == ["ARK"]
        bj.add_persistent_identifier_scheme("PURL")
        assert bj.pid_scheme == ["ARK", "PURL"]

        assert bj.subject == bj.subjects()
        bj.set_subjects({"scheme" : "whatever", "term" : "also whatever"})
        assert bj.subject == [{"scheme" : "whatever", "term" : "also whatever"}]
        bj.remove_subjects()
        assert len(bj.subject) == 0

        bj.set_archiving_policy(["LOCKSS"], "http://archiving")
        assert bj.preservation_services == ["LOCKSS"]
        assert bj.preservation_url == "http://archiving"
        bj.add_archiving_policy("CLOCKSS")
        assert bj.preservation_services == ["LOCKSS", "CLOCKSS"]

        bj.add_identifier(bj.E_ISSN, "0101-0101")
        assert bj.eissn == "0101-0101"
        bj.add_identifier(bj.P_ISSN, "1010-1010")
        assert bj.pissn == "1010-1010"
        assert bj.get_identifiers(bj.E_ISSN) == ["0101-0101"]
        assert bj.get_identifiers(bj.P_ISSN) == ["1010-1010"]
        assert bj.get_one_identifier(bj.E_ISSN) == "0101-0101"
        assert bj.get_one_identifier(bj.P_ISSN) == "1010-1010"

        bj.add_url("http://homepage", bj.HOMEPAGE)
        bj.add_url("http://waiver", bj.WAIVER_POLICY)
        bj.add_url("http://editorial", bj.EDITORIAL_BOARD)
        bj.add_url("http://aims", bj.AIMS_SCOPE)
        bj.add_url("http://author", bj.AUTHOR_INSTRUCTIONS)
        bj.add_url("http://oa", bj.OA_STATEMENT)

        assert bj.journal_url == "http://homepage"
        assert bj.waiver_url == "http://waiver"
        assert bj.editorial_board_url == "http://editorial"
        assert bj.aims_scope_url == "http://aims"
        assert bj.author_instructions_url == "http://author"
        assert bj.oa_statement_url == "http://oa"

        assert bj.get_urls(bj.HOMEPAGE) == ["http://homepage"]
        assert bj.get_urls(bj.WAIVER_POLICY) == ["http://waiver"]
        assert bj.get_urls(bj.EDITORIAL_BOARD) == ["http://editorial"]
        assert bj.get_urls(bj.AIMS_SCOPE) == ["http://aims"]
        assert bj.get_urls(bj.AUTHOR_INSTRUCTIONS) == ["http://author"]
        assert bj.get_urls(bj.OA_STATEMENT) == ["http://oa"]

        assert bj.get_single_url(bj.HOMEPAGE) == "http://homepage"
        assert bj.get_single_url(bj.WAIVER_POLICY) == "http://waiver"
        assert bj.get_single_url(bj.EDITORIAL_BOARD) == "http://editorial"
        assert bj.get_single_url(bj.AIMS_SCOPE) == "http://aims"
        assert bj.get_single_url(bj.AUTHOR_INSTRUCTIONS) == "http://author"
        assert bj.get_single_url(bj.OA_STATEMENT) == "http://oa"

        assert bj.first_eissn == bj.eissn
        assert bj.first_pissn == bj.pissn
        assert bj.country == bj.publisher_country
        assert bj.open_access == bj.boai

        bj.country = "RUS"
        assert bj.country == "RUS"
        assert bj.publisher_country == "RUS"

        bj.set_open_access(not bj.open_access)
        assert bj.open_access == bj.boai

        assert bj.country_name() == bj.publisher_country_name()

        assert bj.publisher_name == bj.publisher

        # deleters
        del bj.discontinued_date
        del bj.eissn
        del bj.pissn
        del bj.is_replaced_by
        del bj.replaces
        del bj.subject

        assert bj.discontinued_date is None
        assert bj.eissn is None
        assert bj.pissn is None
        assert bj.is_replaced_by == []
        assert bj.replaces == []
        assert bj.subject == []


    def test_15_continuations(self):
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

    def test_16_article_bibjson(self):
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
        assert bj.journal_language == ["ENG"]
        assert bj.journal_country == "GBR"
        assert bj.journal_issns == ["1234-5678", "9876-5432"]
        assert bj.publisher == "IEEE"
        assert bj.author[0].get("name") == "Test"
        assert bj.author[0].get("affiliation") == "University of Life"
        assert bj.author[0].get("orcid_id") == "https://orcid.org/0000-0001-1234-1234", "received: {}".format(bj.author[0].get("orcid_id"))

        bj.year = "2000"
        bj.month = "5"
        bj.start_page = "100"
        bj.end_page = "110"
        bj.abstract = "New abstract"
        bj.volume = "Four"
        bj.number = "Q1"
        bj.journal_title = "Journal of Stuff"
        bj.journal_language = "fre"
        bj.journal_country = "FR"
        bj.journal_issns = ["1111-1111", "9999-9999"]
        bj.publisher = "Elsevier"
        bj.add_author("Testing", "School of Hard Knocks", "0000-0001-4321-4321")
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
        assert bj.journal_language == ["FRE"]
        assert bj.journal_country == "FR"
        assert bj.journal_issns == ["1111-1111", "9999-9999"]
        assert bj.publisher == "Elsevier"
        assert bj.author[1].get("name") == "Testing"
        assert bj.author[1].get("affiliation") == "School of Hard Knocks"
        assert bj.author[1].get("orcid_id") == "0000-0001-4321-4321", "received: {}".format(bj.author[1].get("orcid_id"))

        del bj.year
        del bj.month
        bj.remove_journal_metadata()

        assert bj.year is None
        assert bj.month is None
        assert bj.journal_title is None

    def test_17_make_continuation_replaces(self):
        journal = models.Journal()
        bj = journal.bibjson()
        bj.add_identifier(bj.E_ISSN, "0000-0000")
        bj.add_identifier(bj.P_ISSN, "1111-1111")
        bj.title = "First Journal"
        journal.save(blocking=True)

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

    def test_18_make_continuation_is_replaced_by(self):
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

    def test_19_make_continuation_errors(self):
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

    def test_20_make_continuation_single_issn(self):
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

    def test_21_index_has_apc(self):
        # no apc record, not ticked
        j = models.Journal()
        j.set_created("1970-01-01T00:00:00Z")  # so it's before the tick
        j.prep()
        assert j.data.get("index", {}).get("has_apc") == "No Information"

        # no apc record, ticked
        j = models.Journal()
        j.prep()
        assert j.data.get("index", {}).get("has_apc") == "No"

        # apc record, not ticked
        j = models.Journal()
        j.set_created("1970-01-01T00:00:00Z")  # so it's before the tick
        b = j.bibjson()
        b.add_apc("GBP", 100)
        j.prep()
        assert j.data.get("index", {}).get("has_apc") == "Yes"

        # apc record, ticked
        j = models.Journal()
        b = j.bibjson()
        b.add_apc("GBP", 100)
        j.prep()
        assert j.data.get("index", {}).get("has_apc") == "Yes"

    def test_22_autocomplete(self):
        j = models.Journal()
        bj = j.bibjson()
        bj.publisher = "BioMed Central"
        j.save()

        j = models.Journal()
        bj = j.bibjson()
        bj.publisher = "BioMedical Publisher"
        j.save()

        j = models.Journal()
        bj = j.bibjson()
        bj.publisher = "De Gruyter"
        j.save()

        j = models.Journal()
        bj = j.bibjson()
        bj.publisher = "Deep Mind"
        j.save(blocking=True)

        res = models.Journal.advanced_autocomplete("index.publisher_ac", "bibjson.publisher.name", "Bio")
        assert len(res) == 2, "autocomplete for 'Bio': found {}, expected 2".format(len(res))

        res = models.Journal.advanced_autocomplete("index.publisher_ac", "bibjson.publisher.name", "BioMed")
        assert len(res) == 2, "autocomplete for 'BioMed': found {}, expected 2".format(len(res))

        res = models.Journal.advanced_autocomplete("index.publisher_ac", "bibjson.publisher.name", "De ")
        assert len(res) == 1, "autocomplete for 'De ': found {}, expected 2".format(len(res))

        res = models.Journal.advanced_autocomplete("index.publisher_ac", "bibjson.publisher.name", "BioMed C")
        assert len(res) == 1, "autocomplete for 'BioMed C': found {}, expected 2".format(len(res))

    def test_23_provenance(self):
        """Read and write properties into the provenance model"""
        p = models.Provenance()

        # now construct from a fixture
        source = ProvenanceFixtureFactory.make_provenance_source()
        p = models.Provenance(**source)
        assert p is not None

        # run the remaining methods just to make sure there are no errors
        p.save()

    def test_24_save_valid_seamless_or_dataobj(self):
        j = models.Journal()
        bj = j.bibjson()
        bj.title = "A legitimate title"
        j.data["junk"] = "in here"
        with self.assertRaises(seamless.SeamlessException):
            j.save()
        assert j.id is None

        s = models.Suggestion()
        sbj = s.bibjson()
        sbj.title = "A legitimate title"
        s.data["junk"] = "in here"
        with self.assertRaises(seamless.SeamlessException):
            s.save()
        assert s.id is None

        p = models.Provenance()
        p.type = "suggestion"
        p.data["junk"] = "in here"
        with self.assertRaises(dataobj.DataStructureException):
            p.save()
        assert p.id is None

    def test_25_make_provenance(self):
        acc = models.Account()
        acc.set_id("test")
        acc.add_role("associate_editor")
        acc.add_role("editor")

        obj1 = models.Application()
        obj1.set_id("obj1")

        models.Provenance.make(acc, "act1", obj1)

        time.sleep(2)

        prov = models.Provenance.get_latest_by_resource_id("obj1")
        assert prov.type == "suggestion"
        assert prov.user == "test"
        assert prov.roles == ["associate_editor", "editor"]
        assert len(prov.editor_group) == 0
        assert prov.subtype is None
        assert prov.action == "act1"
        assert prov.resource_id == "obj1"

        eg1 = models.EditorGroup()
        eg1.set_id("associate")
        eg1.add_associate(acc.id)
        eg1.save()

        eg2 = models.EditorGroup()
        eg2.set_id("editor")
        eg2.set_name("Editor")   # note: REQUIRED so that the mapping includes .name, which is needed to find groups_by
        eg2.set_editor(acc.id)
        eg2.save()

        time.sleep(2)

        obj2 = models.Suggestion()
        obj2.set_id("obj2")

        models.Provenance.make(acc, "act2", obj2, "sub")

        time.sleep(2)

        prov = models.Provenance.get_latest_by_resource_id("obj2")
        assert prov.type == "suggestion"
        assert prov.user == "test"
        assert prov.roles == ["associate_editor", "editor"]
        assert prov.editor_group == ["editor", "associate"]
        assert prov.subtype == "sub"
        assert prov.action == "act2"
        assert prov.resource_id == "obj2"

    def test_26_background_job(self):
        source = BackgroundFixtureFactory.example()
        bj = models.BackgroundJob(**source)
        bj.save(blocking=True)

        retrieved = models.BackgroundJob.pull(bj.id)
        assert retrieved is not None

        source = BackgroundFixtureFactory.example()
        source["params"]["ids"] = ["1", "2", "3"]
        source["params"]["type"] = "suggestion"
        source["reference"]["query"]  = json.dumps({"query" : {"match_all" : {}}})
        bj = models.BackgroundJob(**source)
        bj.save()

        bj.add_audit_message("message")
        assert len(bj.audit) == 2

    def test_26a_background_job_active(self):
        source = BackgroundFixtureFactory.example()
        bj = models.BackgroundJob(**source)
        bj.save(blocking=True)

        assert len(models.BackgroundJob.active(source["action"])) == 1, "expected 1 active, got {x}".format(x=len(models.BackgroundJob.active(source["action"])))


    def test_27_article_journal_sync(self):
        j = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        a = models.Article(**ArticleFixtureFactory.make_article_source(in_doaj=False, with_journal_info=False))

        assert a.has_seal() is False
        assert a.bibjson().journal_issns != j.bibjson().issns()

        reg = models.Journal()
        changed = a.add_journal_metadata(j, reg)

        assert changed is True
        assert a.has_seal() is False
        assert a.is_in_doaj() is True
        assert a.bibjson().journal_issns == j.bibjson().issns()
        assert a.bibjson().publisher == j.bibjson().publisher
        assert a.bibjson().journal_country == j.bibjson().country
        assert a.bibjson().journal_language == j.bibjson().language
        assert a.bibjson().journal_title == j.bibjson().title

        changed = a.add_journal_metadata(j)
        assert changed is False

    def test_28_application_latest_by_current_journal(self):
        j = models.Journal()
        j.set_id(j.makeid())

        app1 = models.Suggestion(**ApplicationFixtureFactory.make_application_source())
        app1.set_id(app1.makeid())
        app1.set_current_journal(j.id)
        app1.set_created("1970-01-01T00:00:00Z")
        app1.save()

        app2 = models.Suggestion(**ApplicationFixtureFactory.make_application_source())
        app2.set_id(app2.makeid())
        app2.set_current_journal(j.id)
        app2.set_created("1971-01-01T00:00:00Z")
        app2.save(blocking=True)

        # check that we find the right application when we search
        app3 = models.Suggestion.find_latest_by_current_journal(j.id)
        assert app3 is not None
        assert app3.id == app2.id

        # make sure we get a None response when there's no application
        app0 = models.Suggestion.find_latest_by_current_journal("whatever")
        assert app0 is None

    def test_29_application_all_by_related_journal(self):
        j = models.Journal()
        j.set_id(j.makeid())

        app1 = models.Suggestion(**ApplicationFixtureFactory.make_application_source())
        app1.set_id(app1.makeid())
        app1.set_related_journal(j.id)
        app1.set_created("1970-01-01T00:00:00Z")
        app1.save()

        app2 = models.Suggestion(**ApplicationFixtureFactory.make_application_source())
        app2.set_id(app2.makeid())
        app2.set_related_journal(j.id)
        app2.set_created("1971-01-01T00:00:00Z")
        app2.save(blocking=True)

        # check that we find all the applications when we search, and that they're in the right order
        all = models.Suggestion.find_all_by_related_journal(j.id)
        assert len(all) == 2
        assert all[0].id == app1.id
        assert all[1].id == app2.id

    def test_30_article_stats(self):
        articles = []

        # make a bunch of articles variably in doaj/not in doaj, for/not for the issn we'll search
        for i in range(1, 3):
            article = models.Article(
                **ArticleFixtureFactory.make_article_source(eissn="1111-1111", pissn="1111-1111", with_id=False, in_doaj=True)
            )
            article.set_created("2019-01-0" + str(i) + "T00:00:00Z")
            articles.append(article)
        for i in range(3, 5):
            article = models.Article(
                **ArticleFixtureFactory.make_article_source(eissn="1111-1111", pissn="1111-1111", with_id=False, in_doaj=False)
            )
            article.set_created("2019-01-0" + str(i) + "T00:00:00Z")
            articles.append(article)
        for i in range(5, 7):
            article = models.Article(
                **ArticleFixtureFactory.make_article_source(eissn="2222-2222", pissn="2222-2222", with_id=False, in_doaj=True)
            )
            article.set_created("2019-01-0" + str(i) + "T00:00:00Z")
            articles.append(article)
        for i in range(7, 9):
            article = models.Article(
                **ArticleFixtureFactory.make_article_source(eissn="2222-2222", pissn="2222-2222", with_id=False, in_doaj=False)
            )
            article.set_created("2019-01-0" + str(i) + "T00:00:00Z")
            articles.append(article)

        [a.save() for a in articles]
        models.Article.blockall([(a.id, a.last_updated) for a in articles])

        journal = models.Journal()
        bj = journal.bibjson()
        bj.add_identifier(bj.P_ISSN, "1111-1111")
        stats = journal.article_stats()
        assert stats.get("total", 0) == 2
        assert stats.get("latest") == "2019-01-02T00:00:00Z"

    def test_31_cache(self):
        models.Cache.cache_site_statistics({
            "journals" : 10,
            "new_journals" : 20,
            "countries" : 30,
            "abstracts" : 40,
            "no_apc" : 50
        })

        models.Cache.cache_csv("/csv/filename.csv")

        models.Cache.cache_sitemap("sitemap.xml")

        models.Cache.cache_public_data_dump("ac", "af", "http://example.com/article", 100, "jc", "jf", "http://example.com/journal", 200)
        
        time.sleep(1)

        stats = models.Cache.get_site_statistics()
        assert stats["journals"] == 10
        assert stats["new_journals"] == 20
        assert stats["countries"] == 30
        assert stats["abstracts"] == 40
        assert stats["no_apc"] == 50

        assert models.Cache.get_latest_csv().get("url") == "/csv/filename.csv"

        assert models.Cache.get_latest_sitemap() == "sitemap.xml"

        article_data = models.Cache.get_public_data_dump().get("article")
        assert article_data.get("url") == "http://example.com/article"
        assert article_data.get("size") == 100
        assert article_data.get("container") == "ac"
        assert article_data.get("filename") == "af"

        journal_data = models.Cache.get_public_data_dump().get("journal")
        assert journal_data.get("url") == "http://example.com/journal"
        assert journal_data.get("size") == 200
        assert journal_data.get("container") == "jc"
        assert journal_data.get("filename") == "jf"

    def test_32_journal_like_object_discovery(self):
        """ Check that the JournalLikeObject can retrieve the correct results for Journals and Applications """
        # todo - more tests for the shared journallike code

        # Create accounts with journals
        account_blocklist = []
        journal_blocklist = []
        application_blocklist = []

        # Create account without journals attached
        pubsource = AccountFixtureFactory.make_publisher_source()
        pubaccount_no_journal = models.Account(**pubsource)
        pubaccount_no_journal.set_id()
        pubaccount_no_journal.save()
        account_blocklist.append((pubaccount_no_journal.id, pubaccount_no_journal.last_updated))

        for i in range(3):
            pubsource = AccountFixtureFactory.make_publisher_source()
            pubaccount = models.Account(**pubsource)
            pubaccount.set_id()
            pubaccount.save()
            account_blocklist.append((pubaccount.id, pubaccount.last_updated))

            # Attach a few applications and journals, some in doaj and some not
            for j in range(4):
                jsource = JournalFixtureFactory.make_journal_source(in_doaj=bool(j % 2))
                a = models.Journal(**jsource)
                a.set_id()
                a.set_owner(pubaccount.id)
                a.save()
                journal_blocklist.append((a.id, a.last_updated))

                asource = ApplicationFixtureFactory.make_application_source()
                a = models.Application(**asource)
                a.set_id()
                a.set_owner(pubaccount.id)
                a.save()
                application_blocklist.append((a.id, a.last_updated))

        models.Account.blockall(account_blocklist)
        models.Journal.blockall(journal_blocklist)
        models.Application.blockall(application_blocklist)

        # Check we don't get anything when we request by owner with the owner who has no journallike objects
        print(pubaccount_no_journal.id)
        assert len(models.Journal.issns_by_owner(pubaccount_no_journal.id)) == 0
        assert len(models.Application.issns_by_owner(pubaccount_no_journal.id)) == 0
        assert len(models.Journal.get_by_owner(pubaccount_no_journal.id)) == 0
        assert len(models.Application.get_by_owner(pubaccount_no_journal.id)) == 0

        # Ensure we get all journals and applications for a given owner (including those not in doaj)
        last_owner_id = account_blocklist.pop()[0]
        owned_journals = models.Journal.get_by_owner(last_owner_id)
        assert len(owned_journals) == 4
        assert isinstance(owned_journals.pop(), models.Journal)

        owned_applications = models.Application.get_by_owner(last_owner_id)
        assert len(owned_applications) == 4
        assert isinstance(owned_applications.pop(), models.Application)

        # find_by_issn(cls, issns, in_doaj=None, max=10)
        # issns_by_owner(cls, owner)
        # get_by_owner(cls, owner)
        # issns_by_query(cls, query):
        # find_by_journal_url(cls, url, in_doaj=None, max=10)
        # recent(cls, max=10):

# TODO: reinstate this test when author emails have been disallowed again
# '''
#     def test_33_article_with_author_email(self):
#         """Check the system disallows articles with emails in the author field"""
#         a_source = ArticleFixtureFactory.make_article_source()
#
#         # Creating a model from a source with email is rejected by the DataObj
#         a_source['bibjson']['author'][0]['email'] = 'author@example.com'
#         with self.assertRaises(dataobj.DataStructureException):
#             a = models.Article(**a_source)
#             bj = a.bibjson()
#
#         # Remove the email address again to create the model
#         del a_source['bibjson']['author'][0]['email']
#         a = models.Article(**a_source)
#
#         # We can't add an author with an email address any more.
#         with self.assertRaises(TypeError):
#             a.bibjson().add_author(name='Ms Test', affiliation='School of Rock', email='author@example.com')
# '''

    def test_34_preserve(self):
        model = models.PreservationState()
        model.set_id("1234")
        model.set_created("2021-06-10T00:00:00Z")
        model.initiated("rama", "test_article.zip")

        assert model.id == "1234"
        assert model.owner == "rama"
        assert model.created_date == "2021-06-10T00:00:00Z"
        assert model.status == "initiated"

        model.validated()
        assert model.status == "validated"

        model.pending()
        assert model.status == "pending"

        model.uploaded_to_ia()
        assert model.status == "uploaded"

        model.failed("Unknown Reason", "Error: Unknown  Reason")
        assert model.status == "failed"
        assert model.error == "Unknown Reason"
        assert model.error_details == "Error: Unknown  Reason"

    def test_35_event(self):
        event = models.Event()
        event.id = "12345"
        event.who = "testuser"
        event.set_context(key="value", key2="value2")

        assert event.id == "12345"
        assert event.who == "testuser"
        assert event.context.get("key") == "value"
        assert event.context.get("key2") == "value2"
        assert event.when is not None

        j = event.serialise()
        data = json.loads(j)

        event2 = models.Event(raw=data)
        assert event2.id == "12345"
        assert event2.who == "testuser"
        assert event2.context.get("key") == "value"
        assert event2.context.get("key2") == "value2"
        assert event2.when == event.when

        event3 = models.Event("ABCD", "another", {"key3" : "value3"})
        assert event3.id == "ABCD"
        assert event3.who == "another"
        assert event3.context.get("key3") == "value3"
        assert event3.when is not None

    def test_36_notification(self):
        n = models.Notification()
        n.who = "testuser"
        n.long = "my message"
        n.short = "short note"
        n.action = "/test"
        n.classification = "test_class"
        n.created_by = "test:notify"

        assert n.who == "testuser"
        assert n.long == "my message"
        assert n.short == "short note"
        assert n.action == "/test"
        assert n.classification == "test_class"
        assert n.created_by == "test:notify"

        assert not n.is_seen()
        assert n.seen_date is None

        n.set_seen()
        assert n.is_seen()
        assert n.seen_date is not None

        n2 = models.Notification(**n.data)
        assert n2.who == "testuser"
        assert n2.long == "my message"
        assert n2.short == "short note"
        assert n2.action == "/test"
        assert n2.classification == "test_class"
        assert n2.created_by == "test:notify"
        assert n2.is_seen()
        assert n2.seen_date is not None


