import portality.formcontext.xwalks.journal_form
from doajtest.fixtures.article_doajxml import DoajXmlArticleFixtureFactory
from doajtest.fixtures.article_crossref import CrossrefArticleFixtureFactory
from doajtest.helpers import DoajTestCase, diff_dicts
from portality.crosswalks.article_doaj_xml import DOAJXWalk
from portality.crosswalks.article_crossref_xml import CrossrefXWalk
from portality.formcontext import forms
from portality.formcontext.xwalks import suggestion_form
from portality import models
from werkzeug.datastructures import MultiDict
from copy import deepcopy
from portality import lcc

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

class TestXwalk(DoajTestCase):
    def setUp(self):
        self.old_lookup_code = lcc.lookup_code
        lcc.lookup_code = mock_lookup_code

    def tearDown(self):
        lcc.lookup_code = self.old_lookup_code

    def test_01_journal(self):
        forminfo = portality.formcontext.xwalks.journal_form.JournalFormXWalk.obj2form(models.Journal(**JOURNAL_SOURCE))
        #diff_dicts(JOURNAL_FORMINFO, forminfo)
        assert forminfo == JOURNAL_FORMINFO

        form = forms.ManEdJournalReviewForm(formdata=MultiDict(JOURNAL_FORM))
        obj = portality.formcontext.xwalks.journal_form.JournalFormXWalk.form2obj(form)

        onotes = obj["admin"]["notes"]
        del obj["admin"]["notes"]

        cnotes = JOURNAL_SOURCE["admin"]["notes"]
        csource = deepcopy(JOURNAL_SOURCE)
        del csource["admin"]["notes"]

        otext = [n.get("note") for n in onotes]
        ctext = [n.get("note") for n in cnotes]
        assert otext == ctext

        # get rid of the id and created_date in the ready-made fixture journal for comparison
        # the model object is not going to have an id or created_date since it's not been saved yet
        del csource['id']
        del csource['created_date']
        del csource["admin"]["current_application"]
        del csource["admin"]["related_applications"]
        assert obj == csource, diff_dicts(csource, obj, 'csource', 'modelobj')

    def test_02_application(self):
        forminfo = suggestion_form.SuggestionFormXWalk.obj2form(models.Suggestion(**APPLICATION_SOURCE))
        #diff_dicts(APPLICATION_FORMINFO, forminfo)
        assert forminfo == APPLICATION_FORMINFO

        form = forms.ManEdApplicationReviewForm(formdata=MultiDict(APPLICATION_FORM))
        obj = suggestion_form.SuggestionFormXWalk.form2obj(form)

        onotes = obj["admin"]["notes"]
        del obj["admin"]["notes"]

        cnotes = APPLICATION_SOURCE["admin"]["notes"]
        csource = deepcopy(APPLICATION_SOURCE)
        del csource["admin"]["notes"]

        otext = [n.get("note") for n in onotes]
        ctext = [n.get("note") for n in cnotes]
        assert otext == ctext

        # get rid of the id and created_date in the ready-made fixture application for comparison
        # the model object is not going to have an id or created_date since it's not been saved yet
        del csource['id']
        del csource['created_date']
        del csource["admin"]["current_journal"]
        del csource["admin"]["related_journal"]
        del csource["suggestion"]["suggested_on"]
        #diff_dicts(csource, obj, 'csource', 'modelobj')
        #diff_dicts(csource["bibjson"], obj["bibjson"])
        assert obj == csource

    def test_04_application_license_other_text_broken(self):
        af = APPLICATION_FORM
        af["license_other"] = "None",

        form = forms.ManEdApplicationReviewForm(formdata=MultiDict(af))
        obj = suggestion_form.SuggestionFormXWalk.form2obj(form)

        assert obj.bibjson().get_license_type() == "None"

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
