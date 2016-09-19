from copy import deepcopy
from datetime import datetime


class ProvenanceFixtureFactory(object):
    @staticmethod
    def make_provenance_source():
        return deepcopy(PROVENANCE)

PROVENANCE = {
    "id" : "1234567890",
    "created_date" : "2001-01-01T00:00:00Z",
    "user": "test",
    "editor_group": ["eg1", "eg2"],
    "type" : "suggestion",
    "subtype" : "reapplication",
    "action" : "edit",
    "resource_id" : "987654321"
}