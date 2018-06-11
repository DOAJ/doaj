from datetime import datetime, timedelta
import requests
from portality.core import app


class BadSnapshotMetaException(Exception):
    pass


class TodaySnapshotMissingException(Exception):
    pass


class FailedSnapshotException(Exception):
    pass


class SnapshotDeleteException(Exception):
    pass


class ESSnapshot(object):
    def __init__(self, snapshot_json):
        self.data = snapshot_json
        self.name = snapshot_json['snapshot']
        self.state = snapshot_json['state']
        self.datetime = datetime.utcfromtimestamp(snapshot_json['start_time_in_millis'] / 1000)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def delete(self):
        snapshots_url = app.config.get('ELASTIC_SEARCH_HOST', 'http://localhost:9200') + '/_snapshot/' + app.config.get('ELASTIC_SEARCH_SNAPSHOT_REPOSITORY', 'doaj_s3')
        resp = requests.delete(snapshots_url + '/' + self.name)
        return resp.status_code == 200


class ESSnapshotsClient(object):

    def __init__(self):
        self.snapshots = []

    def list_snapshots(self):
        # If we don't have the snapshots, ask ES for them
        if not self.snapshots:
            snapshots_url = app.config.get('ELASTIC_SEARCH_HOST', 'http://localhost:9200') + '/_snapshot/' + app.config.get('ELASTIC_SEARCH_SNAPSHOT_REPOSITORY', 'doaj_s3')
            resp = requests.get(snapshots_url + '/_all', timeout=600)

            if 'snapshots' in resp.json():
                try:
                    snap_objs = [ESSnapshot(s) for s in resp.json()['snapshots']]
                except Exception as e:
                    raise BadSnapshotMetaException("Error creating snapshot object: " + e.message + ";")
                self.snapshots = sorted(snap_objs, key=lambda x: x.datetime)

        return self.snapshots

    def check_today_snapshot(self):
        snapshots = self.list_snapshots()
        if snapshots[-1].datetime.date() != datetime.utcnow().date():
            raise TodaySnapshotMissingException('Snapshot appears to be missing for {}'.format(datetime.utcnow().date()))
        elif snapshots[-1].state != 'SUCCESS':
            raise FailedSnapshotException('Snapshot for {} has failed'.format(datetime.utcnow().date()))

    def prune_snapshots(self, ttl_days, delete_callback=None):
        snapshots = self.list_snapshots()
        results = []
        for snapshot in snapshots:
            if snapshot.datetime < datetime.utcnow() - timedelta(days=ttl_days):
                results.append(snapshot.delete())
                if delete_callback:
                    delete_callback(snapshot.name)

        if not all(results):
            raise SnapshotDeleteException('Not all snapshots were deleted successfully.')
