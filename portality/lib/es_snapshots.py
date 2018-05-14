from datetime import datetime, timedelta


class BadSnapshotNameException(Exception):
    pass


class TodaySnapshotMissingException(Exception):
    pass


class ESSnapshot(object):
    def __init__(self, snapshot_json):
        self.data = snapshot_json
        self.name = snapshot_json['snapshot']
        self.datetime = datetime.utcfromtimestamp(snapshot_json['start_time_in_millis'] / 1000)

    def delete(self):
        pass


class ESSnapshotsClient(object):

    def __init__(self):
        self.snapshots = []

    def list_snapshots(self):
        # if self.snapshots:
        #     return self.snapshots
        # self.snapshots = [ordered ESSnapshot]
        # return self.snapshots
        pass

    def check_today_snapshot(self):
        snapshots = self.list_snapshots()
        if snapshots[-1].datetime.date() != datetime.utcnow().date():
            raise TodaySnapshotMissingException('Snapshot appears to be missing for {}'.format(datetime.utcnow().date()))

    def prune_snapshots(self, ttl_days, delete_callback=None):
        snapshots = self.list_snapshots()
        for snapshot in snapshots:
            if snapshot.datetime < datetime.utcnow() - timedelta(days=ttl_days):
                snapshot.delete()
                if delete_callback:
                    delete_callback(snapshot.name)
