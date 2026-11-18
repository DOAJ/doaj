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
            assert resp.status_code == 404

    def test_update_request__not_owner_redirects_to_journals(self):
        """ A publisher who is not the owner is sent to their journals list with a message, not a 404 """
        from doajtest.fixtures import JournalFixtureFactory
        from portality.ui.messages import Messages

        pwd = 'password'
        owner = models.Account.make_account("owner@example.com", "owner", "Owner", [constants.ROLE_PUBLISHER])
        owner.save()
        other = models.Account.make_account("other@example.com", "other", "Other", [constants.ROLE_PUBLISHER])
        other.set_password(pwd)
        other.save(blocking=True)

        j = JournalFixtureFactory.make_legacy_journal_object(in_doaj=True)
        j.set_owner(owner.id)
        j.save(blocking=True)

        with self.app_test.test_client() as t_client:
            resp = helpers.login(t_client, other.email, pwd)
            assert resp.status_code == 200

            resp = t_client.get(url_for("publisher.update_request", journal_id=j.id))
            assert resp.status_code == 302
            assert resp.location.endswith(url_for("publisher.journals"))

            with t_client.session_transaction() as sess:
                assert ("info", Messages.JOURNAL__YOU_ARE_NOT_OWNER) in sess.get("_flashes", [])
