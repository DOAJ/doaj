import datetime
import time
from typing import Iterable

from doajtest import helpers
from doajtest.helpers import DoajTestCase
from portality.dao import DomainObject
from portality.lib import es_queries
from portality.models import Notification, BackgroundJob
from portality.tasks import old_data_cleanup


def _save_all(objs: Iterable[DomainObject]):
    objs = list(objs)
    for o in objs[:-1]:
        o.save(blocking=False)
    objs[-1].save(blocking=True)
    time.sleep(1)


def _create_obj(domain_class, _days):
    created_date = datetime.datetime.now() - datetime.timedelta(days=_days)
    obj = domain_class(
        created_date=created_date.strftime(es_queries.ES_DATETIME_FMT)
    )
    return obj


class TestOldDataCleanup(DoajTestCase):

    def test_clean_all_old_data__normal(self):
        # prepare data
        days_for_test = [0, 1, 2, 2, 5, 5, 10]
        noti_list = (_create_obj(Notification, d) for d in days_for_test)
        bgjob_list = (_create_obj(BackgroundJob, d) for d in days_for_test)
        _save_all(noti_list)
        _save_all(bgjob_list)
        self.assertEqual(Notification.hit_count(es_queries.query_all()),
                         len(days_for_test))
        self.assertEqual(BackgroundJob.hit_count(es_queries.query_all()),
                         len(days_for_test))

        org_config = helpers.patch_config(self.app_test, {
            "TASK_DATA_RETENTION_DAYS": {
                "notification": 4,
                "background_job": 7,
            }
        })

        # run target
        old_data_cleanup.clean_all_old_data()

        # assert result
        time.sleep(3)
        self.assertEqual(Notification.hit_count(es_queries.query_all()), 4)
        self.assertEqual(BackgroundJob.hit_count(es_queries.query_all()), 6)

        helpers.patch_config(self.app_test, org_config)

    def test_clean_all_old_data__no_obj_deleted(self):
        # prepare data
        BackgroundJob.delete_by_query(es_queries.query_all())
        days_for_test = [0, 1, 2, 2, 5, 5, 10]
        noti_list = (_create_obj(Notification, d) for d in days_for_test)
        _save_all(noti_list)
        org_size = Notification.hit_count(es_queries.query_all())
        self.assertEqual(org_size, len(days_for_test))
        self.assertEqual(BackgroundJob.hit_count(es_queries.query_all()), 0)

        org_config = helpers.patch_config(self.app_test, {
            "TASK_DATA_RETENTION_DAYS": {
                "notification": 1000,
                "background_job": 7,
            }
        })

        # run target
        old_data_cleanup.clean_all_old_data()

        # assert result
        time.sleep(3)
        self.assertEqual(Notification.hit_count(es_queries.query_all()), org_size)
        self.assertEqual(BackgroundJob.hit_count(es_queries.query_all()), 0)

        helpers.patch_config(self.app_test, org_config)
