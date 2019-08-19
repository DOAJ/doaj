from doajtest.helpers import DoajTestCase
from portality import models
from doajtest.fixtures import ApplicationFixtureFactory, DoajXmlArticleFixtureFactory, JournalFixtureFactory
from copy import deepcopy
import json
import time

class TestCrudReturnValues(DoajTestCase):

    def setUp(self):
        super(TestCrudReturnValues, self).setUp()

        account = models.Account.make_account(username="test",
                                              name="Tester",
                                              email="test@test.com",
                                              roles=["publisher", "api"],
                                              associated_journal_ids=['abcdefghijk_journal'])
        account.set_password('password123')
        self.api_key = account.api_key
        account.save()

        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(account.id)
        journal.save()
        time.sleep(1)

    def tearDown(self):
        super(TestCrudReturnValues, self).tearDown()

    def test_01_all_crud(self):

        # we should get a JSON 404 if we try to hit a nonexistent endpoint
        with self.app_test.test_client() as t_client:
            response = t_client.get('/api/v1/not_valid')
            assert response.status_code == 404
            assert response.mimetype == 'application/json'

            response = t_client.post('/api/v1/not_valid')
            assert response.status_code == 404
            assert response.mimetype == 'application/json'

            response = t_client.put('/api/v1/not_valid')
            assert response.status_code == 404
            assert response.mimetype == 'application/json'

            response = t_client.delete('/api/v1/not_valid')
            assert response.status_code == 404
            assert response.mimetype == 'application/json'

            response = t_client.patch('/api/v1/not_valid')
            assert response.status_code == 404
            assert response.mimetype == 'application/json'

            response = t_client.head('/api/v1/not_valid')
            assert response.status_code == 404
            assert response.mimetype == 'application/json'

    def test_02_applications_crud(self):
        # add some data to the index with a Create
        user_data = ApplicationFixtureFactory.incoming_application()
        del user_data["admin"]["current_journal"]

        with self.app_test.test_client() as t_client:
            # log into the app as our user
            self.login(t_client, 'test', 'password123')

            # CREATE a new application
            response = t_client.post('/api/v1/applications?api_key=' + self.api_key, data=json.dumps(user_data))
            assert response.status_code == 201          # 201 "Created"
            assert response.mimetype == 'application/json'

            # Check it gives back a newly created application, with an ID
            new_app_id = json.loads(response.data)['id']
            new_app_loc = json.loads(response.data)['location']
            assert new_app_id is not None
            assert new_app_id in new_app_loc

            # RETRIEVE the same application using the ID
            response = t_client.get('/api/v1/applications/{0}?api_key={1}'.format(new_app_id, self.api_key))
            assert response.status_code == 200          # 200 "OK"
            assert response.mimetype == 'application/json'

            retrieved_application = json.loads(response.data)
            new_app_title = retrieved_application['bibjson']['title']
            assert new_app_title == user_data['bibjson']['title']

            # UPDATE the title of the application
            updated_data = deepcopy(user_data)
            updated_data['bibjson']['title'] = 'This is a new title for this application'
            response = t_client.put('/api/v1/applications/{0}?api_key={1}'.format(new_app_id, self.api_key), data=json.dumps(updated_data))
            assert response.status_code == 204          # 204 "No Content"
            assert response.mimetype == 'application/json'

            response = t_client.get('/api/v1/applications/{0}?api_key={1}'.format(new_app_id, self.api_key))
            retrieved_application = json.loads(response.data)
            new_app_title = retrieved_application['bibjson']['title']
            assert new_app_title == updated_data['bibjson']['title']
            assert new_app_title != user_data['bibjson']['title']

            # DELETE the application
            assert models.Suggestion.pull(new_app_id) is not None
            response = t_client.delete('/api/v1/applications/{0}?api_key={1}'.format(new_app_id, self.api_key))
            assert response.status_code == 204          # 204 "No Content"
            assert response.mimetype == 'application/json'

            # Try to RETRIEVE the Application again - check it isn't there anymore
            response = t_client.get('/api/v1/applications/{0}?api_key={1}'.format(new_app_id, self.api_key))
            assert response.status_code == 404
            assert response.mimetype == 'application/json'

            self.logout(t_client)

    def test_03_articles_crud(self):
        # add some data to the index with a Create
        user_data = DoajXmlArticleFixtureFactory.make_article_source()

        with self.app_test.test_client() as t_client:
            # log into the app as our user
            self.login(t_client, 'test', 'password123')

            # CREATE a new article
            response = t_client.post('/api/v1/articles?api_key=' + self.api_key, data=json.dumps(user_data))
            assert response.status_code == 201          # 201 "Created"
            assert response.mimetype == 'application/json'

            # Check it gives back a newly created article, with an ID
            new_ar_id = json.loads(response.data)['id']
            new_ar_loc = json.loads(response.data)['location']
            assert new_ar_id is not None
            assert new_ar_id in new_ar_loc

            # RETRIEVE the same article using the ID
            response = t_client.get('/api/v1/articles/{0}?api_key={1}'.format(new_ar_id, self.api_key))
            assert response.status_code == 200          # 200 "OK"
            assert response.mimetype == 'application/json'

            retrieved_article = json.loads(response.data)
            new_ar_title = retrieved_article['bibjson']['title']
            assert new_ar_title == user_data['bibjson']['title']

            # UPDATE the title of the article
            updated_data = deepcopy(user_data)
            updated_data['bibjson']['title'] = 'This is a new title for this article'
            response = t_client.put('/api/v1/articles/{0}?api_key={1}'.format(new_ar_id, self.api_key), data=json.dumps(updated_data))
            assert response.status_code == 204          # 204 "No Content"
            assert response.mimetype == 'application/json'

            response = t_client.get('/api/v1/articles/{0}?api_key={1}'.format(new_ar_id, self.api_key))
            retrieved_article = json.loads(response.data)
            new_ar_title = retrieved_article['bibjson']['title']
            assert new_ar_title == updated_data['bibjson']['title']
            assert new_ar_title != user_data['bibjson']['title']

            # DELETE the article
            assert models.Article.pull(new_ar_id) is not None
            response = t_client.delete('/api/v1/articles/{0}?api_key={1}'.format(new_ar_id, self.api_key))
            assert response.status_code == 204          # 204 "No Content"
            assert response.mimetype == 'application/json'

            # Try to RETRIEVE the article again - check it isn't there anymore
            response = t_client.get('/api/v1/applications/{0}?api_key={1}'.format(new_ar_id, self.api_key))
            assert response.status_code == 404
            assert response.mimetype == 'application/json'

    @staticmethod
    def login(app, username, password):
        return app.post('/account/login',
                        data=dict(username=username, password=password),
                        follow_redirects=True)

    @staticmethod
    def logout(app):
        return app.get('/account/logout', follow_redirects=True)
