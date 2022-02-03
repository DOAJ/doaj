from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import ApplicationFixtureFactory, AccountFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality.bll import exceptions
from portality import models
from portality import constants
from portality.lib.paths import rel2abs
from portality.lib import dates
from datetime import datetime


def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "bll_todo"), "top_todo", "test_id",
                               {"test_id" : []})


EXCEPTIONS = {
    "ArgumentException" : exceptions.ArgumentException
}


class TestBLLTopTodo(DoajTestCase):

    def setUp(self):
        super(TestBLLTopTodo, self).setUp()
        self.svc = DOAJ.todoService()

    def tearDown(self):
        super(TestBLLTopTodo, self).tearDown()

    @parameterized.expand(load_cases)
    def test_top_todo(self, name, kwargs):

        account_arg = kwargs.get("account")
        size_arg = kwargs.get("size")
        raises_arg = kwargs.get("raises")

        categories = [
            "todo_maned_stalled",
            "todo_maned_follow_up_old"
        ]

        category_args = {cat : int(kwargs.get(cat)) for cat in categories}

        ###############################################
        ## set up

        apps = []
        w = 7*24*60*60

        # an application stalled for more than 8 weeks
        self.build_application("maned_stalled__maned_old", 10*w, 10*w, constants.APPLICATION_STATUS_IN_PROGRESS, apps)

        # an application that is not stalled
        self.build_application("unstalled", 2*w, 2*w, constants.APPLICATION_STATUS_IN_PROGRESS, apps)

        # an application that is old but rejected
        self.build_application("rejected", 11 * w, 11 * w, constants.APPLICATION_STATUS_REJECTED, apps)

        # an application that was created over 10 weeks ago (but updated recently)
        self.build_application("maned_old", 2 * w, 11 * w, constants.APPLICATION_STATUS_IN_PROGRESS, apps)

        # an application that was created recently
        self.build_application("not_old", 2 * w, 2 * w, constants.APPLICATION_STATUS_IN_PROGRESS, apps)

        # an application that was created over 10 weeks ago and is accepted
        self.build_application("accepted", 12 * w, 12 * w, constants.APPLICATION_STATUS_ACCEPTED, apps)

        models.Application.blockall([(ap.id, ap.last_updated) for ap in apps])

        account = None
        if account_arg == "admin":
            asource = AccountFixtureFactory.make_managing_editor_source()
            account = models.Account(**asource)
        elif account_arg == "editor":
            asource = AccountFixtureFactory.make_editor_source()
            account = models.Account(**asource)
        elif account_arg == "assed":
            asource = AccountFixtureFactory.make_assed1_source()
            account = models.Account(**asource)
        elif account_arg == "no_role":
            asource = AccountFixtureFactory.make_publisher_source()
            account = models.Account(**asource)

        size = int(size_arg)

        raises = None
        if raises_arg:
            raises = EXCEPTIONS[raises_arg]

        ###########################################################
        # Execution

        if raises is not None:
            with self.assertRaises(raises):
                todos = self.svc.top_todo(account, size)
        else:
            todos = self.svc.top_todo(account, size)

            actions = {}
            for todo in todos:
                for aid in todo["action_id"]:
                    if aid not in actions:
                        actions[aid] = 0
                    actions[aid] += 1

            for k, v in category_args:
                assert actions.get(k, 0) == v

            # todo_maned_stalled_expected = int(todo_maned_stalled_arg)
            # assert actions.get(constants.TODO_MANED_STALLED, 0) == todo_maned_stalled_expected
            #
            # todo_maned_follow_up_old_expected = int(todo_maned_follow_up_old_arg)
            # assert actions.get(constants.TODO_MANED_FOLLOW_UP_OLD, 0) == todo_maned_follow_up_old_expected

    def build_application(self, id, lmu_diff, cd_diff, status, app_registry):
        source = ApplicationFixtureFactory.make_application_source()
        ap = models.Application(**source)
        ap.set_id(id)
        ap.set_last_manual_update(dates.before(datetime.utcnow(), lmu_diff))  # 10 weeks ago
        ap.set_created(dates.before(datetime.utcnow(), cd_diff))  # 10 weeks ago
        ap.set_application_status(status)
        ap.save()
        app_registry.append(ap)