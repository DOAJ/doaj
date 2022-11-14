import itertools
from collections import Counter
from datetime import datetime

from combinatrix.testintegration import load_parameter_sets
from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import ApplicationFixtureFactory, AccountFixtureFactory, EditorGroupFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import constants
from portality import models
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.constants import TODO_ASSOCIATE_PROGRESS_STALLED, TODO_ASSOCIATE_START_PENDING, \
    TODO_ASSOCIATE_FOLLOW_UP_OLD, TODO_ASSOCIATE_ALL_APPLICATIONS
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

    @classmethod
    def setUpClass(cls) -> None:
        super(TestBLLTopTodo, cls).setUpClass()
        w = 7*24*60*60
        apps = [
            # an application stalled for more than 8 weeks
            cls.build_application("maned_stalled__maned_old", 10*w, 10*w, constants.APPLICATION_STATUS_IN_PROGRESS),

            # an application that is not stalled
            cls.build_application("unstalled", 2*w, 2*w, constants.APPLICATION_STATUS_IN_PROGRESS),

            # an application that is old but rejected
            cls.build_application("rejected", 11 * w, 11 * w, constants.APPLICATION_STATUS_REJECTED),

            # an application that was created over 10 weeks ago (but updated recently)
            cls.build_application("maned_old", 2 * w, 11 * w, constants.APPLICATION_STATUS_IN_PROGRESS),

            # an application that was created recently
            cls.build_application("not_old", 2 * w, 2 * w, constants.APPLICATION_STATUS_IN_PROGRESS),

            # an application that was created over 10 weeks ago and is accepted
            cls.build_application("accepted", 12 * w, 12 * w, constants.APPLICATION_STATUS_ACCEPTED),

            # special editor, so it will not match TODO_ASSOCIATE_START_PENDING
            cls.build_application("special_editor", 2 * w, 2 * w, constants.APPLICATION_STATUS_IN_PROGRESS,
                                  editor='special_editorXXX'),

            # status is pending
            cls.build_application("pending_12", 12 * w, 12 * w, constants.APPLICATION_STATUS_PENDING),
        ]

        models.Application.blockall([(ap.id, ap.last_updated) for ap in apps])

    def setUp(self):
        super(TestBLLTopTodo, self).setUp()
        self.svc = DOAJ.todoService()

    def tearDown(self):
        pass   # avoid reset db records

    @classmethod
    def tearDownClass(cls) -> None:
        cls.reset_db_record()
        super().tearDownClass()

    @parameterized.expand(load_cases)
    def test_top_todo(self, name, kwargs):

        account_arg = kwargs.get("account")
        size_arg = kwargs.get("size")
        raises_arg = kwargs.get("raises")

        categories = [
            "todo_maned_stalled",
            "todo_maned_follow_up_old"
        ]

        category_args = {
            cat : (
                int(kwargs.get(cat)),
                int(kwargs.get(cat + "_order") if kwargs.get(cat + "_order") != "" else -1)
            ) for cat in categories
        }

        ###############################################
        ## set up

        account = self.make_account_by_type(account_arg)

        size = int(size_arg)

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
            actions = Counter(itertools.chain.from_iterable(todo["action_id"] for todo in todos))
            for k, v in category_args.items():
                assert actions.get(k, 0) == v

            # todo_maned_stalled_expected = int(todo_maned_stalled_arg)
            # assert actions.get(constants.TODO_MANED_STALLED, 0) == todo_maned_stalled_expected
            #
            # todo_maned_follow_up_old_expected = int(todo_maned_follow_up_old_arg)
            # assert actions.get(constants.TODO_MANED_FOLLOW_UP_OLD, 0) == todo_maned_follow_up_old_expected


    def test_todo__assed_normal(self):
        account = self.make_account_by_type('assed')
        size = 100


        todos = self.svc.top_todo(account, size)

        app_action_dict = {
            t['object_id']: set(t['action_id']) for t in todos
        }

        # breakpoint()
        excepted_app_action_dict = {
            "maned_stalled__maned_old": {TODO_ASSOCIATE_PROGRESS_STALLED,
                                         TODO_ASSOCIATE_FOLLOW_UP_OLD, TODO_ASSOCIATE_ALL_APPLICATIONS},
            "unstalled": {TODO_ASSOCIATE_ALL_APPLICATIONS},
            "maned_old": {TODO_ASSOCIATE_FOLLOW_UP_OLD, TODO_ASSOCIATE_ALL_APPLICATIONS},
            "not_old": {TODO_ASSOCIATE_ALL_APPLICATIONS},
            "pending_12": {TODO_ASSOCIATE_START_PENDING, TODO_ASSOCIATE_PROGRESS_STALLED, TODO_ASSOCIATE_FOLLOW_UP_OLD, TODO_ASSOCIATE_ALL_APPLICATIONS},
        }

        self.assertEqual(app_action_dict, excepted_app_action_dict)


    @staticmethod
    def make_account_by_type(acc_type):
        asource = None
        if acc_type == "admin":
            asource = AccountFixtureFactory.make_managing_editor_source()
        elif acc_type == "editor":
            asource = AccountFixtureFactory.make_editor_source()
        elif acc_type == "assed":
            asource = AccountFixtureFactory.make_assed1_source()
        elif acc_type == "no_role":
            asource = AccountFixtureFactory.make_publisher_source()

        if asource is None:
            return None
        else:
            return models.Account(**asource)


    @staticmethod
    def build_application(id, lmu_diff, cd_diff, status, editor=None):
        source = ApplicationFixtureFactory.make_application_source()
        ap = models.Application(**source)
        ap.set_id(id)
        ap.set_last_manual_update(dates.before(datetime.utcnow(), lmu_diff))
        ap.set_created(dates.before(datetime.utcnow(), cd_diff))
        ap.set_application_status(status)

        if editor is not None:
            ap.set_editor(editor)

        ap.save()
        return ap