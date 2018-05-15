from doajtest.helpers import DoajTestCase
from portality.core import app
from portality.lib import es_snapshots
from doajtest.fixtures.snapshots import SNAPSHOTS_LIST
import responses
import freezegun


class TestSnapshotClient(DoajTestCase):

    def setUp(self):
        super(TestSnapshotClient, self).setUp()

    def tearDown(self):
        super(TestSnapshotClient, self).tearDown()

    @responses.activate
    def test_01_list_snapshots(self):
        snapshot_url = app.config.get('ELASTIC_SEARCH_HOST', 'http://localhost:9200') + '/_snapshot/' + app.config.get('ELASTIC_SEARCH_SNAPSHOT_REPOSITORY', 'doaj_s3')
        responses.add(responses.GET, snapshot_url, json=SNAPSHOTS_LIST, status=200)
        client = es_snapshots.ESSnapshotsClient()
        s = client.list_snapshots()
        assert s == SNAPSHOTS_LIST

    def test_02_snapshots_are_sorted(self):
        pass

    def test_03_todays_exists(self):
        pass

    def test_04_prune_snapshots(self):
        pass
