""" Library for managing ElasticSearch snapshots - ported from esprit and modified to use the Elasticsearch bindings
"""

from datetime import datetime, timedelta
from elasticsearch import Elasticsearch, ElasticsearchException


class BadSnapshotMetaException(Exception):
    pass


class TodaySnapshotMissingException(Exception):
    pass


class FailedSnapshotException(Exception):
    pass


class SnapshotDeleteException(Exception):
    pass


class ESSnapshot(object):
    """ Representation of an ES Snapshot """
    def __init__(self, snapshot_json: dict):
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


class ESSnapshotsClient(object):
    """ Client for performing operations on the ES Snapshots """

    def __init__(self, connection: Elasticsearch, snapshot_repository: str):
        """
        Initialise the Client with a connection to ES
        :param connection: Elasticsearch connection object (elasticsearch.Elasticsearch)
        :param snapshot_repository: the S3 repo identifier defined in the snapshot settings
        """
        self.conn = connection
        self.repo = snapshot_repository
        self.snapshots = []

    def request_snapshot(self, snapshot_name: str = None):
        """
        Request the elasticsearch snapshot plugin to create a snapshot
        :param snapshot_name a string to name the snapshot. Defaults to UTC timestamp e.g. 2019-01-26_1602z
        :return: Tuple of the result as text & True / False for success / fail
        """
        name = snapshot_name if snapshot_name is not None else datetime.strftime(datetime.utcnow(), "%Y-%m-%d_%H%Mz")
        try:
            resp = self.conn.snapshot.create(repository=self.repo, snapshot=name, master_timeout='600s')
        except ElasticsearchException as e:
            return str(e), False
        return resp, resp['accepted']

    def delete_snapshot(self, snapshot: ESSnapshot):
        """
        Delete a snapshot from S3 storage
        :param snapshot: An ESSnapshot object
        :return: Tuple of the result as text & True / False for success / fail
        """
        try:
            resp = self.conn.snapshot.delete(self.repo, snapshot.name, master_timeout='600s')
        except ElasticsearchException as e:
            return str(e), False
        return resp, resp['acknowledged']

    def list_snapshots(self):
        """
        Return a list of all snapshots in the S3 repository
        :return: list of ESSnapshot objects, oldest to newest
        """

        # If the client doesn't have the snapshots, ask ES for them
        if not self.snapshots:
            resp = self.conn.snapshot.get(self.repo, '_all', master_timeout='600s')

            if 'snapshots' in resp:
                try:
                    snap_objs = [ESSnapshot(s) for s in resp['snapshots']]
                except Exception as e:
                    raise BadSnapshotMetaException("Error creating snapshot object: ") from e

                # Sort the snapshots old to new
                self.snapshots = sorted(snap_objs, key=lambda x: x.datetime)

        return self.snapshots

    def check_today_snapshot(self):
        """ Check we have a successful snapshot for today """
        snapshots = self.list_snapshots()
        if snapshots[-1].datetime.date() != datetime.utcnow().date():
            raise TodaySnapshotMissingException('Snapshot appears to be missing for {}'.format(datetime.utcnow().date()))
        elif snapshots[-1].state != 'SUCCESS':
            raise FailedSnapshotException('Snapshot for {} has failed'.format(datetime.utcnow().date()))

    def prune_snapshots(self, ttl_days: int, delete_callback=None):
        """
        Delete all snapshots outwith our TTL (Time To Live) period based on today's date.
        :param ttl_days: integer number of days a snapshot should be retained
        :param delete_callback: callback to run after the delete has occurred, should accept an ESSnapshot and
        boolean success / fail: f(snapshot, succeeded)
        :return: nothing, but throws SnapshotDeleteException if not all were successful.
        """
        snapshots = self.list_snapshots()

        # Keep a list of boolean success / failures of our deletes
        results = []
        for snapshot in snapshots:
            if snapshot.datetime < datetime.utcnow() - timedelta(days=ttl_days):
                _, status = self.delete_snapshot(snapshot)

                # Log a success if we get a 2xx response
                results.append(status)

                # Run the callback if there is one
                if delete_callback:
                    delete_callback(snapshot, status, results[-1])

        # Our snapshots list is outdated, invalidate it
        self.snapshots = []

        print("snapshots prune results: {}".format(results))
        if not all(results):
            raise SnapshotDeleteException('Not all snapshots were deleted successfully.')
