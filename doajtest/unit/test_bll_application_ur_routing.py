import os, csv, io

from doajtest.fixtures import AccountFixtureFactory, EditorGroupFixtureFactory, ApplicationFixtureFactory
from doajtest.helpers import DoajTestCase
from doajtest.mocks.response import ResponseMockFactory
from portality.lib.thread_utils import wait_until
from portality.bll import DOAJ
from portality import models
from portality.lib import paths
import requests
from portality.bll import exceptions
from portality.models import URReviewRoute

from portality.util import patch_config
from portality.core import app
from portality.lib import dates

EXAMPLE_FILES_DIR = paths.rel2abs(__file__, "..", "example_files")

class TestURRouting(DoajTestCase):

    def setUp(self):
        super(TestURRouting, self).setUp()
        self.get = requests.get
        self.originals = patch_config(app, {
            "AUTO_ASSIGN_EDITOR_BY_PUBLISHER_SHEET": "http://example.com/editor_by_publisher",
            "AUTO_ASSIGN_EDITOR_BY_COUNTRY_SHEET": "http://example.com/editor_by_country",
        })

    def tearDown(self):
        super(TestURRouting, self).tearDown()
        requests.get = self.get
        patch_config(app, self.originals)

    def test_01_retrieve_and_map_success(self):
        ebp = os.path.join(EXAMPLE_FILES_DIR, "editor_by_publisher.csv")
        ebc = os.path.join(EXAMPLE_FILES_DIR, "editor_by_country.csv")

        ebp_map = []
        ebc_map = []

        with open(ebp, "r") as ebp_file, open(ebc, "r") as ebc_file:
            ebpcsv = csv.reader(ebp_file)
            ebccsv = csv.reader(ebc_file)

            accounts = {}
            groups = {}
            for row in ebpcsv:
                if row[0] == "Publisher":
                    continue

                if row[1] not in accounts:
                    source = AccountFixtureFactory.make_publisher_source()
                    source["id"] = row[1]
                    acc = models.Account(**source)
                    acc.save()
                    accounts[row[1]] = acc

                if row[2] not in accounts:
                    source2 = AccountFixtureFactory.make_managing_editor_source()
                    source2["id"] = row[2]
                    editor = models.Account(**source2)
                    editor.save()
                    accounts[row[2]] = editor

                if row[2] not in groups:
                    source3 = EditorGroupFixtureFactory.make_editor_group_source(group_name=row[2], editor=row[2], maned=row[2])
                    group = models.EditorGroup(**source3)
                    group.save()
                    groups[row[2]] = group

                ebp_map.append((row[1], row[2]))

            for row in ebccsv:
                if row[0] == "Country":
                    continue

                if row[1] not in accounts:
                    source = AccountFixtureFactory.make_managing_editor_source()
                    source["id"] = row[1]
                    editor = models.Account(**source2)
                    editor.save()
                    accounts[row[1]] = editor

                if row[1] not in groups:
                    source2 = EditorGroupFixtureFactory.make_editor_group_source(group_name=row[1], editor=row[1], maned=row[1])
                    group = models.EditorGroup(**source2)
                    group.save()
                    groups[row[1]] = group

                ebc_map.append((row[0], row[1]))

        assert len(ebp_map) == 4
        assert len(ebc_map) == 4

        models.Account.blockall([(a.id, a.last_updated) for a in accounts.values()])
        models.EditorGroup.blockall([(g.id, g.last_updated) for g in groups.values()])

        requests.get = ResponseMockFactory.get_file({
            "http://example.com/editor_by_publisher": open(ebp, "r"),
            "http://example.com/editor_by_country": open(ebc, "r")
        })

        svc = DOAJ.applicationService()
        routers = svc.retrieve_ur_editor_group_sheets(prune=False)

        assert len(routers) == 8
        wait_until(lambda: models.URReviewRoute.count() == 8)

        for acc, target in ebp_map:
            route = models.URReviewRoute.by_account(acc)
            assert route.target == target
            assert route.account_id == acc
            assert route.country is None

        for country, target in ebc_map:
            route = models.URReviewRoute.by_country_name(country)
            assert route.target == target
            assert route.account_id is None
            assert route.country == country

    def test_02_retrieve_fail(self):
        ebp = os.path.join(EXAMPLE_FILES_DIR, "editor_by_publisher.csv")
        ebc = os.path.join(EXAMPLE_FILES_DIR, "editor_by_country.csv")

        with open(ebp, "r") as ebp_file, open(ebc, "r") as ebc_file:
            ebp_content = ebp_file.read()
            ebc_content = ebc_file.read()

        svc = DOAJ.applicationService()

        # fail to retieve editor by publisher
        requests.get = ResponseMockFactory.get_failure({
            "http://example.com/editor_by_publisher": (400, "Bad Request"),
            "http://example.com/editor_by_country": (200, ebp_content)
        })

        with self.assertRaises(exceptions.RemoteServiceException):
            routes = svc.retrieve_ur_editor_group_sheets(prune=False)

        # fail to retrieve editor by country
        requests.get = ResponseMockFactory.get_failure({
            "http://example.com/editor_by_publisher": (200, ebp_content),
            "http://example.com/editor_by_country": (400, "Bad Request")
        })

        with self.assertRaises(exceptions.RemoteServiceException):
            routes = svc.retrieve_ur_editor_group_sheets(prune=False)

        # empty response to editor by publisher
        requests.get = ResponseMockFactory.get_failure({
            "http://example.com/editor_by_publisher": (200, ""),
            "http://example.com/editor_by_country": (200, ebp_content)
        })

        with self.assertRaises(ValueError):
            routes = svc.retrieve_ur_editor_group_sheets(prune=False)

        # empty response to editor by country
        requests.get = ResponseMockFactory.get_failure({
            "http://example.com/editor_by_publisher": (200, ebp_content),
            "http://example.com/editor_by_country": (200, "")
        })
        with self.assertRaises(ValueError):
            routes = svc.retrieve_ur_editor_group_sheets(prune=False)

    def test_03_retrieve_invalid(self):
        ebp = os.path.join(EXAMPLE_FILES_DIR, "editor_by_publisher.csv")
        ebc = os.path.join(EXAMPLE_FILES_DIR, "editor_by_country.csv")

        svc = DOAJ.applicationService()

        # accound data not supplied
        invalid_data = "Publisher,Account,Assign to...\nMissing Account,,Group1"
        stream = io.StringIO(invalid_data.strip())
        requests.get = ResponseMockFactory.get_file({
            "http://example.com/editor_by_publisher": stream,
            "http://example.com/editor_by_country": open(ebc, "r")
        })
        with self.assertRaises(ValueError):
            svc.retrieve_ur_editor_group_sheets(prune=False)

        # target group not supplied
        invalid_data = "Publisher,Account,Assign to...\nMissing Account,1234567890,"
        stream = io.StringIO(invalid_data.strip())
        requests.get = ResponseMockFactory.get_file({
            "http://example.com/editor_by_publisher": stream,
            "http://example.com/editor_by_country": open(ebc, "r")
        })
        with self.assertRaises(ValueError):
            svc.retrieve_ur_editor_group_sheets(prune=False)

        # country not supplied
        invalid_data = "Country,Assign to...\n,Group1"
        stream = io.StringIO(invalid_data.strip())
        requests.get = ResponseMockFactory.get_file({
            "http://example.com/editor_by_publisher": open(ebp, "r"),
            "http://example.com/editor_by_country": stream
        })
        with self.assertRaises(ValueError):
            svc.retrieve_ur_editor_group_sheets(prune=False)

        # group not supplied
        invalid_data = "Country,Assign to...\nUnited Kingdom,"
        stream = io.StringIO(invalid_data.strip())
        requests.get = ResponseMockFactory.get_file({
            "http://example.com/editor_by_publisher": open(ebp, "r"),
            "http://example.com/editor_by_country": stream
        })
        with self.assertRaises(ValueError):
            svc.retrieve_ur_editor_group_sheets(prune=False)

    def test_04_retrieve_objects_not_found(self):
        data = "Publisher,Account,Assign to...\nPublisher1,1234567890,Group1"
        null = "Country,Assign to..."

        svc = DOAJ.applicationService()

        # account not found
        stream = io.StringIO(data.strip())
        null_stream = io.StringIO(null.strip())
        with self.assertRaises(ValueError):
            requests.get = ResponseMockFactory.get_file({
                "http://example.com/editor_by_publisher": stream,
                "http://example.com/editor_by_country": null_stream
            })
            svc.retrieve_ur_editor_group_sheets(prune=False)

        # create the account
        source = AccountFixtureFactory.make_publisher_source()
        source["id"] = "1234567890"
        acc = models.Account(**source)
        acc.save(blocking=True)

        # group not found
        stream = io.StringIO(data.strip())
        null_stream = io.StringIO(null.strip())
        with self.assertRaises(ValueError):
            requests.get = ResponseMockFactory.get_file({
                "http://example.com/editor_by_publisher": stream,
                "http://example.com/editor_by_country": null_stream
            })
            svc.retrieve_ur_editor_group_sheets(prune=False)

        # create the group
        source = EditorGroupFixtureFactory.make_editor_group_source(group_name="Group1", editor="editor1", maned="maned1")
        group = models.EditorGroup(**source)
        group.save(blocking=True)

        # proof that it now works
        stream = io.StringIO(data.strip())
        null_stream = io.StringIO(null.strip())
        requests.get = ResponseMockFactory.get_file({
            "http://example.com/editor_by_publisher": stream,
            "http://example.com/editor_by_country": null_stream
        })
        svc.retrieve_ur_editor_group_sheets(prune=False)

    def test_05_prune(self):
        svc = DOAJ.applicationService()

        # create some URReviewRoutes that are 2 days old
        blocks = []
        for i in range(5):
            review = URReviewRoute()
            review.account_id = f"account_{i}"
            review.target = f"target_{i}"
            review.set_created(dates.format(dates.before_now(2 * 86400)))
            review.save()
            blocks.append((review.id, review.last_updated))
        URReviewRoute.blockall(blocks)

        # request a prune of URReviewRoutes older than 1 day
        deleted = svc.prune_ur_review_routes(cutoff=dates.before_now(86400))

        # none should be deleted, as although they are older than the cutoff, this would leave nothing
        # in the routing table
        assert deleted == 0
        assert URReviewRoute.count() == 5

        # now create a couple more sets and we'll try removing them

        # 5 days old
        blocks = []
        for i in range(5):
            review = URReviewRoute()
            review.account_id = f"account_{i}"
            review.target = f"target_{i}"
            review.set_created(dates.format(dates.before_now(5 * 86400)))
            review.save()
            blocks.append((review.id, review.last_updated))
        URReviewRoute.blockall(blocks)

        # 10 days old
        blocks = []
        for i in range(5):
            review = URReviewRoute()
            review.account_id = f"account_{i}"
            review.target = f"target_{i}"
            review.set_created(dates.format(dates.before_now(10 * 86400)))
            review.save()
            blocks.append((review.id, review.last_updated))
        URReviewRoute.blockall(blocks)

        # request a prune of URReviewRoutes older than 12 days, which is older
        # than everything, so should have no effect
        deleted = svc.prune_ur_review_routes(cutoff=dates.before_now(12 * 86400))
        wait_until(lambda: URReviewRoute.count() == 15)
        assert deleted == 0
        assert URReviewRoute.count() == 15

        # request a prune of URReviewRoutes older than 8 days, which should
        # delete the 10 day old ones
        deleted = svc.prune_ur_review_routes(cutoff=dates.before_now(8 * 86400))
        wait_until(lambda: URReviewRoute.count() == 10)
        assert deleted == 5
        assert URReviewRoute.count() == 10

        # request a prune of URReviewRoutes older than 3 days, which should
        # delete the 5 day old ones
        deleted = svc.prune_ur_review_routes(cutoff=dates.before_now(3 * 86400))
        wait_until(lambda: URReviewRoute.count() == 5)
        assert deleted == 5
        assert URReviewRoute.count() == 5

    def test_06_auto_assign(self):
        current_account = models.URReviewRoute()
        current_account.account_id = "known_account"
        current_account.target = "A"
        current_account.set_created(dates.format(dates.before_now(86400)))
        current_account.save()

        old_account = models.URReviewRoute()
        old_account.account_id = "known_account"
        old_account.target = "B"
        old_account.set_created(dates.format(dates.before_now(2 * 86400)))
        old_account.save()

        current_country = models.URReviewRoute()
        current_country.country = "France"
        current_country.target = "C"
        current_country.set_created(dates.format(dates.before_now(86400)))
        current_country.save()

        old_country = models.URReviewRoute()
        old_country.country = "France"
        old_country.target = "D"
        old_country.set_created(dates.format(dates.before_now(2 * 86400)))
        old_country.save()

        eg1_source = EditorGroupFixtureFactory.make_editor_group_source(group_name="A", editor="editor1", maned="maned1")
        eg1 = models.EditorGroup(**eg1_source)
        eg1.save()
        eg2_source = EditorGroupFixtureFactory.make_editor_group_source(group_name="C", editor="editor2", maned="maned2")
        eg2 = models.EditorGroup(**eg2_source)
        eg2.save()

        models.URReviewRoute.blockall([
            (current_account.id, current_account.last_updated),
            (old_account.id, old_account.last_updated),
            (current_country.id, current_country.last_updated),
            (old_country.id, old_country.last_updated)
        ])

        models.EditorGroup.blockall([
            (eg1.id, eg1.last_updated),
            (eg2.id, eg2.last_updated)
        ])


        svc = DOAJ.applicationService()

        # An application with a matching account and unmatched country, should match the account's preference
        source = ApplicationFixtureFactory.make_update_request_source({
            "admin": {
                "editor": None,
                "editor_group": None,
                "owner": "known_account"
            },
            "bibjson": {
                "publisher": {
                    "country": "DE"
                }
            }
        })
        application = models.Application(**source)
        svc.auto_assign_ur_editor_group(application)
        assert application.editor_group == "A"

        # An application with a matching account and country, should match the account's preference
        source = ApplicationFixtureFactory.make_update_request_source({
            "admin": {
                "editor": None,
                "editor_group": None,
                "owner": "known_account"
            },
            "bibjson": {
                "publisher": {
                    "country": "FR"
                }
            }
        })
        application = models.Application(**source)
        svc.auto_assign_ur_editor_group(application)
        assert application.editor_group == "A"

        # An application with an unmatching account and matching country, should match the country's preference
        source = ApplicationFixtureFactory.make_update_request_source({
            "admin": {
                "editor": None,
                "editor_group": None,
                "owner": "unknown_account"
            },
            "bibjson": {
                "publisher": {
                    "country": "FR"
                }
            }
        })
        application = models.Application(**source)
        svc.auto_assign_ur_editor_group(application)
        assert application.editor_group == "C"

        # An application with a unmatching account and country, should not be routed
        source = ApplicationFixtureFactory.make_update_request_source({
            "admin": {
                "editor": None,
                "editor_group": None,
                "owner": "unknown_account"
            },
            "bibjson": {
                "publisher": {
                    "country": "DE"
                }
            }
        })
        application = models.Application(**source)
        svc.auto_assign_ur_editor_group(application)
        assert application.editor_group is None


