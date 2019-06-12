import time
import json
from flask import url_for
from portality import constants
from doajtest.fixtures import ApplicationFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models
from portality.api.v1 import ApplicationsBulkApi, Api401Error, Api400Error


class TestCrudApplication(DoajTestCase):

    def setUp(self):
        super(TestCrudApplication, self).setUp()

    def tearDown(self):
        super(TestCrudApplication, self).tearDown()

    def test_01_create_applications_success(self):
        # set up all the bits we need - 10 applications
        data = ApplicationFixtureFactory.incoming_application()
        del data["admin"]["current_journal"]
        dataset = [data] * 10

        # create an account that we'll do the create as
        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")

        # call create on the object (which will save it to the index)
        ids = ApplicationsBulkApi.create(dataset, account)

        # check that we got the right number of ids back
        assert len(ids) == 10

        # let the index catch up
        time.sleep(2)

        # check that each id was actually created
        for id in ids:
            s = models.Suggestion.pull(id)
            assert s is not None

    def test_02_create_applications_fail(self):
        # if the account is dud
        with self.assertRaises(Api401Error):
            data = ApplicationFixtureFactory.incoming_application()
            del data["admin"]["current_journal"]
            dataset = [data] * 10
            ids = ApplicationsBulkApi.create(dataset, None)

        # check that the index is empty, as none of them should have been made
        all = [x for x in models.Suggestion.iterall()]
        assert len(all) == 0

        # if the data is bust
        with self.assertRaises(Api400Error):
            account = models.Account()
            account.set_id("test")
            account.set_name("Tester")
            account.set_email("test@test.com")
            dataset = dataset[:5] + [{"some" : {"junk" : "data"}}] + dataset[5:]
            ids = ApplicationsBulkApi.create(dataset, account)

        # check that the index is empty, as none of them should have been made
        all = [x for x in models.Suggestion.iterall()]
        assert len(all) == 0

    def test_03_delete_application_success(self):
        # set up all the bits we need
        data = ApplicationFixtureFactory.incoming_application()
        del data["admin"]["current_journal"]
        dataset = [data] * 10

        # create the account we're going to work as
        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")
        account.add_role("publisher")

        # call create on the objects (which will save it to the index)
        ids = ApplicationsBulkApi.create(dataset, account)

        # let the index catch up
        time.sleep(2)

        # now delete half of them
        dels = ids[:5]
        ApplicationsBulkApi.delete(dels, account)

        # let the index catch up
        time.sleep(2)

        for id in dels:
            ap = models.Suggestion.pull(id)
            assert ap is None
        for id in ids[5:]:
            ap = models.Suggestion.pull(id)
            assert ap is not None

    def test_04_delete_applications_fail(self):
        # set up all the bits we need
        data = ApplicationFixtureFactory.incoming_application()
        del data["admin"]["current_journal"]
        dataset = [data] * 10

        # create the account we're going to work as
        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")

        # call create on the objects (which will save it to the index)
        ids = ApplicationsBulkApi.create(dataset, account)

        # let the index catch up
        time.sleep(2)

        # call delete on the object in various context that will fail

        # without an account
        with self.assertRaises(Api401Error):
            ApplicationsBulkApi.delete(ids, None)

        # with the wrong account
        account.set_id("other")
        with self.assertRaises(Api400Error):
            ApplicationsBulkApi.delete(ids, account)

        # on the wrong id
        ids.append("adfasdfhwefwef")
        account.set_id("test")
        with self.assertRaises(Api400Error):
            ApplicationsBulkApi.delete(ids, account)

        # on one with a disallowed workflow status
        created = models.Suggestion.pull(ids[3])
        created.set_application_status(constants.APPLICATION_STATUS_ACCEPTED)
        created.save()
        time.sleep(2)

        with self.assertRaises(Api400Error):
            ApplicationsBulkApi.delete(ids, account)

    def test_05_test_via_endpoint(self):
        """ Use a request context to test the API via the route """

        # set up all the bits we need
        data = ApplicationFixtureFactory.incoming_application()
        del data["admin"]["current_journal"]
        dataset = [data] * 10

        # create the main account we're going to work as
        account = models.Account()
        account.set_id("test")
        account.set_name("Tester")
        account.set_email("test@test.com")
        account.generate_api_key()
        account.add_role('publisher')
        account.add_role('api')
        account.save(blocking=True)

        # Add another user who doesn't own these articles
        somebody_else = models.Account()
        somebody_else.set_id("somebody_else")
        somebody_else.set_name("Somebody Else")
        somebody_else.set_email("somebodyelse@test.com")
        somebody_else.generate_api_key()
        somebody_else.add_role('publisher')
        somebody_else.add_role('api')
        somebody_else.save(blocking=True)

        assert account.api_key != somebody_else.api_key

        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                # Create some new applications
                resp = t_client.post(url_for('api_v1.bulk_application_create', api_key=account.api_key),
                                     data=json.dumps(dataset))
                assert resp.status_code == 201
                reply = json.loads(resp.data)
                assert len(reply) == len(dataset)
                first_apl = reply.pop()
                assert first_apl['status'] == 'created'
                # Check we actually created new records
                time.sleep(1)
                assert len(models.Suggestion.all()) == len(dataset)

                # Bulk delete
                all_but_one = [new_art['id'] for new_art in reply]
                resp = t_client.delete(url_for('api_v1.bulk_application_delete', api_key=account.api_key),
                                       data=json.dumps(all_but_one))
                assert resp.status_code == 204
                time.sleep(1)
                # we should have deleted all but one of the applications.
                assert len(models.Suggestion.all()) == 1
                # And our other user isn't allowed to delete the remaining one.
                resp = t_client.delete(url_for('api_v1.bulk_application_delete', api_key=somebody_else.api_key),
                                       data=json.dumps([first_apl['id']]))
                assert resp.status_code == 400


