import uuid
from copy import deepcopy
from datetime import datetime
from random import randint

from portality import constants
from portality.lib import dates
from portality.models import Provenance


class ProvenanceFixtureFactory(object):
    @classmethod
    def make_provenance_source(cls):
        return deepcopy(PROVENANCE)

    @classmethod
    def make_action_spread(cls, desired_output, action, period):
        desired_output = deepcopy(desired_output)
        header = desired_output[0]
        del desired_output[0]
        del header[0]
        ranges = []
        for h in header:
            start = None
            end = None
            if period == "month":
                startts = dates.parse(h, "%Y-%m")
                year, month = divmod(startts.month+1, 12)
                if month == 0:
                    month = 12
                    year = year - 1
                endts = datetime(startts.year + year, month, 1)
                start = dates.format(startts)
                end = dates.format(endts)
            elif period == "year":
                startts = dates.parse(h, "%Y")
                endts = datetime(startts.year + 1, 1, 1)
                start = dates.format(startts)
                end = dates.format(endts)

            ranges.append((start, end))

        provs = []
        for row in desired_output:
            user = row[0]
            del row[0]
            for i in range(len(row)):
                count = row[i]
                start, end = ranges[i]
                for j in range(count):
                    p = Provenance()
                    p.set_created(dates.random_date(start, end))
                    p.user = user
                    p.type = "suggestion"
                    p.action = action
                    p.resource_id = uuid.uuid4().hex
                    provs.append(p)

        return provs

    @classmethod
    def make_status_spread(cls, desired_output, period, role_map):
        desired_output = deepcopy(desired_output)
        header = desired_output[0]
        del desired_output[0]
        del header[0]
        ranges = []
        for h in header:
            start = None
            end = None
            if period == "month":
                startts = dates.parse(h, "%Y-%m")
                year, month = divmod(startts.month+1, 12)
                if month == 0:
                    month = 12
                    year = year - 1
                endts = datetime(startts.year + year, month, 1)
                start = dates.format(startts)
                end = dates.format(endts)
            elif period == "year":
                startts = dates.parse(h, "%Y")
                endts = datetime(startts.year + 1, 1, 1)
                start = dates.format(startts)
                end = dates.format(endts)

            ranges.append((start, end))

        provs = []
        for row in desired_output:
            user = row[0]
            del row[0]
            role = role_map[user]
            for i in range(len(row)):
                count = row[i]
                start, end = ranges[i]
                status = None
                if role == "associate_editor":
                    status = constants.APPLICATION_STATUS_COMPLETED
                elif role == "editor":
                    status = constants.APPLICATION_STATUS_READY
                elif role == "admin":
                    status = ADMIN_STATUSES[randint(0, len(ADMIN_STATUSES) - 1)]
                for j in range(count):
                    p = Provenance()
                    p.set_created(dates.random_date(start, end))
                    p.user = user
                    p.roles = [role]
                    p.type = "suggestion"
                    p.action = "status:" + status
                    p.resource_id = uuid.uuid4().hex
                    provs.append(p)

        return provs


PROVENANCE = {
    "id" : "1234567890",
    "created_date" : "2001-01-01T00:00:00Z",
    "last_updated" : "2001-01-01T00:00:00Z",
    "user": "test",
    "roles" : ["associate_editor", "editor", "admin"],
    "editor_group": ["eg1", "eg2"],
    "type" : "suggestion",
    "subtype" : "update_request",
    "action" : "edit",
    "resource_id" : "987654321"
}

ADMIN_STATUSES = [constants.APPLICATION_STATUS_ACCEPTED, constants.APPLICATION_STATUS_REJECTED]