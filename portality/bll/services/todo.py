from portality.lib.argvalidate import argvalidate
from portality import models
from portality.bll import exceptions
from portality import constants
from portality.lib import dates
from datetime import datetime


class TodoService(object):
    """
    ~~Todo:Service->DOAJ:Service~~
    ~~-> ApplicationStatuses:Config~~
    """

    def group_stats(self, group_id):
        # ~~-> EditorGroup:Model~~
        eg = models.EditorGroup.pull(group_id)
        stats = {"editor_group": eg.data}

        # ~~-> Account:Model ~~
        stats["editors"] = {}
        editors = [eg.editor] + eg.associates
        for editor in editors:
            acc = models.Account.pull(editor)
            stats["editors"][editor] = {
                "email": None if acc is None else acc.email
            }

        q = GroupStatsQuery(eg.name)
        resp = models.Application.query(q=q.query())

        stats["total"] = {"applications": 0, "update_requests": 0}

        stats["by_editor"] = {}
        for bucket in resp.get("aggregations", {}).get("editor", {}).get("buckets", []):
            stats["by_editor"][bucket["key"]] = {"applications": 0, "update_requests": 0}

            for b in bucket.get("application_type", {}).get("buckets", []):
                if b["key"] == constants.APPLICATION_TYPE_NEW_APPLICATION:
                    stats["by_editor"][bucket["key"]]["applications"] = b["doc_count"]
                    stats["total"]["applications"] += b["doc_count"]
                elif b["key"] == constants.APPLICATION_TYPE_UPDATE_REQUEST:
                    stats["by_editor"][bucket["key"]]["update_requests"] = b["doc_count"]
                    stats["total"]["update_requests"] += b["doc_count"]

        unassigned_buckets = resp.get("aggregations", {}).get("unassigned", {}).get("application_type", {}).get(
            "buckets", [])
        stats["unassigned"] = {"applications": 0, "update_requests": 0}
        for ub in unassigned_buckets:
            if ub["key"] == constants.APPLICATION_TYPE_NEW_APPLICATION:
                stats["unassigned"]["applications"] = ub["doc_count"]
                stats["total"]["applications"] += ub["doc_count"]
            elif ub["key"] == constants.APPLICATION_TYPE_UPDATE_REQUEST:
                stats["unassigned"]["update_requests"] = ub["doc_count"]
                stats["total"]["update_requests"] += ub["doc_count"]

        stats["by_status"] = {}
        for bucket in resp.get("aggregations", {}).get("status", {}).get("buckets", []):
            stats["by_status"][bucket["key"]] = {"applications": 0, "update_requests": 0}
            for b in bucket.get("application_type", {}).get("buckets", []):
                if b["key"] == constants.APPLICATION_TYPE_NEW_APPLICATION:
                    stats["by_status"][bucket["key"]]["applications"] = b["doc_count"]
                elif b["key"] == constants.APPLICATION_TYPE_UPDATE_REQUEST:
                    stats["by_status"][bucket["key"]]["update_requests"] = b["doc_count"]

        stats["historical_numbers"] = self.group_finished_historical_counts(eg)

        return stats

    def group_finished_historical_counts(self, editor_group: models.EditorGroup, year=None):
        """
        Get the count of applications in an editor group where
        Associate Editors set to Completed when they have done their review
        Editors set them to Ready
        in a given year (current by default)
        :param editor_group
        :param year
        :return: historical for editor and associate editor in dict
        """
        year_for_query = dates.now_str(dates.FMT_YEAR) if year is None else year
        editor_status = "status:" + constants.APPLICATION_STATUS_READY
        associate_status = "status:" + constants.APPLICATION_STATUS_COMPLETED

        stats = {"year": year_for_query}

        hs = HistoricalNumbersQuery(editor_group.editor, editor_status, editor_group.id)
        # ~~-> Provenance:Model ~~
        editor_count = models.Provenance.count(query=hs.query())

        # ~~-> Account:Model ~~
        acc = models.Account.pull(editor_group.editor)
        stats["editor"] = {"id": acc.id, "count": editor_count}

        stats["associate_editors"] = []
        for associate in editor_group.associates:
            hs = HistoricalNumbersQuery(associate, associate_status, editor_group.id)
            associate_count = models.Provenance.count(query=hs.query())
            acc = models.Account.pull(associate)
            stats["associate_editors"].append({"id": acc.id, "name": acc.name, "count": associate_count})

        return stats

    def user_finished_historical_counts(self, account, year=None):
        """
        Get the count of overall applications
        Associate Editors set to Completed
        Editors set them to Ready
        in a given year (current by default)
        :param account
        :param year
        :return:
        """
        hs = None

        if account.has_role("editor"):
            hs = HistoricalNumbersQuery(account.id, "status:" + constants.APPLICATION_STATUS_READY, year)
        elif account.has_role("associate_editor"):
            hs = HistoricalNumbersQuery(account.id, "status:" + constants.APPLICATION_STATUS_COMPLETED, year)

        if hs:
            count = models.Provenance.count(query=hs.query())
        else:
            count = None

        return count

    def top_todo(self, account, size=25, new_applications=True, update_requests=True, flagged=True, on_hold=True):
        """
        Returns the top number of todo items for a given user

        :param account:
        :param size:
        :return:
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("top_todo", [
            {"arg": account, "instance": models.Account, "allow_none": False, "arg_name": "account"}
        ], exceptions.ArgumentException)

        queries = []
        if account.has_role("admin"):
            maned_of = models.EditorGroup.groups_by_maned(account.id)
            if new_applications:
                queries.append(TodoRules.maned_follow_up_old(size, maned_of))
                queries.append(TodoRules.maned_stalled(size, maned_of))
                queries.append(TodoRules.maned_ready(size, maned_of))
                queries.append(TodoRules.maned_completed(size, maned_of))
                queries.append(TodoRules.maned_assign_pending(size, maned_of))
            if update_requests:
                queries.append(TodoRules.maned_last_month_update_requests(size, maned_of))
                queries.append(TodoRules.maned_new_update_requests(size, maned_of))
            if on_hold:
                queries.append(TodoRules.maned_on_hold(size, account.id, maned_of))

        if new_applications:  # editor and associate editor roles only deal with new applications
            if account.has_role("editor"):
                groups = [g for g in models.EditorGroup.groups_by_editor(account.id)]
                regular_groups = [g for g in groups if g.maned != account.id]
                maned_groups = [g for g in groups if g.maned == account.id]
                if len(groups) > 0:
                    queries.append(TodoRules.editor_follow_up_old(groups, size))
                    queries.append(TodoRules.editor_stalled(groups, size))
                    queries.append(TodoRules.editor_completed(groups, size))

                # for groups where the user is not the maned for a group, given them the assign
                # pending todos at the regular priority
                if len(regular_groups) > 0:
                    queries.append(TodoRules.editor_assign_pending(regular_groups, size))

                # for groups where the user IS the maned for a group, give them the assign
                # pending todos at a lower priority
                if len(maned_groups) > 0:
                    qi = TodoRules.editor_assign_pending(maned_groups, size)
                    queries.append((constants.TODO_EDITOR_ASSIGN_PENDING_LOW_PRIORITY, qi[1], qi[2], -2))

            if account.has_role(constants.ROLE_ASSOCIATE_EDITOR):
                queries.extend([
                    TodoRules.associate_follow_up_old(account.id, size),
                    TodoRules.associate_stalled(account.id, size),
                    TodoRules.associate_start_pending(account.id, size),
                    TodoRules.associate_all_applications(account.id, size)
                ])

        todos = []
        for aid, q, sort, boost in queries:
            applications = models.Application.object_query(q=q.query())
            for ap in applications:
                todos.append({
                    "date": ap.last_manual_update_timestamp if sort == "last_manual_update" else ap.date_applied_timestamp,
                    "date_type": sort,
                    "action_id": [aid],
                    "title": ap.bibjson().title,
                    "object_id": ap.id,
                    "object": ap,
                    "boost": boost
                })

        todos = self._rationalise_todos(todos, size)

        return todos

    def _rationalise_todos(self, todos, size):
        boost_groups = sorted(list(set([x["boost"] for x in todos])), reverse=True)

        stds = []
        for bg in boost_groups:
            group = list(filter(lambda x: x["boost"] == bg, todos))
            stds += sorted(group, key=lambda x: x['date'])

        id_map = {}
        removals = []
        for i in range(len(stds)):
            todo = stds[i]
            oid = todo["object_id"]
            if oid in id_map:
                removals.append(i)
                stds[id_map[oid]]['action_id'] += todo['action_id']
            else:
                id_map[oid] = i

        removals.reverse()
        for r in removals:
            del stds[r]

        return stds[:size]


class TodoRules(object):

    @classmethod
    def maned_stalled(cls, size, maned_of):
        sort_date = "created_date"
        stalled = TodoQuery(
            musts=[
                TodoQuery.lmu_older_than(8),
                TodoQuery.editor_group(maned_of),
                TodoQuery.is_new_application()
            ],
            must_nots=[
                TodoQuery.status([
                    constants.APPLICATION_STATUS_ACCEPTED,
                    constants.APPLICATION_STATUS_REJECTED,
                    constants.APPLICATION_STATUS_ON_HOLD
                ])
            ],
            sort=sort_date,
            size=size
        )
        return constants.TODO_MANED_STALLED, stalled, sort_date, 0

    @classmethod
    def maned_follow_up_old(cls, size, maned_of):
        sort_date = "created_date"
        follow_up_old = TodoQuery(
            musts=[
                TodoQuery.cd_older_than(10),
                TodoQuery.editor_group(maned_of),
                TodoQuery.is_new_application()
            ],
            must_nots=[
                TodoQuery.status([
                    constants.APPLICATION_STATUS_ACCEPTED,
                    constants.APPLICATION_STATUS_REJECTED,
                    constants.APPLICATION_STATUS_ON_HOLD
                ])
            ],
            sort=sort_date,
            size=size
        )
        return constants.TODO_MANED_FOLLOW_UP_OLD, follow_up_old, sort_date, 0

    @classmethod
    def maned_ready(cls, size, maned_of):
        sort_date = "created_date"
        ready = TodoQuery(
            musts=[
                TodoQuery.status([constants.APPLICATION_STATUS_READY]),
                TodoQuery.editor_group(maned_of),
                TodoQuery.is_new_application()
            ],
            sort=sort_date,
            size=size
        )
        return constants.TODO_MANED_READY, ready, sort_date, 1

    @classmethod
    def maned_completed(cls, size, maned_of):
        print("maned_completed")
        sort_date = "created_date"
        completed = TodoQuery(
            musts=[
                TodoQuery.status([constants.APPLICATION_STATUS_COMPLETED]),
                TodoQuery.lmu_older_than(2),
                TodoQuery.editor_group(maned_of),
                TodoQuery.is_new_application()
            ],
            sort=sort_date,
            size=size
        )
        return constants.TODO_MANED_COMPLETED, completed, sort_date, 0

    @classmethod
    def maned_assign_pending(cls, size, maned_of):
        sort_date = "created_date"

        assign_pending = TodoQuery(
            musts=[
                TodoQuery.exists("admin.editor_group"),
                TodoQuery.lmu_older_than(2),
                TodoQuery.status([constants.APPLICATION_STATUS_PENDING]),
                TodoQuery.editor_group(maned_of),
                TodoQuery.is_new_application()
            ],
            must_nots=[
                TodoQuery.exists("admin.editor")
            ],
            sort=sort_date,
            size=size
        )
        return constants.TODO_MANED_ASSIGN_PENDING, assign_pending, sort_date, 0

    @classmethod
    def maned_last_month_update_requests(cls, size, maned_of):
        som = dates.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        now = dates.now()
        since_som = int((now - som).total_seconds())

        sort_date = "created_date"
        assign_pending = TodoQuery(
            musts=[
                TodoQuery.exists("admin.editor_group"),
                TodoQuery.cd_older_than(since_som, unit="s"),
                # TodoQuery.status([constants.APPLICATION_STATUS_UPDATE_REQUEST]),
                TodoQuery.editor_group(maned_of),
                TodoQuery.is_update_request(),
            ],
            must_nots=[
                TodoQuery.status([
                    constants.APPLICATION_STATUS_ACCEPTED,
                    constants.APPLICATION_STATUS_REJECTED
                ])
            ],
            sort=sort_date,
            size=size
        )
        return constants.TODO_MANED_LAST_MONTH_UPDATE_REQUEST, assign_pending, sort_date, 2

    @classmethod
    def maned_new_update_requests(cls, size, maned_of):
        sort_date = "created_date"
        assign_pending = TodoQuery(
            musts=[
                TodoQuery.exists("admin.editor_group"),
                # TodoQuery.cd_older_than(4),
                # TodoQuery.status([constants.APPLICATION_STATUS_UPDATE_REQUEST]),
                TodoQuery.editor_group(maned_of),
                TodoQuery.is_update_request()
            ],
            must_nots=[
                TodoQuery.status([
                    constants.APPLICATION_STATUS_ACCEPTED,
                    constants.APPLICATION_STATUS_REJECTED
                ])
            ],
            sort=sort_date,
            size=size
        )
        return constants.TODO_MANED_NEW_UPDATE_REQUEST, assign_pending, sort_date, -2

    @classmethod
    def maned_on_hold(cls, size, account, maned_of):
        sort_date = "created_date"
        on_holds = TodoQuery(
            musts=[
                TodoQuery.is_new_application(),
                TodoQuery.status([constants.APPLICATION_STATUS_ON_HOLD])
            ],
            ors=[
                TodoQuery.editor_group(maned_of),
                TodoQuery.editor(account)
            ],
            sort=sort_date,
            size=size
        )
        return constants.TODO_MANED_ON_HOLD, on_holds, sort_date, 0

    @classmethod
    def editor_stalled(cls, groups, size):
        sort_date = "created_date"
        stalled = TodoQuery(
            musts=[
                TodoQuery.lmu_older_than(6),
                TodoQuery.editor_groups(groups),
                TodoQuery.is_new_application()
            ],
            must_nots=[
                TodoQuery.status([
                    constants.APPLICATION_STATUS_ACCEPTED,
                    constants.APPLICATION_STATUS_REJECTED,
                    constants.APPLICATION_STATUS_READY,
                    constants.APPLICATION_STATUS_ON_HOLD
                ])
            ],
            sort=sort_date,
            size=size
        )
        return constants.TODO_EDITOR_STALLED, stalled, sort_date, 0

    @classmethod
    def editor_follow_up_old(cls, groups, size):
        sort_date = "created_date"
        follow_up_old = TodoQuery(
            musts=[
                TodoQuery.cd_older_than(8),
                TodoQuery.editor_groups(groups),
                TodoQuery.is_new_application()
            ],
            must_nots=[
                TodoQuery.status([
                    constants.APPLICATION_STATUS_ACCEPTED,
                    constants.APPLICATION_STATUS_REJECTED,
                    constants.APPLICATION_STATUS_READY,
                    constants.APPLICATION_STATUS_ON_HOLD
                ])
            ],
            sort=sort_date,
            size=size
        )
        return constants.TODO_EDITOR_FOLLOW_UP_OLD, follow_up_old, sort_date, 0

    @classmethod
    def editor_completed(cls, groups, size):
        sort_date = "created_date"
        completed = TodoQuery(
            musts=[
                TodoQuery.status([constants.APPLICATION_STATUS_COMPLETED]),
                TodoQuery.editor_groups(groups),
                TodoQuery.is_new_application()
            ],
            sort=sort_date,
            size=size
        )
        return constants.TODO_EDITOR_COMPLETED, completed, sort_date, 1

    @classmethod
    def editor_assign_pending(cls, groups, size):
        sort_date = "created_date"
        assign_pending = TodoQuery(
            musts=[
                TodoQuery.status([constants.APPLICATION_STATUS_PENDING]),
                TodoQuery.is_new_application()
            ],
            must_nots=[
                TodoQuery.exists("admin.editor")
            ],
            sort=sort_date,
            size=size
        )
        return constants.TODO_EDITOR_ASSIGN_PENDING, assign_pending, sort_date, 1

    @classmethod
    def associate_stalled(cls, acc_id, size):
        sort_field = "created_date"
        stalled = TodoQuery(
            musts=[
                TodoQuery.lmu_older_than(3),
                TodoQuery.editor(acc_id),
                TodoQuery.is_new_application()
            ],
            must_nots=[
                TodoQuery.status([
                    constants.APPLICATION_STATUS_ACCEPTED,
                    constants.APPLICATION_STATUS_REJECTED,
                    constants.APPLICATION_STATUS_READY,
                    constants.APPLICATION_STATUS_COMPLETED,
                    constants.APPLICATION_STATUS_ON_HOLD
                ])
            ],
            sort=sort_field,
            size=size
        )
        return constants.TODO_ASSOCIATE_PROGRESS_STALLED, stalled, sort_field, 0

    @classmethod
    def associate_follow_up_old(cls, acc_id, size):
        sort_field = "created_date"
        follow_up_old = TodoQuery(
            musts=[
                TodoQuery.cd_older_than(6),
                TodoQuery.editor(acc_id),
                TodoQuery.is_new_application()
            ],
            must_nots=[
                TodoQuery.status([
                    constants.APPLICATION_STATUS_ACCEPTED,
                    constants.APPLICATION_STATUS_REJECTED,
                    constants.APPLICATION_STATUS_READY,
                    constants.APPLICATION_STATUS_COMPLETED,
                    constants.APPLICATION_STATUS_ON_HOLD
                ])
            ],
            sort=sort_field,
            size=size
        )
        return constants.TODO_ASSOCIATE_FOLLOW_UP_OLD, follow_up_old, sort_field, 0

    @classmethod
    def associate_start_pending(cls, acc_id, size):
        sort_field = "created_date"
        assign_pending = TodoQuery(
            musts=[
                TodoQuery.editor(acc_id),
                TodoQuery.status([constants.APPLICATION_STATUS_PENDING]),
                TodoQuery.is_new_application()
            ],
            sort=sort_field,
            size=size
        )
        return constants.TODO_ASSOCIATE_START_PENDING, assign_pending, sort_field, 0

    @classmethod
    def associate_all_applications(cls, acc_id, size):
        sort_field = "created_date"
        all = TodoQuery(
            musts=[
                TodoQuery.editor(acc_id),
                TodoQuery.is_new_application()
            ],
            must_nots=[
                TodoQuery.status([
                    constants.APPLICATION_STATUS_ACCEPTED,
                    constants.APPLICATION_STATUS_REJECTED,
                    constants.APPLICATION_STATUS_READY,
                    constants.APPLICATION_STATUS_COMPLETED,
                    constants.APPLICATION_STATUS_ON_HOLD
                ])
            ],
            sort=sort_field,
            size=size
        )
        return constants.TODO_ASSOCIATE_ALL_APPLICATIONS, all, sort_field, -1


class TodoQuery(object):
    """
    ~~->$Todo:Query~~
    ~~^->Elasticsearch:Technology~~
    """
    lmu_sort = {"last_manual_update": {"order": "asc"}}
    # cd_sort = {"created_date" : {"order" : "asc"}}
    # NOTE that admin.date_applied and created_date should be the same for applications, but for some reason this is not always the case
    # therefore, we take a created_date sort to mean a date_applied sort
    cd_sort = {"admin.date_applied": {"order": "asc"}}

    def __init__(self, musts=None, must_nots=None, ors=None, sort="last_manual_update", size=10):
        self._musts = [] if musts is None else musts
        self._must_nots = [] if must_nots is None else must_nots
        self._ors = [] if ors is None else ors
        self._sort = sort
        self._size = size

    def query(self):
        sort = self.lmu_sort if self._sort == "last_manual_update" else self.cd_sort
        q = {
            "query": {
                "bool": {
                    "must": self._musts,
                    "must_not": self._must_nots
                }
            },
            "sort": [
                sort
            ],
            "size": self._size
        }

        if len(self._musts) > 0:
            q["query"]["bool"]["must"] = self._musts
        if len(self._must_nots) > 0:
            q["query"]["bool"]["must_not"] = self._must_nots
        if len(self._ors) > 0:
            q["query"]["bool"]["should"] = self._ors
            q["query"]["bool"]["minimum_should_match"] = 1

        return q

    @classmethod
    def is_new_application(cls):
        return {
            "term": {
                "admin.application_type.exact": constants.APPLICATION_TYPE_NEW_APPLICATION
            }
        }

    @classmethod
    def is_update_request(cls):
        return {
            "term": {
                "admin.application_type.exact": constants.APPLICATION_TYPE_UPDATE_REQUEST
            }
        }

    @classmethod
    def editor_group(cls, groups):
        return {
            "terms": {
                "admin.editor_group.exact": [g.name for g in groups]
            }
        }

    @classmethod
    def lmu_older_than(cls, weeks):
        return {
            "range": {
                "last_manual_update": {
                    "lte": "now-" + str(weeks) + "w"
                }
            }
        }

    @classmethod
    def cd_older_than(cls, count, unit="w"):
        return {
            "range": {
                "admin.date_applied": {
                    "lte": "now-" + str(count) + unit
                }
            }
        }

    @classmethod
    def status(cls, statuses):
        return {
            "terms": {
                "admin.application_status.exact": statuses
            }
        }

    @classmethod
    def exists(cls, field):
        return {
            "exists": {
                "field": field
            }
        }

    @classmethod
    def editor_groups(cls, groups):
        gids = [g.name for g in groups]
        return {
            "terms": {
                "admin.editor_group.exact": gids
            }
        }

    @classmethod
    def editor(cls, acc_id):
        return {
            "terms": {
                "admin.editor.exact": [acc_id],
            }
        }

    @classmethod
    def flagged_to_me(cls, acc_id):
        return {
            "terms": {
                "index.flag_assignees": [acc_id]
            }
        }


class GroupStatsQuery():
    """
    ~~->$GroupStats:Query~~
    ~~^->Elasticsearch:Technology~~
    """

    def __init__(self, group_name, editor_count=10):
        self.group_name = group_name
        self.editor_count = editor_count

    def query(self):
        return {
            "track_total_hits": True,
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "admin.editor_group.exact": self.group_name
                            }
                        }
                    ],
                    "must_not": [
                        {
                            "terms": {
                                "admin.application_status.exact": [
                                    constants.APPLICATION_STATUS_ACCEPTED,
                                    constants.APPLICATION_STATUS_REJECTED
                                ]
                            }
                        }
                    ]
                }
            },
            "size": 0,
            "aggs": {
                "editor": {
                    "terms": {
                        "field": "admin.editor.exact",
                        "size": self.editor_count
                    },
                    "aggs": {
                        "application_type": {
                            "terms": {
                                "field": "admin.application_type.exact",
                                "size": 2
                            }
                        }
                    }
                },
                "status": {
                    "terms": {
                        "field": "admin.application_status.exact",
                        "size": len(constants.APPLICATION_STATUSES_ALL)
                    },
                    "aggs": {
                        "application_type": {
                            "terms": {
                                "field": "admin.application_type.exact",
                                "size": 2
                            }
                        }
                    }
                },
                "unassigned": {
                    "missing": {
                        "field": "admin.editor.exact"
                    },
                    "aggs": {
                        "application_type": {
                            "terms": {
                                "field": "admin.application_type.exact",
                                "size": 2
                            }
                        }
                    }
                }
            }
        }


class HistoricalNumbersQuery:
    """
    ~~->$HistoricalNumbers:Query~~
    ~~^->Elasticsearch:Technology~~
    """

    def __init__(self, editor, application_status, editor_group=None, year=None):
        self.editor_group = editor_group
        self.editor = editor
        self.application_status = application_status
        self.year = year

    def query(self):
        if self.year is None:
            date_range = {"gte": "now/y", "lte": "now"}
        else:
            date_range = {
                "gte": f"{self.year}-01-01",
                "lte": f"{self.year}-12-31"
            }
        must_terms = [{"range": {"last_updated": date_range}},
                      {"term": {"type": "suggestion"}},
                      {"term": {"user.exact": self.editor}},
                      {"term": {"action": self.application_status}}
                      ]

        if self.editor_group:
            must_terms.append({"term": {"editor_group": self.editor_group}})

        return {
            "query": {
                "bool": {
                    "must": must_terms
                }
            }
        }
