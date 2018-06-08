from doajtest.helpers import DoajTestCase
from portality.core import app
from portality.lib import es_snapshots
from doajtest.fixtures.snapshots import SNAPSHOTS_LIST
from copy import deepcopy
from datetime import datetime, timedelta
from nose.tools import assert_raises
import responses
from freezegun import freeze_time


class TestSnapshotClient(DoajTestCase):

    def setUp(self):
        self.snapshot_url = app.config.get('ELASTIC_SEARCH_HOST', 'http://localhost:9200') + '/_snapshot/' + app.config.get('ELASTIC_SEARCH_SNAPSHOT_REPOSITORY', 'doaj_s3')
        super(TestSnapshotClient, self).setUp()

    def tearDown(self):
        responses.reset()
        super(TestSnapshotClient, self).tearDown()

    @responses.activate
    def test_01_list_snapshots(self):
        # Set up a mock response for the snapshots request
        responses.add(responses.GET, self.snapshot_url, json=SNAPSHOTS_LIST, status=200)

        # Ensure the client can list the snapshots correctly
        client = es_snapshots.ESSnapshotsClient()
        snaps = client.list_snapshots()
        assert snaps == [es_snapshots.ESSnapshot(s) for s in SNAPSHOTS_LIST['snapshots']]

    @responses.activate
    def test_02_snapshots_are_sorted(self):
        # Set up a mock response for the snapshots request, this time in the wrong order
        REVERSED_SNAPS = deepcopy(SNAPSHOTS_LIST)
        REVERSED_SNAPS['snapshots'].reverse()
        responses.add(responses.GET, self.snapshot_url, json=REVERSED_SNAPS, status=200)

        # Ensure the client can list the snapshots in the correct order
        client = es_snapshots.ESSnapshotsClient()
        snaps = client.list_snapshots()
        assert snaps != [es_snapshots.ESSnapshot(s) for s in REVERSED_SNAPS['snapshots']]
        assert snaps == [es_snapshots.ESSnapshot(s) for s in SNAPSHOTS_LIST['snapshots']]

    @responses.activate
    def test_03_todays_exists(self):
        # Set up a mock response for the snapshots request
        responses.add(responses.GET, self.snapshot_url, json=SNAPSHOTS_LIST, status=200)

        # Set the time to be that which will succeed according to the fixtures
        latest_fixture_date = datetime.utcfromtimestamp(SNAPSHOTS_LIST['snapshots'][-1]['start_time_in_millis'] / 1000)
        with freeze_time(latest_fixture_date):
            # Ensure the client correctly identifies the last snapshot exists per the date set
            client = es_snapshots.ESSnapshotsClient()
            client.check_today_snapshot()

        # And a day later it raises an exception, because that snapshot is missing
        with assert_raises(es_snapshots.TodaySnapshotMissingException):
            with freeze_time(latest_fixture_date + timedelta(days=1)):
                client = es_snapshots.ESSnapshotsClient()
                client.check_today_snapshot()

        # Make the failed snapshot our latest
        LATEST_FAILED_SNAPS = deepcopy(SNAPSHOTS_LIST)
        LATEST_FAILED_SNAPS['snapshots'].pop()
        responses.reset()
        responses.add(responses.GET, self.snapshot_url, json=LATEST_FAILED_SNAPS, status=200)

        # Using the fixture with the failed snapshot, check we get an exception if that's the latest in the response
        failed_fixture_date = datetime.utcfromtimestamp(LATEST_FAILED_SNAPS['snapshots'][-1]['start_time_in_millis'] / 1000)
        with assert_raises(es_snapshots.FailedSnapshotException):
            with freeze_time(failed_fixture_date):
                client = es_snapshots.ESSnapshotsClient()
                client.check_today_snapshot()

    def test_04_prune_snapshots(self):
        pass
