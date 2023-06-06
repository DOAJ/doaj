from doajtest.helpers import DoajTestCase
from esprit import raw, snapshot
from doajtest.fixtures.snapshots import SNAPSHOTS_LIST
from copy import deepcopy
from datetime import datetime, timedelta
import responses
from freezegun import freeze_time

from portality.lib import dates


class TestSnapshotClient(DoajTestCase):

    def setUp(self):
        self.snap_repo = 'mock-repo'
        self.snapshot_url = 'http://localhost:9200' + '/_snapshot/' + self.snap_repo
        self.es_conn = raw.Connection('http://localhost:9200', index='_snapshot')
        super(TestSnapshotClient, self).setUp()

    def tearDown(self):
        responses.reset()
        super(TestSnapshotClient, self).tearDown()

    @responses.activate
    def test_01_list_snapshots(self):
        # Set up a mock response for the snapshots request
        responses.add(responses.GET, self.snapshot_url + '/_all', json=SNAPSHOTS_LIST, status=200)

        # Ensure the client can list the snapshots correctly
        client = snapshot.ESSnapshotsClient(self.es_conn, self.snap_repo)
        snaps = client.list_snapshots()
        assert snaps == [snapshot.ESSnapshot(s) for s in SNAPSHOTS_LIST['snapshots']]

    @responses.activate
    def test_02_snapshots_are_sorted(self):
        # Set up a mock response for the snapshots request, this time in the wrong order
        REVERSED_SNAPS = deepcopy(SNAPSHOTS_LIST)
        REVERSED_SNAPS['snapshots'].reverse()
        responses.add(responses.GET, self.snapshot_url + '/_all', json=REVERSED_SNAPS, status=200)

        # Ensure the client can list the snapshots in the correct order
        client = snapshot.ESSnapshotsClient(self.es_conn, self.snap_repo)
        snaps = client.list_snapshots()
        assert snaps != [snapshot.ESSnapshot(s) for s in REVERSED_SNAPS['snapshots']]
        assert snaps == [snapshot.ESSnapshot(s) for s in SNAPSHOTS_LIST['snapshots']]

    @responses.activate
    def test_03_todays_exists(self):
        # Set up a mock response for the snapshots request
        responses.add(responses.GET, self.snapshot_url + '/_all', json=SNAPSHOTS_LIST, status=200)

        # Set the time to be that which will succeed according to the fixtures
        latest_fixture_date = datetime.utcfromtimestamp(SNAPSHOTS_LIST['snapshots'][-1]['start_time_in_millis'] / 1000)
        with freeze_time(latest_fixture_date):
            # Ensure the client correctly identifies the last snapshot exists per the date set
            client = snapshot.ESSnapshotsClient(self.es_conn, self.snap_repo)
            client.check_today_snapshot()

        # And a day later it raises an exception, because that snapshot is missing
        with self.assertRaises(snapshot.TodaySnapshotMissingException):
            with freeze_time(latest_fixture_date + timedelta(days=1)):
                client = snapshot.ESSnapshotsClient(self.es_conn, self.snap_repo)
                client.check_today_snapshot()

        # Make the failed snapshot our latest
        LATEST_FAILED_SNAPS = deepcopy(SNAPSHOTS_LIST)
        LATEST_FAILED_SNAPS['snapshots'].pop()
        responses.reset()
        responses.add(responses.GET, self.snapshot_url + '/_all', json=LATEST_FAILED_SNAPS, status=200)

        # Using the fixture with the failed snapshot, check we get an exception if that's the latest in the response
        failed_fixture_date = datetime.utcfromtimestamp(LATEST_FAILED_SNAPS['snapshots'][-1]['start_time_in_millis'] / 1000)
        with self.assertRaises(snapshot.FailedSnapshotException):
            with freeze_time(failed_fixture_date):
                client = snapshot.ESSnapshotsClient(self.es_conn, self.snap_repo)
                client.check_today_snapshot()

    @responses.activate
    def test_04_prune_snapshots(self):
        # Mock response for listing the snapshots
        responses.add(responses.GET, self.snapshot_url + '/_all', json=SNAPSHOTS_LIST, status=200)

        # Set up a mock responses for deleting the snapshots
        for s in SNAPSHOTS_LIST['snapshots']:
            responses.add(responses.DELETE, self.snapshot_url + '/' + s['snapshot'], json={"acknowledged": True}, status=200)

        # Set the time to the day of the latest backup, and request a prune
        latest_fixture_date = datetime.utcfromtimestamp(SNAPSHOTS_LIST['snapshots'][-1]['start_time_in_millis'] / 1000)
        with freeze_time(latest_fixture_date):
            # Ensure the client correctly deletes snapshots up to our specified threshold
            client = snapshot.ESSnapshotsClient(self.es_conn, self.snap_repo)
            client.prune_snapshots(ttl_days=4)
            assert client.snapshots == []                     # This just checks we reached the end of the deletion code

        # We can't really test anything more here - we don't have a remote system that will actually respond to deletes,
        # so if I mock the next list_snapshots call I'd just be testing how good the fixtures are.

    @responses.activate
    def test_05_request_snapshot(self):
        # Mock response for initiating a snapshot
        right_now = dates.now()
        slashtimestamp = datetime.strftime(right_now, "/%Y-%m-%d_%H%Mz")
        responses.add(responses.PUT, self.snapshot_url + slashtimestamp, json={"acknowledged": True}, status=200)

        # Request a new backup, check it has the right timestamp
        with freeze_time(right_now):
            # Ensure the client correctly deletes snapshots up to our specified threshold
            client = snapshot.ESSnapshotsClient(self.es_conn, self.snap_repo)
            resp = client.request_snapshot()
            assert resp.status_code == 200
            assert resp.url == self.snapshot_url + slashtimestamp
