from doajtest.helpers import DoajTestCase
from portality import models
import time


class TestApiErrors(DoajTestCase):

    def setUp(self):
        super(TestApiErrors, self).setUp()

    def tearDown(self):
        super(TestApiErrors, self).tearDown()

    def test_01_api_404(self):
        with self.app_test.test_client() as t_client:
            # On API blueprint, check we get an HTML doc page but a json 404
            response = t_client.get('/api/v2/docs')
            assert response.status_code == 200
            assert response.mimetype == 'text/html'

            response = t_client.get('/api/v2/not_valid')
            assert response.status_code == 404
            assert response.mimetype == 'application/json'

            # But the rest of the app gives the HTML 404
            response = t_client.get('/about')
            assert response.status_code == 200
            assert response.mimetype == 'text/html'

            response = t_client.get('/not_about')
            assert response.status_code == 404
            assert response.mimetype == 'text/html'


    def test_02_api_400(self):

        with self.app_test.test_client() as t_client:
            # a normal journal query, with a valid page number
            response = t_client.get('/api/v2/search/journals/query_string?page=1')
            assert response.status_code == 200

            # a bad request, the page number is invalid
            response = t_client.get('/api/v2/search/journals/query_string?page=@')
            assert response.status_code == 400
            assert response.mimetype == 'application/json'
            # check the error string has appeared in the response
            assert b"Page number was not an integer" in response.data

    def test_03_api_401(self):
        # make a user account for the authorisation test
        a1 = models.Account.make_account(email="a1@example.com", username="a1_user", name="a1_name",
                                         roles=["user", "api"], associated_journal_ids=[])
        a1_key = a1.api_key
        a1.save()               # a1 has api access

        # populate the index with an application owned by this owner
        a = models.Suggestion()
        a.set_owner("a1_user")
        bj = a.bibjson()
        bj.title = "Test Suggestion Title"
        bj.add_identifier(bj.P_ISSN, "0000-0000")
        bj.publisher = "Test Publisher"
        bj.add_url("http://homepage.com", "homepage")
        a.save()

        time.sleep(1)

        with self.app_test.test_client() as t_client:
            # a successful authenticated query, giving the right result
            response = t_client.get('/api/v2/search/applications/issn%3A0000-0000?api_key=' + a1_key)
            assert response.status_code == 200, "first assertions: received: {}".format(response.status_code)
            # check we got a result by looking for something that must be in the results
            assert b"Test Suggestion Title" in response.data, "first assertions: data received: {}".format(response.data)

            # and a successful but empty search for an application that doesn't belong to them
            a.set_owner('not_a1_user')
            a.save()
            time.sleep(1)
            response = t_client.get('/api/v2/search/applications/issn%3A0000-0000?api_key=' + a1_key)
            assert response.status_code == 200, "second assertions: received: {}".format(response.status_code)
            assert b"Test Suggestion Title" not in response.data, "second assertions: received data: {}".format(response.data)

            # and we expect a json 401 error if we fail to authenticate
            spurious_key = 'blahblahblah'
            response = t_client.get('/api/v2/search/applications/issn%3A0000-0000?api_key=' + spurious_key)
            assert response.status_code == 401, "third assertions: received: {}".format(response.status_code)
            assert response.mimetype == 'application/json', "third assertions: mimetype received: {}".format(response.mimetype)
            assert b"An API Key is required to access this." in response.data, "third assertions: data received: {}".format(response.data)
