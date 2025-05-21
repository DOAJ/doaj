"""
Identify and amend status of update requests created by CSV ingest to 'accepted'
"""


def amend_status(ur_source: dict):
    ur_source['admin']['application_status'] = 'accepted'
    return ur_source

