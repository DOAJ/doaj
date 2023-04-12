import pytest

from doajtest import helpers
from doajtest.fixtures import JournalFixtureFactory, AccountFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models
from portality.forms.application_forms import disable_edit_note_except_cur_user, JournalFormFactory
from portality.lib.formulaic import FormulaicField
from portality.models import Account
from portality.util import url_for
import bs4

JOURNAL_SOURCE = JournalFixtureFactory.make_journal_source()


@pytest.fixture
def edit_note_cases():
    return [
        ('test_user_id', True),
        ("fake_account_id__b", False),
    ]


@pytest.mark.parametrize("user_id, expected_result", [
    ('test_user_id', True),
    ("fake_account_id__b", False),
])
def test_disable_edit_note_except_cur_user(user_id, expected_result):
    formulaic_context = JournalFormFactory.context("associate_editor", extra_param={
        'cur_user': Account(id=user_id),
    })
    formulaic_context.processor(source=models.Journal(**JOURNAL_SOURCE))
    note_field: FormulaicField = formulaic_context.fieldset('notes').fields()[0].group_subfields()[0]
    note_field.wtfinst = next(formulaic_context.fieldset('notes').fields()[0].wtfield[0].__iter__(), None)
    assert disable_edit_note_except_cur_user(note_field, formulaic_context) == expected_result


class TestEditableNote(DoajTestCase):

    def test_note_textarea_disabled_correctly(self):
        pwd = 'password123'
        acc = models.Account(**AccountFixtureFactory.make_editor_source())
        acc.set_id('fake_account_id__b')
        acc.set_password(pwd)
        acc.save()

        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_editor(acc.id)
        journal.save(blocking=True)

        with self.app_test.test_client() as t_client:
            resp = helpers.login(t_client, acc.email, pwd)
            assert resp.status_code == 200

            resp = t_client.get(url_for("editor.journal_page", journal_id=journal.id))
            assert resp.status_code == 200

            soup = bs4.BeautifulSoup(resp.data, 'html.parser')
            ele = soup.select_one('textarea#notes-0-note')
            assert not ele.has_attr('disabled')

            ele = soup.select_one('textarea#notes-1-note')
            assert ele.has_attr('disabled')
