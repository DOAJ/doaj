from doajtest.fixtures import EditorGroupFixtureFactory
from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from portality import models
from portality.lib import dates

class Autoassign(TestDrive):

    def _account(self, prefix, roles):
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, prefix + " " + un, roles)
        acc.set_password(pw)
        acc.save()
        return acc, pw

    def _draft(self, acc):
        jsource = JournalFixtureFactory.make_journal_source(in_doaj=True, overlay={
            "id": models.Journal.makeid(),
            "created_date": dates.format(dates.before_now(86400)),
            "admin": {
                "editor_group": None,
                "editor": None,
                "owner": acc.id,
            },
            "bibjson": {
                "title": acc.id + " Journal",
            }
        })
        j = models.Journal(**jsource)
        j.save()
        asource = ApplicationFixtureFactory.make_update_request_source(overlay={
            "id": models.Application.makeid(),
            "created_date": dates.format(dates.now()),
            "admin": {
                "application_status": constants.APPLICATION_STATUS_UPDATE_REQUEST,
                "current_journal": j.id,
                "owner": acc.id,
                "editor_group": None,
                "editor": None,
                "date_applied": dates.format(dates.now())
            },
            "bibjson": {
                "title": acc.id + " Update Request",
            }
        })
        ap = models.Application(**asource)
        ap.save()

        return j, ap

    def setup(self) -> dict:
        pub1, pw1 = self._account("Publisher", [constants.ROLE_PUBLISHER])
        pub2, pw2 = self._account("Publisher", [constants.ROLE_PUBLISHER])
        pub3, pw3 = self._account("Publisher", [constants.ROLE_PUBLISHER])
        maned1, pw4 = self._account("Managing Editor", [constants.ROLE_ADMIN])
        maned2, pw5 = self._account("Managing Editor", [constants.ROLE_ADMIN])

        eg1source = EditorGroupFixtureFactory.make_editor_group_source(group_name="Account Mapping", maned=maned1.id)
        eg1 = models.EditorGroup(**eg1source)
        eg1.save()

        eg2source = EditorGroupFixtureFactory.make_editor_group_source(group_name="Country Mapping", maned=maned2.id)
        eg2 = models.EditorGroup(**eg2source)
        eg2.save()

        j1, ap1 = self._draft(pub1)
        j2, ap2 = self._draft(pub2)
        j3, ap3 = self._draft(pub3)

        ur1 = models.URReviewRoute()
        ur1.account_id = pub1.id
        ur1.target = eg1.name
        ur1.save()

        ur2 = models.URReviewRoute()
        ur2.country = "France"
        ur2.target = eg2.name
        ur2.save()

        return {
            "map_by_account": {
                "publisher_username": pub1.id,
                "publisher_password": pw1,
                "update_request": ap1.id,
                "journal": j1.id,
                "editor_group": eg1.name,
                "maned_username": maned1.id,
                "maned_password": pw4
            },
            "map_by_country": {
                "publisher_username": pub2.id,
                "publisher_password": pw2,
                "update_request": ap2.id,
                "journal": j2.id,
                "editor_group": eg2.name,
                "maned_username": maned2.id,
                "maned_password": pw5
            },
            "unmapped": {
                "publisher_username": pub3.id,
                "publisher_password": pw3,
                "draft": ap3.id,
                "journal": j3.id
            }
        }


    def teardown(self, params):
        models.Account.remove_by_id(params["map_by_account"]["publisher_username"])
        models.Account.remove_by_id(params["map_by_country"]["publisher_username"])
        models.Account.remove_by_id(params["unmapped"]["publisher_username"])

        models.Application.remove_by_id(params["map_by_account"]["update_request"])
        models.Application.remove_by_id(params["map_by_country"]["update_request"])
        models.Application.remove_by_id(params["unmapped"]["draft"])

        models.Journal.remove_by_id(params["map_by_country"]["journal"])
        models.Journal.remove_by_id(params["map_by_account"]["journal"])
        models.Journal.remove_by_id(params["unmapped"]["journal"])

        eg = models.EditorGroup.pull_by_key("name", params["map_by_account"]["editor_group"])
        eg.delete()
        eg = models.EditorGroup.pull_by_key("name", params["map_by_country"]["editor_group"])
        eg.delete()

        return {"status": "success"}
