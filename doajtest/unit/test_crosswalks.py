from portality.crosswalks.journal_form import JournalFormXWalk
from portality.crosswalks.application_form import ApplicationFormXWalk
from doajtest.fixtures.article_doajxml import DoajXmlArticleFixtureFactory
from doajtest.fixtures.article_crossref import CrossrefArticleFixtureFactory
from doajtest.helpers import DoajTestCase, diff_dicts
from portality.crosswalks.article_doaj_xml import DOAJXWalk
from portality.crosswalks.article_crossref_xml import CrossrefXWalk
from portality.formcontext import forms

from portality import models
from werkzeug.datastructures import MultiDict
from copy import deepcopy
from portality import lcc
from portality.models import Journal, Application
from portality.forms.application_forms import ApplicationFormFactory

from doajtest.fixtures import JournalFixtureFactory, ApplicationFixtureFactory

JOURNAL_FORM = JournalFixtureFactory.make_journal_form()
JOURNAL_FORMINFO = JournalFixtureFactory.make_journal_form_info()
JOURNAL_SOURCE = JournalFixtureFactory.make_journal_source()

APPLICATION_FORM = ApplicationFixtureFactory.make_application_form()
APPLICATION_FORMINFO = ApplicationFixtureFactory.make_application_form_info()
APPLICATION_SOURCE = ApplicationFixtureFactory.make_update_request_source()

######################################################################
# Mocks
######################################################################

def mock_lookup_code(code):
    if code == "H": return "Social Sciences"
    if code == "HB1-3840": return "Economic theory. Demography"
    return None


class TestCrosswalks(DoajTestCase):
    def setUp(self):
        self.old_lookup_code = lcc.lookup_code
        lcc.lookup_code = mock_lookup_code

    def tearDown(self):
        lcc.lookup_code = self.old_lookup_code

    def test_01_journal_form2obj(self):
        pc = ApplicationFormFactory.context("admin")
        form = pc.wtform(JOURNAL_FORM)

        obj = JournalFormXWalk.form2obj(form)

        assert isinstance(obj, Journal)

        xwalked = obj.bibjson().data
        compare = deepcopy(JOURNAL_SOURCE.get("bibjson"))

        assert xwalked == compare, diff_dicts(xwalked, compare, 'xwalked', 'fixture')

    def test_02_journal_obj2form(self):
        j = models.Journal(**JOURNAL_SOURCE)
        form = JournalFormXWalk.obj2form(j)

        compare = deepcopy(JOURNAL_FORMINFO)
        assert form == compare, diff_dicts(form, compare, 'xwalked', 'fixture')


    def test_03_application_form2obj(self):
        pc = ApplicationFormFactory.context("admin")
        form = pc.wtform(MultiDict(APPLICATION_FORM))

        obj = ApplicationFormXWalk.form2obj(form)

        assert isinstance(obj, Application)

        xwalked = obj.bibjson().data
        compare = deepcopy(APPLICATION_SOURCE.get("bibjson"))

        assert xwalked == compare, diff_dicts(xwalked, compare, 'xwalked', 'fixture')

    def test_04_application_obj2form(self):
        j = models.Application(**APPLICATION_SOURCE)
        form = ApplicationFormXWalk.obj2form(j)

        compare = deepcopy(APPLICATION_FORMINFO)

        # sort the notes so they are comparable
        form.get("notes").sort(key=lambda x: x["note_id"])
        compare.get("notes").sort(key=lambda x: x["note_id"])

        assert form == compare, diff_dicts(form, compare, 'xwalked', 'fixture')

    def test_05_doaj_article_xml_xwalk(self):
        handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
        xwalk = DOAJXWalk()
        art = xwalk.crosswalk_file(file_handle=handle, add_journal_info=False)
        article = models.Article(**art[0])
        bibjson = article.bibjson()

        assert bibjson.journal_language == ["fre"], "expected ['fre'], actual: {} ".format(bibjson.journal_language)
        assert bibjson.publisher == "Codicille éditeur et CRILCQ", "expected 'Codicille éditeur et CRILCQ', actual: {} ".format(bibjson.publisher)
        assert bibjson.journal_title == "2 ISSNs Correct", "expected '2 ISSNs Correct', received: {}".format(bibjson.journal_title)
        assert bibjson.get_one_identifier(bibjson.P_ISSN) == "1234-5678", "expected '1234-5678', received: {}".format(bibjson.get_one_identifier(bibjson.P_ISSN))
        assert bibjson.get_one_identifier(bibjson.E_ISSN) == "9876-5432", "expected '9876-5432', received: {}".format(bibjson.get_one_identifier(bibjson.E_ISSN))
        assert bibjson.year == "2013", "expected '2013', received: {}".format(bibjson.year)
        assert bibjson.title == "Imaginaires autochtones contemporains. Introduction", "expected 'Imaginaires autochtones contemporains. Introduction', received: {}".format(bibjson.title)
        assert bibjson.author == [{'name': 'Papillon, Joëlle'}], "expected [{{'name': 'Papillon, Joëlle'}}]', received: {}".format(bibjson.author)
        assert bibjson.get_single_url("fulltext") == "http://doaj.org/testing/url.pdf", "expected 'http://doaj.org/testing/url.pdf', received: {}".format(bibjson.get_single_url("fulltext"))

    def test_06_crossref_article_xml_xwalk(self):
        handle = CrossrefArticleFixtureFactory.upload_2_issns_correct()
        xwalk = CrossrefXWalk()
        art = xwalk.crosswalk_file(file_handle=handle, add_journal_info=False)
        article = models.Article(**art[0])
        bibjson = article.bibjson()

        assert bibjson.journal_title == "2 ISSNs Correct", "expected '2 ISSNs Correct', received: {}".format(bibjson.journal_title)
        assert bibjson.get_one_identifier(bibjson.P_ISSN) == "1234-5678", "expected '1234-5678', received: {}".format(bibjson.get_one_identifier(bibjson.P_ISSN))
        assert bibjson.get_one_identifier(bibjson.E_ISSN) == "9876-5432", "expected '9876-5432', received: {}".format(bibjson.get_one_identifier(bibjson.E_ISSN))
        assert bibjson.year == "2004", "expected '2004', received: {}".format(bibjson.year)
        assert bibjson.title == "Article 12292005 9:32", "expected 'Article 12292005 9:32', received: {}".format(bibjson.title)
        assert bibjson.author == [{'name': 'Surname, Bob'}], "expected [{{'name': 'Surname, Bob'}}]', received: {}".format(bibjson.author)
        assert bibjson.get_single_url("fulltext") == "http://www.crossref.org/", "expected 'http://www.crossref.org/', received: {}".format(bibjson.get_single_url("fulltext"))
