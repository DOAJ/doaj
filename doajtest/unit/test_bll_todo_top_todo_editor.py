from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import ApplicationFixtureFactory, AccountFixtureFactory, EditorGroupFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import constants
from portality import models
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.lib.paths import rel2abs
from portality.lib import dates


def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "bll_todo_editor"), "top_todo_editor", "test_id",
                               {"test_id" : []})


EXCEPTIONS = {
    "ArgumentException" : exceptions.ArgumentException
}


class TestBLLTopTodoEditor(DoajTestCase):

    def setUp(self):
        super(TestBLLTopTodoEditor, self).setUp()
        self.svc = DOAJ.todoService()

    def tearDown(self):
        super(TestBLLTopTodoEditor, self).tearDown()

    @parameterized.expand(load_cases)
    def test_top_todo(self, name, kwargs):

        account_arg = kwargs.get("account")
        raises_arg = kwargs.get("raises")

        categories = [
            "todo_editor_follow_up_old",
            "todo_editor_stalled",
            "todo_editor_completed",
            "todo_editor_assign_pending"
        ]

        category_args = {
            cat : (
                int(kwargs.get(cat)),
                int(kwargs.get(cat + "_order") if kwargs.get(cat + "_order") != "" else -1)
            ) for cat in categories
        }

        ###############################################
        ## set up

        apps = []
        w = 7 * 24 * 60 * 60

        account = None
        if account_arg == "admin":
            asource = AccountFixtureFactory.make_managing_editor_source()
            account = models.Account(**asource)
        elif account_arg == "editor":
            asource = AccountFixtureFactory.make_editor_source()
            account = models.Account(**asource)
            eg_source = EditorGroupFixtureFactory.make_editor_group_source(editor=account.id)
            eg = models.EditorGroup(**eg_source)
            eg.save(blocking=True)
        elif account_arg == "assed":
            asource = AccountFixtureFactory.make_assed1_source()
            account = models.Account(**asource)
        elif account_arg == "no_role":
            asource = AccountFixtureFactory.make_publisher_source()
            account = models.Account(**asource)

        # Applications that we expect to see reported for some tests
        ############################################################

        # an application created more than 8 weeks ago
        self.build_application("editor_follow_up_old", 2 * w, 9 * w, constants.APPLICATION_STATUS_IN_PROGRESS, apps)

        # an application that was last updated over 6 weeks ago
        self.build_application("editor_stalled", 7 * w, 7 * w, constants.APPLICATION_STATUS_IN_PROGRESS, apps)

        # an application that was modifed recently into the completed status
        self.build_application("editor_completed", 2 * w, 2 * w, constants.APPLICATION_STATUS_COMPLETED, apps)

        # an application that is pending without an editor assigned
        def assign_pending(ap):
            ap.remove_editor()

        self.build_application("editor_assign_pending", 2 * w, 2 * w, constants.APPLICATION_STATUS_PENDING, apps, additional_fn=assign_pending)

        models.Application.blockall([(ap.id, ap.last_updated) for ap in apps])

        # size = int(size_arg)
        size=25

        raises = None
        if raises_arg:
            raises = EXCEPTIONS[raises_arg]

        ###########################################################
        # Execution

        if raises is not None:
            with self.assertRaises(raises):
                self.svc.top_todo(account, size)
        else:
            todos = self.svc.top_todo(account, size)

            actions = {}
            positions = {}
            for i, todo in enumerate(todos):
                for aid in todo["action_id"]:
                    if aid not in actions:
                        actions[aid] = 0
                    actions[aid] += 1
                    if aid not in positions:
                        positions[aid] = []
                    positions[aid].append(i + 1)

            for k, v in category_args.items():
                assert actions.get(k, 0) == v[0]
                if v[1] > -1:
                    assert v[1] in positions.get(k, [])
                else:   # the todo item is not positioned at all
                    assert len(positions.get(k, [])) == 0

    def build_application(self, id, lmu_diff, cd_diff, status, app_registry, additional_fn=None):
        source = ApplicationFixtureFactory.make_application_source()
        ap = models.Application(**source)
        ap.set_id(id)
        ap.set_last_manual_update(dates.before_now(lmu_diff))
        ap.set_created(dates.before_now(cd_diff))
        ap.set_application_status(status)

        if additional_fn is not None:
            additional_fn(ap)

        ap.save()
        app_registry.append(ap)