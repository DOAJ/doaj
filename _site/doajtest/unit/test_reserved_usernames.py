from doajtest.helpers import DoajTestCase

from nose.tools import assert_raises

from werkzeug.datastructures import MultiDict
from wtforms import StringField, Form, validators

from portality import models
from portality.formcontext import validate

class TestReservedUsernames(DoajTestCase):
    def setUp(self):
        class FormWithUsernameField(Form):
            username = StringField('Username', [validate.ReservedUsernames()])

        self.test_form_class = FormWithUsernameField
        self.reserved_user = self.app_test.config['RESERVED_USERNAMES'][0]

    def tearDown(self):
        pass

    def test_01_reserved_usernames_in_forms(self):
        test_form = self.test_form_class(formdata=MultiDict({'username': 'system'}))
        test_form.validate()
        assert len(test_form.errors) == 1, str(test_form.errors)
        assert test_form.errors['username'] == ['The "{}" user is reserved. Please choose a different '
                                                'username.'.format(self.reserved_user)] \
            , str(test_form.errors['username'])

    def test_02_unreserved_usernames_in_forms(self):
        test_form = self.test_form_class(formdata=MultiDict({'username': 'justauser'}))
        test_form.validate()
        assert len(test_form.errors) == 0

    def test_03_reserved_usernames_using_model_directly(self):
        assert_raises(validators.ValidationError, models.Account, id=self.reserved_user)

    def test_04_unreserved_usernames_using_model_directly(self):
        models.Account(id='justauser')  # no error is raised, that is the test
