from flask import Response

from doajtest import helpers
from doajtest.helpers import DoajTestCase
from portality import models
from portality.core import load_account_for_login_manager
from portality.decorators import api_key_required, api_key_optional


class TestAPIClient(DoajTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestAPIClient, cls).setUpClass()
        helpers.initialise_index()

        # Turn off debug and so we're allowed to add these routes after the app has been used in other tests
        cls.app_test.debug = False
        cls.app_test.testing = False

        """This is a lie, but it allows us to circumnavigate a check to prevent routes being added after first request:
        
        AssertionError: The setup method 'route' can no longer be called on the application. It has already handled its 
        first request, any changes will not be applied consistently.
        Make sure all imports, decorators, functions, etc. needed to set up the application are done before running it.
        """
        cls.app_test._got_first_request = False

        @cls.app_test.route('/hello')
        @api_key_required
        def hello_world():
            return Response("hello, world!")

        @cls.app_test.route('/helloopt')
        @api_key_optional
        def hello_world_opt():
            return Response("hello, world!")

        # Reinstate debug
        cls.app_test.debug = True
        cls.app_test.testing = True
        cls.app_test.login_manager.user_loader(load_account_for_login_manager)

    @classmethod
    def tearDownClass(cls) -> None:
        # put debug back on
        cls.app_test.debug = True

    def test_01_api_role(self):
        """test the new roles added for the API"""
        a1 = models.Account.make_account(email="a1@example.com", username="a1_user", name="a1_name",
                                         roles=["user", "api"], associated_journal_ids=[])
        a1.save(blocking=True)

        # Check an API key was generated on account creation
        a1_key = a1.api_key
        assert a1_key is not None

        # Check we can retrieve the account by its key
        a1_retrieved = models.Account.pull_by_api_key(a1_key)
        assert a1 == a1_retrieved, (a1, a1_retrieved)

        # Check that removing the API role means you don't get a key
        a1.remove_role('api')
        assert a1.api_key is None

    def test_02_api_required_decorator(self):
        """test the api_key_required decorator"""
        a1 = models.Account.make_account(email="a1@example.com", username="a1_user", name="a1_name",
                                         roles=["user", "api"], associated_journal_ids=[])
        a1_key = a1.api_key
        a1.save()               # a1 has api access

        a2 = models.Account.make_account(email="a2@example.com", username="a2_user", name="a2_name",
                                         roles=["user", "api"], associated_journal_ids=[])
        a2_key = a2.api_key     # user gets the key before access is removed
        a2.remove_role('api')
        a2.save(blocking=True)               # a2 does not have api access.

        with self.app_test.test_client() as t_client:
            # Check the authorised user can access our function, but the unauthorised one can't.
            response_authorised = t_client.get('/hello?api_key=' + a1_key)
            assert response_authorised.data == b"hello, world!", response_authorised.data
            assert response_authorised.status_code == 200

            response_denied = t_client.get('/hello?api_key=' + a2_key)
            assert response_denied.status_code == 401

    def test_03_api_optional_decorator(self):
        """test the api_key_optional decorator"""
        a1 = models.Account.make_account(email="a1@example.com", username="a1_user", name="a1_name",
                                         roles=["user", "api"], associated_journal_ids=[])
        a1_key = a1.api_key
        a1.save()               # a1 has api access

        a2 = models.Account.make_account(email="a2@example.com", username="a2_user", name="a2_name",
                                         roles=["user", "api"], associated_journal_ids=[])
        a2_key = a2.api_key     # user gets the key before access is removed
        a2.remove_role('api')
        a2.save(blocking=True)               # a2 does not have api access.

        # There is no a3 - the last test case is just a public call with no API key

        with self.app_test.test_client() as t_client:
            # Check the authorised user can access our function, but the unauthorised one can't.
            response_authorised = t_client.get('/helloopt?api_key=' + a1_key)
            assert response_authorised.data == b"hello, world!"
            assert response_authorised.status_code == 200

            response_denied = t_client.get('/helloopt?api_key=' + a2_key)
            assert response_denied.status_code == 401

            # also check it's ok to not have a key at all
            response_authorised2 = t_client.get('/helloopt')
            assert response_authorised2.data == b"hello, world!"
            assert response_authorised2.status_code == 200

            # but if you do specify a key it needs to exist
            response_denied2 = t_client.get('/helloopt?api_key=nonexistent_key')
            assert response_denied2.status_code == 401
