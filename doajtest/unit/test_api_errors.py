from doajtest.helpers import DoajTestCase
from portality import models
from portality.app import app
import time


class TestApiErrors(DoajTestCase):

    def setUp(self):
        super(TestApiErrors, self).setUp()

    def tearDown(self):
        super(TestApiErrors, self).tearDown()

    def test_01_api_404(self):
        with app.test_client() as t_client:
            # On API blueprint, check we get an HTML doc page but a json 404
            response = t_client.get('/api/v1/docs')
            assert response.status_code == 200
            assert response.mimetype == 'text/html'

            response = t_client.get('/api/v1/not_valid')
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

        with app.test_client() as t_client:
            # a normal journal query, with a valid page number
            response = t_client.get('/api/v1/search/journals/query_string?page=1')
            assert response.status_code == 200

            # a bad request, the page number is invalid
            response = t_client.get('/api/v1/search/journals/query_string?page=@')
            assert response.status_code == 400
            assert response.mimetype == 'application/json'
            # check the error string has appeared in the response
            assert "Page number was not an integer" in response.data

    def test_03_api_401(self):
        # make a user account for the authorisation test
        a1 = models.Account.make_account(username="a1_user", name="a1_name", email="a1@example.com", roles=["user", "api"], associated_journal_ids=[])
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

        with app.test_client() as t_client:
            # a successful authenticated query, giving the right result
            response = t_client.get('/api/v1/search/applications/issn%3A0000-0000?api_key=' + a1_key)
            assert response.status_code == 200
            # check we got a result by looking for something that must be in the results
            assert "Test Suggestion Title" in response.data

            # and a successful but empty search for an application that doesn't belong to them
            a.set_owner('not_a1_user')
            a.save()
            time.sleep(1)
            response = t_client.get('/api/v1/search/applications/issn%3A0000-0000?api_key=' + a1_key)
            assert response.status_code == 200
            assert "Test Suggestion Title" not in response.data

            # and we expect a json 401 error if we fail to authenticate
            spurious_key = 'blahblahblah'
            response = t_client.get('/api/v1/search/applications/issn%3A0000-0000?api_key=' + spurious_key)
            assert response.status_code == 401
            assert response.mimetype == 'application/json'
            assert "An API Key is required to access this." in response.data
