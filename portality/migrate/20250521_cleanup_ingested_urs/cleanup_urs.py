"""
Identify and amend status of update requests created by CSV ingest to 'accepted'
"""

from portality import constants


def amend_status(ur_source: dict):
    ur_source['admin']['application_status'] = constants.APPLICATION_STATUS_ACCEPTED
    ur_source['index']['application_type'] = 'finished application/update'
    return ur_source
