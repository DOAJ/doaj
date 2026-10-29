from werkzeug.datastructures import ImmutableMultiDict

from doajtest.helpers import DoajTestCase
from portality.core import app
from portality.models import Account
from portality.view.account import RegisterForm


def _form(identifier):
    return RegisterForm(ImmutableMultiDict([
        ('next', '/register'),
        ('identifier', identifier),
        ('sender_email', 'aga@example.com'),
    ]))


class TestRegisterFormIdentifier(DoajTestCase):

    def test_01_identifier_is_stripped(self):
        for raw in ['bob ', ' bob', '  bob  ', '\tbob\n']:
            assert _form(raw).identifier.data == 'bob', raw

    def test_02_internal_spaces_kept(self):
        assert _form(' bob smith ').identifier.data == 'bob smith'

    def test_03_blank_identifier(self):
        assert _form('   ').identifier.data == ''

    def test_04_validators_see_stripped_value(self):
        reserved = app.config.get('RESERVED_USERNAMES', [])[0]
        form = _form(reserved + ' ')
        assert not form.validate()
        assert form.identifier.errors

        Account.make_account(email='taken@example.com', username='taken').save(blocking=True)
        form = _form(' taken ')
        assert not form.validate()
        assert 'Account ID already in use' in form.identifier.errors
