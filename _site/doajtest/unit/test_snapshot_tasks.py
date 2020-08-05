from doajtest.helpers import DoajTestCase
from portality.core import app
from portality.tasks import check_latest_es_backup, prune_es_backups
from portality.background import BackgroundApi
import responses


class TestSnapshotTasks(DoajTestCase):

    def setUp(self):
        super(TestSnapshotTasks, self).setUp()

    def tearDown(self):
        super(TestSnapshotTasks, self).tearDown()

    def test_01_es_snapshots_client(self):
        pass

    def test_0x_check_latest_es_backup(self):
        user = app.config.get("SYSTEM_USERNAME")
        job = check_latest_es_backup.CheckLatestESBackupBackgroundTask.prepare(user)
        task = check_latest_es_backup.CheckLatestESBackupBackgroundTask(job)
        BackgroundApi.execute(task)

    def test_0y_prune_es_backups(self):
        pass
