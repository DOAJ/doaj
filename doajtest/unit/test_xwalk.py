from doajtest.helpers import DoajTestCase, diff_dicts
from portality.formcontext import xwalk, forms
from portality import models
from werkzeug.datastructures import MultiDict
from copy import deepcopy
from portality import lcc

from doajtest.fixtures import JournalFixtureFactory, ApplicationFixtureFactory

JOURNAL_FORM = JournalFixtureFactory.make_journal_form()
JOURNAL_FORMINFO = JournalFixtureFactory.make_journal_form_info()
JOURNAL_SOURCE = JournalFixtureFactory.make_journal_source_with_legacy_info()

APPLICATION_FORM = ApplicationFixtureFactory.make_application_form()
APPLICATION_FORMINFO = ApplicationFixtureFactory.make_application_form_info()
APPLICATION_SOURCE = ApplicationFixtureFactory.make_update_request_source()

OLD_STYLE_APP = ApplicationFixtureFactory.make_update_request_source()
del OLD_STYLE_APP["bibjson"]["persistent_identifier_scheme"]
del OLD_STYLE_APP["bibjson"]["deposit_policy"]
del OLD_STYLE_APP["bibjson"]["author_copyright"]
del OLD_STYLE_APP["bibjson"]["author_publishing_rights"]

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
        forminfo = xwalk.JournalFormXWalk.obj2form(models.Journal(**JOURNAL_SOURCE))
        #diff_dicts(JOURNAL_FORMINFO, forminfo)
        assert forminfo == JOURNAL_FORMINFO

        form = forms.ManEdJournalReviewForm(formdata=MultiDict(JOURNAL_FORM))
        obj = xwalk.JournalFormXWalk.form2obj(form)

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
        forminfo = xwalk.SuggestionFormXWalk.obj2form(models.Suggestion(**APPLICATION_SOURCE))
        #diff_dicts(APPLICATION_FORMINFO, forminfo)
        assert forminfo == APPLICATION_FORMINFO

        form = forms.ManEdApplicationReviewForm(formdata=MultiDict(APPLICATION_FORM))
        obj = xwalk.SuggestionFormXWalk.form2obj(form)

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
        #diff_dicts(csource, obj, 'csource', 'modelobj')
        #diff_dicts(csource["bibjson"], obj["bibjson"])
        assert obj == csource

    def test_03_old_style_to_new_style(self):
        forminfo = xwalk.SuggestionFormXWalk.obj2form(models.Suggestion(**OLD_STYLE_APP))
        # assert forminfo.get("article_identifiers") != "None"

    def test_04_application_license_other_text_broken(self):
        af = APPLICATION_FORM
        af["license_other"] = "None",

        form = forms.ManEdApplicationReviewForm(formdata=MultiDict(af))
        obj = xwalk.SuggestionFormXWalk.form2obj(form)

        assert obj.bibjson().get_license_type() == "None"
