from doajtest import helpers
from doajtest.helpers import DoajTestCase
from portality import models, constants
from portality.util import url_for


class TestViewPublisher(DoajTestCase):

    def test_delete_application__no_such_object(self):
        pwd = 'password'
        un = 'publisher_a'
        acc = models.Account.make_account(un + "@example.com", un, "Publisher " + un, [constants.ROLE_PUBLISHER])
        acc.set_password(pwd)
        acc.save(blocking=True)

        with self.app_test.test_client() as t_client:
            resp = helpers.login(t_client, acc.email, pwd)
            assert resp.status_code == 200

            resp = t_client.get(url_for("publisher.delete_application", application_id='no_such_id'))
            assert resp.status_code == 400
