from doajtest.helpers import DoajTestCase
from werkzeug.datastructures import MultiDict
from portality.forms.application_forms import ApplicationFormFactory, STOP_WORDS
from portality.forms.validate import NotValue, ForbiddenWord

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

    def test_06_not_value(self):
        # "None" in review_process_other triggers error
        formdata = MultiDict({
            "review_process": "other",
            "review_process_other": "None"
        })
        pap = ApplicationFormFactory.context("public")
        wtf = pap.wtform(formdata)
        wtf.validate()
        rpo = wtf.review_process_other
        assert any("not a valid answer" in e for e in rpo.errors)

        # Case-insensitive: "none" also triggers error
        formdata = MultiDict({
            "review_process": "other",
            "review_process_other": "none"
        })
        pap = ApplicationFormFactory.context("public")
        wtf = pap.wtform(formdata)
        wtf.validate()
        rpo = wtf.review_process_other
        assert any("not a valid answer" in e for e in rpo.errors)

        # A valid value passes
        formdata = MultiDict({
            "review_process": "other",
            "review_process_other": "Registered reports"
        })
        pap = ApplicationFormFactory.context("public")
        wtf = pap.wtform(formdata)
        wtf.validate()
        rpo = wtf.review_process_other
        assert not any("not a valid answer" in e for e in rpo.errors)

        # Empty value passes
        formdata = MultiDict({})
        pap = ApplicationFormFactory.context("public")
        wtf = pap.wtform(formdata)
        wtf.validate()
        rpo = wtf.review_process_other
        assert not any("not a valid answer" in e for e in rpo.errors)

        # Validator with None forbidden-value is a no-op (defensive guard)
        validator = NotValue(None)
        class FakeField:
            data = "None"
            errors = []
        validator(None, FakeField())  # should not raise

    def test_07_forbidden_word(self):
        # "blind" in review_process_other triggers error
        formdata = MultiDict({
            "review_process": "other",
            "review_process_other": "blind peer review"
        })
        pap = ApplicationFormFactory.context("public")
        wtf = pap.wtform(formdata)
        wtf.validate()
        rpo = wtf.review_process_other
        assert any("structured options" in e for e in rpo.errors)

        # Case-insensitive: "Double Blind" also triggers
        formdata = MultiDict({
            "review_process": "other",
            "review_process_other": "Double Blind"
        })
        pap = ApplicationFormFactory.context("public")
        wtf = pap.wtform(formdata)
        wtf.validate()
        rpo = wtf.review_process_other
        assert any("structured options" in e for e in rpo.errors)

        # Value without "blind" passes
        formdata = MultiDict({
            "review_process": "other",
            "review_process_other": "Open review"
        })
        pap = ApplicationFormFactory.context("public")
        wtf = pap.wtform(formdata)
        wtf.validate()
        rpo = wtf.review_process_other
        assert not any("structured options" in e for e in rpo.errors)

        # Empty value passes
        formdata = MultiDict({})
        pap = ApplicationFormFactory.context("public")
        wtf = pap.wtform(formdata)
        wtf.validate()
        rpo = wtf.review_process_other
        assert not any("structured options" in e for e in rpo.errors)

        # Validator with None word is a no-op (defensive guard)
        validator = ForbiddenWord(None)
        class FakeField:
            data = "blind review"
            errors = []
        validator(None, FakeField())  # should not raise

    def test_08_not_value_on_other_fields(self):
        # "None" in persistent_identifiers_other triggers error when other is selected
        formdata = MultiDict({
            "persistent_identifiers": "other",
            "persistent_identifiers_other": "None"
        })
        pap = ApplicationFormFactory.context("public")
        wtf = pap.wtform(formdata)
        wtf.validate()
        pido = wtf.persistent_identifiers_other
        assert any("not a valid answer" in e for e in pido.errors)

        # "None" in deposit_policy_other triggers error when other is selected
        formdata = MultiDict({
            "deposit_policy": "other",
            "deposit_policy_other": "None"
        })
        pap = ApplicationFormFactory.context("public")
        wtf = pap.wtform(formdata)
        wtf.validate()
        dpo = wtf.deposit_policy_other
        assert any("not a valid answer" in e for e in dpo.errors)