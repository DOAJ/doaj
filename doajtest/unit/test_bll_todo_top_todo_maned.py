from combinatrix.testintegration import load_parameter_sets
from doajtest.fixtures import ApplicationFixtureFactory, AccountFixtureFactory, EditorGroupFixtureFactory
from doajtest.helpers import DoajTestCase, wait_until_no_es_incomplete_tasks
from parameterized import parameterized
from portality import constants
from portality import models
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.lib import dates
from portality.lib.paths import rel2abs


def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "bll_todo_maned"), "top_todo_maned", "test_id",
                               {"test_id" : []})


EXCEPTIONS = {
    "ArgumentException" : exceptions.ArgumentException
}


class TestBLLTopTodoManed(DoajTestCase):

    def setUp(self):
        super(TestBLLTopTodoManed, self).setUp()
        self.svc = DOAJ.todoService()

    def tearDown(self):
        super(TestBLLTopTodoManed, self).tearDown()

    @parameterized.expand(load_cases)
    def test_top_todo(self, name, kwargs):

        account_arg = kwargs.get("account")
        raises_arg = kwargs.get("raises")

        categories = [
            "todo_maned_stalled",
            "todo_maned_follow_up_old",
            "todo_maned_ready",
            "todo_maned_completed",
            "todo_maned_assign_pending",
            "todo_maned_new_update_request",
            "todo_maned_on_hold"
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
            eg_source = EditorGroupFixtureFactory.make_editor_group_source(maned=account.id)
            eg = models.EditorGroup(**eg_source)
            eg.save(blocking=True)
        elif account_arg == "editor":
            asource = AccountFixtureFactory.make_editor_source()
            account = models.Account(**asource)
        elif account_arg == "assed":
            asource = AccountFixtureFactory.make_assed1_source()
            account = models.Account(**asource)
        elif account_arg == "no_role":
            asource = AccountFixtureFactory.make_publisher_source()
            account = models.Account(**asource)

        # Applications that we expect to see reported for some tests
        ############################################################

        # an application stalled for more than 8 weeks (todo_maned_stalled)
        self.build_application("maned_stalled", 9 * w, 9 * w, constants.APPLICATION_STATUS_IN_PROGRESS, apps)

        # an application that was created over 10 weeks ago (but updated recently) (todo_maned_follow_up_old)
        self.build_application("maned_follow_up_old", 2 * w, 11 * w, constants.APPLICATION_STATUS_IN_PROGRESS, apps)

        # an application that was modifed recently into the ready status (todo_maned_ready)
        self.build_application("maned_ready", 2 * w, 2 * w, constants.APPLICATION_STATUS_READY, apps)

        # an application that was modifed recently into the ready status (todo_maned_completed)
        self.build_application("maned_completed", 3 * w, 3 * w, constants.APPLICATION_STATUS_COMPLETED, apps)

        # an application that was modifed recently into the ready status (todo_maned_assign_pending)
        def assign_pending(ap):
            ap.remove_editor()

        self.build_application("maned_assign_pending", 4 * w, 4 * w, constants.APPLICATION_STATUS_PENDING, apps,
                               assign_pending)

        # an update request
        self.build_application("maned_update_request", 5 * w, 5 * w, constants.APPLICATION_STATUS_UPDATE_REQUEST, apps,
                               update_request=True)

        # an application that was modifed recently into the ready status (todo_maned_completed)
        self.build_application("maned_on_hold", 2 * w, 2 * w, constants.APPLICATION_STATUS_ON_HOLD, apps)

        # Applications that should never be reported
        ############################################

        # an application that is not stalled
        # counter to maned_stalled
        #           maned_follow_up_old
        #           maned_ready
        #           maned_completed
        #           maned_assign_pending
        self.build_application("not_stalled__not_old", 2 * w, 2 * w, constants.APPLICATION_STATUS_IN_PROGRESS, apps)

        # an application that is old but rejected
        # counter to maned_stalled
        #           maned_follow_up_old
        #           maned_ready
        #           maned_completed
        #           maned_assign_pending
        self.build_application("old_rejected", 11 * w, 11 * w, constants.APPLICATION_STATUS_REJECTED, apps)

        # an application that was created/modified over 10 weeks ago and is accepted
        # counter to maned_stalled
        #           maned_follow_up_old
        #           maned_ready
        #           maned_completed
        #           maned_assign_pending
        self.build_application("old_accepted", 12 * w, 12 * w, constants.APPLICATION_STATUS_ACCEPTED, apps)

        # an application that was recently completed (<2wk)
        # counter to maned_stalled
        #           maned_follow_up_old
        #           maned_ready
        #           maned_completed
        #           maned_assign_pending
        self.build_application("old_accepted", 1 * w, 1 * w, constants.APPLICATION_STATUS_COMPLETED, apps)

        # pending application with no assed younger than 2 weeks
        # counter to maned_stalled
        #           maned_follow_up_old
        #           maned_ready
        #           maned_completed
        #           maned_assign_pending
        self.build_application("not_assign_pending", 1 * w, 1 * w, constants.APPLICATION_STATUS_PENDING, apps,
                               assign_pending)

        # pending application with assed assigned
        # counter to maned_assign_pending
        self.build_application("pending_assed_assigned", 3 * w, 3 * w, constants.APPLICATION_STATUS_PENDING, apps)

        # pending application with no editor group assigned
        # counter to maned_assign_pending
        def noeditorgroup(ap):
            ap.remove_editor_group()

        self.build_application("pending_assed_assigned", 3 * w, 3 * w, constants.APPLICATION_STATUS_PENDING, apps,
                               noeditorgroup)

        # application with no assed, but not pending
        # counter to maned_assign_pending
        self.build_application("no_assed", 3 * w, 3 * w, constants.APPLICATION_STATUS_IN_PROGRESS, apps, assign_pending)

        wait_until_no_es_incomplete_tasks()
        models.Application.refresh()

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

    def build_application(self, id, lmu_diff, cd_diff, status, app_registry, additional_fn=None, update_request=False):
        source = ApplicationFixtureFactory.make_application_source()
        ap = models.Application(**source)
        ap.set_id(id)
        ap.set_last_manual_update(dates.before_now(lmu_diff))
        ap.set_date_applied(dates.before_now(cd_diff))
        ap.set_application_status(status)

        if update_request:
            ap.application_type = constants.APPLICATION_TYPE_UPDATE_REQUEST
        else:
            ap.remove_current_journal()
            ap.remove_related_journal()
            ap.application_type = constants.APPLICATION_TYPE_NEW_APPLICATION

        if additional_fn is not None:
            additional_fn(ap)

        ap.save()
        app_registry.append(ap)