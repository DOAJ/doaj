from doajtest.helpers import DoajTestCase
from portality import models
from doajtest.fixtures import ApplicationFixtureFactory, ArticleFixtureFactory, JournalFixtureFactory
from copy import deepcopy
import json
import time


class TestCrudReturnValues(DoajTestCase):

    def setUp(self):
        super(TestCrudReturnValues, self).setUp()

        account = models.Account.make_account(email="test@test.com", username="test", name="Tester",
                                              roles=["publisher", "api"],
                                              associated_journal_ids=['abcdefghijk_journal'])
        account.set_password('password123')
        self.api_key = account.api_key
        self.account = account
        account.save()
        time.sleep(1)

    def tearDown(self):
        super(TestCrudReturnValues, self).tearDown()

    def test_01_all_crud(self):

        # we should get a JSON 404 if we try to hit a nonexistent endpoint
        with self.app_test.test_client() as t_client:
            response = t_client.get('/api/v2/not_valid')
            assert response.status_code == 404
            assert response.mimetype == 'application/json'

            response = t_client.post('/api/v2/not_valid')
            assert response.status_code == 404
            assert response.mimetype == 'application/json'

            response = t_client.put('/api/v2/not_valid')
            assert response.status_code == 404
            assert response.mimetype == 'application/json'

            response = t_client.delete('/api/v2/not_valid')
            assert response.status_code == 404
            assert response.mimetype == 'application/json'

            response = t_client.patch('/api/v2/not_valid')
            assert response.status_code == 404
            assert response.mimetype == 'application/json'

            response = t_client.head('/api/v2/not_valid')
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
            response = t_client.post('/api/v2/applications?api_key=' + self.api_key, data=json.dumps(user_data))
            assert response.status_code == 201          # 201 "Created"
            assert response.mimetype == 'application/json'

            # Check it gives back a newly created application, with an ID
            new_app_id = json.loads(response.data.decode("utf-8"))['id']
            new_app_loc = json.loads(response.data.decode("utf-8"))['location']
            assert new_app_id is not None
            assert new_app_id in new_app_loc

            # RETRIEVE the same application using the ID
            response = t_client.get('/api/v2/applications/{0}?api_key={1}'.format(new_app_id, self.api_key))
            assert response.status_code == 200          # 200 "OK"
            assert response.mimetype == 'application/json'

            retrieved_application = json.loads(response.data.decode("utf-8"))
            new_app_title = retrieved_application['bibjson']['title']
            assert new_app_title == user_data['bibjson']['title']

            # UPDATE the title of the application
            updated_data = deepcopy(user_data)
            updated_data['bibjson']['title'] = 'This is a new title for this application'
            response = t_client.put('/api/v2/applications/{0}?api_key={1}'.format(new_app_id, self.api_key), data=json.dumps(updated_data))
            assert response.status_code == 204          # 204 "No Content"
            assert response.mimetype == 'application/json'

            response = t_client.get('/api/v2/applications/{0}?api_key={1}'.format(new_app_id, self.api_key))
            retrieved_application = json.loads(response.data.decode("utf-8"))
            new_app_title = retrieved_application['bibjson']['title']
            assert new_app_title == updated_data['bibjson']['title']
            assert new_app_title != user_data['bibjson']['title']

            # DELETE the application
            assert models.Suggestion.pull(new_app_id) is not None
            response = t_client.delete('/api/v2/applications/{0}?api_key={1}'.format(new_app_id, self.api_key))
            assert response.status_code == 204          # 204 "No Content"
            assert response.mimetype == 'application/json'

            # Try to RETRIEVE the Application again - check it isn't there anymore
            response = t_client.get('/api/v2/applications/{0}?api_key={1}'.format(new_app_id, self.api_key))
            assert response.status_code == 404
            assert response.mimetype == 'application/json'

            self.logout(t_client)

    def test_03_articles_crud(self):
        # add some data to the index with a Create
        user_data = ArticleFixtureFactory.make_article_source()

        # Add a journal so we can assign articles to it
        journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        journal.set_owner(self.account.id)
        journal.save(blocking=True)

        with self.app_test.test_client() as t_client:
            # log into the app as our user
            self.login(t_client, 'test', 'password123')

            # CREATE a new article
            response = t_client.post('/api/v2/articles?api_key=' + self.api_key, data=json.dumps(user_data))
            assert response.status_code == 201          # 201 "Created"
            assert response.mimetype == 'application/json'

            # Check it gives back a newly created article, with an ID
            new_ar_id = json.loads(response.data.decode("utf-8"))['id']
            new_ar_loc = json.loads(response.data.decode("utf-8"))['location']
            assert new_ar_id is not None
            assert new_ar_id in new_ar_loc

            # RETRIEVE the same article using the ID
            response = t_client.get('/api/v2/articles/{0}?api_key={1}'.format(new_ar_id, self.api_key))
            assert response.status_code == 200          # 200 "OK"
            assert response.mimetype == 'application/json'

            retrieved_article = json.loads(response.data.decode("utf-8"))
            new_ar_title = retrieved_article['bibjson']['title']
            assert new_ar_title == user_data['bibjson']['title']

            # UPDATE the title of the article
            updated_data = deepcopy(user_data)
            updated_data['bibjson']['title'] = 'This is a new title for this article'
            response = t_client.put('/api/v2/articles/{0}?api_key={1}'.format(new_ar_id, self.api_key), data=json.dumps(updated_data))
            assert response.status_code == 204          # 204 "No Content"
            assert response.mimetype == 'application/json'

            response = t_client.get('/api/v2/articles/{0}?api_key={1}'.format(new_ar_id, self.api_key))
            retrieved_article = json.loads(response.data.decode("utf-8"))
            new_ar_title = retrieved_article['bibjson']['title']
            assert new_ar_title == updated_data['bibjson']['title']
            assert new_ar_title != user_data['bibjson']['title']

            # DELETE the article
            assert models.Article.pull(new_ar_id) is not None
            response = t_client.delete('/api/v2/articles/{0}?api_key={1}'.format(new_ar_id, self.api_key))
            assert response.status_code == 204          # 204 "No Content"
            assert response.mimetype == 'application/json'

            # Try to RETRIEVE the article again - check it isn't there anymore
            response = t_client.get('/api/v2/applications/{0}?api_key={1}'.format(new_ar_id, self.api_key))
            assert response.status_code == 404
            assert response.mimetype == 'application/json'

    def test_04_article_structure_exceptions(self):
        # add some data to the index with a Create
        user_data = ArticleFixtureFactory.make_article_source()

        with self.app_test.test_client() as t_client:
            # log into the app as our user
            self.login(t_client, 'test', 'password123')

            # attempt to CREATE a new article with invalid JSON
            bad_data = json.dumps(user_data) + 'blarglrandomblah'
            response = t_client.post('/api/v2/articles?api_key=' + self.api_key, data=bad_data)
            assert response.status_code == 400  # 400 "Bad Request"
            assert response.mimetype == 'application/json'
            assert 'Supplied data was not valid JSON' in response.json['error']

            # attempt to CREATE a new article with too many keywords (exception propagates from DataObj)
            too_many_kwds = deepcopy(user_data)
            too_many_kwds['bibjson']['keywords'] = ['one', 'two', 'three', 'four', 'five', 'six', 'SEVEN']

            response = t_client.post('/api/v2/articles?api_key=' + self.api_key, data=json.dumps(too_many_kwds))
            assert response.status_code == 400  # 400 "Bad Request"
            assert response.mimetype == 'application/json'
            assert 'maximum of 6 keywords' in response.json['error']

            # attempt to CREATE an article with a missing required field (exception propagates from DataObj)
            missing_title = deepcopy(user_data)
            del missing_title['bibjson']['title']

            response = t_client.post('/api/v2/articles?api_key=' + self.api_key, data=json.dumps(missing_title))
            assert response.status_code == 400  # 400 "Bad Request"
            assert response.mimetype == 'application/json'
            assert "Field 'title' is required but not present" in response.json['error']

    @staticmethod
    def login(app, username, password):
        return app.post('/account/login',
                        data=dict(username=username, password=password),
                        follow_redirects=True)

    @staticmethod
    def logout(app):
        return app.get('/account/logout', follow_redirects=True)
