from doajtest.helpers import DoajTestCase
from werkzeug.datastructures import MultiDict
from portality.forms.application_forms import ApplicationFormFactory, STOP_WORDS

class TestFormValidate(DoajTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_issn_in_public_doaj(self):
        # FIXME: we can only do this once the migration code has been merged
        pass

    def test_02_journal_url_in_public_doaj(self):
        # FIXME: we can only do this once the migration code has been merged
        pass

    def test_03_stop_words(self):
        formdata = MultiDict({
            "keywords" : ["allowed", "also allowed", STOP_WORDS[0]]
        })
        pap = ApplicationFormFactory.context("public")
        wtf = pap.wtform(formdata)
        valid = wtf.validate()

        assert not valid

        kwf = wtf.keywords
        assert len(kwf.errors) == 1
        assert STOP_WORDS[0] in kwf.errors[0]

    def test_04_max_tags(self):
        formdata = MultiDict({
            "keywords": ["x"]*7
        })
        pap = ApplicationFormFactory.context("public")
        wtf = pap.wtform(formdata)
        valid = wtf.validate()

        assert not valid

        kwf = wtf.keywords
        assert len(kwf.errors) == 1

        formdata = MultiDict({
            "keywords": ["x"] * 6
        })
        pap = ApplicationFormFactory.context("public")
        wtf = pap.wtform(formdata)
        valid = wtf.validate()
        kwf = wtf.keywords
        assert len(kwf.errors) == 0

    def test_05_required_if(self):
        # PID field has some value not "other"
        formdata = MultiDict({
            "persistent_identifiers": "DOI"
        })
        pap = ApplicationFormFactory.context("public")
        wtf = pap.wtform(formdata)
        valid = wtf.validate()
        pidof = wtf.persistent_identifiers_other
        assert len(pidof.errors) == 0

        # PID field has "other" value
        formdata = MultiDict({
            "persistent_identifiers": "other"
        })
        pap = ApplicationFormFactory.context("public")
        wtf = pap.wtform(formdata)
        valid = wtf.validate()

        assert not valid

        pidof = wtf.persistent_identifiers_other
        assert len(pidof.errors) == 1

        # PID field has "other" value and other is set
        formdata = MultiDict({
            "persistent_identifiers": "DOI",
            "persistent_identifiers_other" : "whatever"
        })
        pap = ApplicationFormFactory.context("public")
        wtf = pap.wtform(formdata)
        valid = wtf.validate()

        pidof = wtf.persistent_identifiers_other
        assert len(pidof.errors) == 0