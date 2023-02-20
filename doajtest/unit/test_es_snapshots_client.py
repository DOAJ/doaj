from doajtest.helpers import DoajTestCase
from portality.lib import es_snapshot
from portality.core import es_connection
from doajtest.fixtures.snapshots import SNAPSHOTS_LIST
from copy import deepcopy
from datetime import datetime, timedelta
from freezegun import freeze_time


class TestSnapshotClient(DoajTestCase):

    def setUp(self):
        self.snap_repo = 'mock-repo'
        self.client = es_snapshot.ESSnapshotsClient(es_connection, self.snap_repo)

        self.old_get = self.client.conn.snapshot.get
        self.old_delete = self.client.conn.snapshot.delete
        self.old_create = self.client.conn.snapshot.create
        super(TestSnapshotClient, self).setUp()

    def tearDown(self):
        self.client.conn.snapshot.get = self.old_get
        self.client.conn.snapshot.delete = self.old_delete
        self.client.conn.snapshot.create = self.old_create
        super(TestSnapshotClient, self).tearDown()

    def test_01_list_snapshots(self):
        # Set up a mock response for the snapshots request
        #responses.add(responses.GET, self.snapshot_url + '/_all', json=SNAPSHOTS_LIST, status=200)

        self.client.conn.snapshot.get = lambda *args, **kwargs: SNAPSHOTS_LIST

        # Ensure the client can list the snapshots correctly
        snaps = self.client.list_snapshots()
        assert snaps == [es_snapshot.ESSnapshot(s) for s in SNAPSHOTS_LIST['snapshots']]

    def test_02_snapshots_are_sorted(self):
        # Set up a mock response for the snapshots request, this time in the wrong order
        REVERSED_SNAPS = deepcopy(SNAPSHOTS_LIST)
        REVERSED_SNAPS['snapshots'].reverse()
        #responses.add(responses.GET, self.snapshot_url + '/_all', json=REVERSED_SNAPS, status=200)

        self.client.conn.snapshot.get = lambda *args, **kwargs: REVERSED_SNAPS

        # Ensure the client can list the snapshots in the correct order
        snaps = self.client.list_snapshots()
        assert snaps != [es_snapshot.ESSnapshot(s) for s in REVERSED_SNAPS['snapshots']]
        assert snaps == [es_snapshot.ESSnapshot(s) for s in SNAPSHOTS_LIST['snapshots']]

    def test_03_todays_exists(self):
        # Set up a mock response for the snapshots request
        #responses.add(responses.GET, self.snapshot_url + '/_all', json=SNAPSHOTS_LIST, status=200)
        self.client.conn.snapshot.get = lambda *args, **kwargs: SNAPSHOTS_LIST

        # Set the time to be that which will succeed according to the fixtures
        latest_fixture_date = datetime.utcfromtimestamp(SNAPSHOTS_LIST['snapshots'][-1]['start_time_in_millis'] / 1000)
        with freeze_time(latest_fixture_date):
            # Ensure the client correctly identifies the last snapshot exists per the date set
            self.client.check_today_snapshot()

        # And a day later it raises an exception, because that snapshot is missing
        with self.assertRaises(es_snapshot.TodaySnapshotMissingException):
            with freeze_time(latest_fixture_date + timedelta(days=1)):
                self.client.check_today_snapshot()

        # invalidate the snapshot list so it looks up again
        self.client.snapshots = []

        # Make the failed snapshot our latest
        LATEST_FAILED_SNAPS = deepcopy(SNAPSHOTS_LIST)
        LATEST_FAILED_SNAPS['snapshots'].pop()
        self.client.conn.snapshot.get = lambda *args, **kwargs: LATEST_FAILED_SNAPS

        # Using the fixture with the failed snapshot, check we get an exception if that's the latest in the response
        failed_fixture_date = datetime.utcfromtimestamp(LATEST_FAILED_SNAPS['snapshots'][-1]['start_time_in_millis'] / 1000)
        with self.assertRaises(es_snapshot.FailedSnapshotException):
            with freeze_time(failed_fixture_date):
                self.client.check_today_snapshot()

    def test_04_prune_snapshots(self):
        # Mock response for listing the snapshots
        self.client.conn.snapshot.get = lambda *args, **kwargs: SNAPSHOTS_LIST
        # A mock responses for deleting the snapshots
        self.client.conn.snapshot.delete = lambda *args, **kwargs: {'acknowledged': True}

        # Set the time to the day of the latest backup, and request a prune
        latest_fixture_date = datetime.utcfromtimestamp(SNAPSHOTS_LIST['snapshots'][-1]['start_time_in_millis'] / 1000)
        with freeze_time(latest_fixture_date):
            # Ensure the client correctly deletes snapshots up to our specified threshold
            self.client.prune_snapshots(ttl_days=4)
            assert self.client.snapshots == []                # This just checks we reached the end of the deletion code

        # We can't really test anything more here - we don't have a remote system that will actually respond to deletes,
        # so if I mock the next list_snapshots call I'd just be testing how good the fixtures are.

    def test_05_request_snapshot(self):
        # Mock response for initiating a snapshot
        right_now = datetime.utcnow()
        snaptimestamp = datetime.strftime(right_now, "%Y-%m-%d_%H%Mz")

        # capture the snapshot name at the ES level to show the client is adding our timestamp
        self.client.conn.snapshot.create = lambda *args, **kwargs: {'accepted': True, 'snapshot_name': kwargs['snapshot']}

        # Request a new backup, check it has the right timestamp
        with freeze_time(right_now):
            resp, status = self.client.request_snapshot()
            assert resp['snapshot_name'] == snaptimestamp
