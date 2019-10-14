"""
Demonstration script for how to generate test matrices from a variety of factors:

* the allowed values per parameter
* The interconnected constraints between parameters
* The results of operations

This first version is just a POC which has been used to generate the matrix for reject_application.  It needs
expanding and generalising before it is properly useful.  Could even be combined with the test classes themselves
to generate the tests on the fly, though that may make review and fixing more difficult.
"""

import csv


def _generate(fields, counters, params):
    record = {}
    for field in fields:
        current = counters[field]["current"]
        record[field] = params[field][current]
    return record


def _count(fields, counters):
    counted = False
    for i in range(len(fields) - 1, -1, -1):
        field = fields[i]
        current = counters[field]["current"]
        if current == counters[field]["max"]:
            counters[field]["current"] = 0
        else:
            counters[field]["current"] += 1
            counted = True
            break

    return counted


def _filter(filters, combo):
    for filter in filters:
        cval = combo[filter["field"]]
        if cval != filter["value"]:
            continue
        for cfield, values in filter["constraints"].items():
            if combo[cfield] not in values:
                return False
    return True


def _add_results(results, combo):
    for result in results:
        trips = 0
        for field, values in result["conditions"].items():
            if combo[field] in values:
                trips += 1
        if trips == len(result["conditions"].keys()):
            for field, value in result["results"].items():
                combo[field] = value
            return


out = "matrix.csv"

order = ["application", "application_status", "account", "prov", "current_journal", "note", "save"]

params = {
    "application": ["none", "exists"],
    "application_status": ["-", "rejected", "accepted", "update_request"],
    "account": ["none", "publisher", "admin"],
    "prov": ["none", "true", "false"],
    "current_journal": ["-", "yes", "no"],
    "note": ["yes", "no"],
    "save": ["success", "fail"]
}

filters = [
    {
        "field": "application",
        "value": "none",
        "constraints": {
            "application_status": ["-"],
            "current_journal": ["-"],
            "save": "success"
        }
    },
    {
        "field": "application_status",
        "value": "-",
        "constraints": {
            "application": ["none"]
        }
    },
    {
        "field": "application_status",
        "value": "rejected",
        "constraints": {
            "application": ["exists"]
        }
    },
    {
        "field": "application_status",
        "value": "accepted",
        "constraints": {
            "application": ["exists"]
        }
    },
    {
        "field": "application_status",
        "value": "update_request",
        "constraints": {
            "application": ["exists"]
        }
    },
    {
        "field": "current_journal",
        "value": "-",
        "constraints": {
            "application": ["none"]
        }
    },
    {
        "field": "current_journal",
        "value": "yes",
        "constraints": {
            "application": ["exists"]
        }
    },
    {
        "field": "current_journal",
        "value": "no",
        "constraints": {
            "application": ["exists"]
        }
    },
    {
        "field": "save",
        "value": "fail",
        "constraints": {
            "application": ["exists"]
        }
    }
]

results_order = ["raises"]

results = [
    {
        "results": {
            "raises": "ArgumentException"
        },
        "conditions": {
            "application": ["none"]
        }
    },
    {
        "results": {
            "raises": "ArgumentException"
        },
        "conditions": {
            "account": ["none"]
        }
    },
    {
        "results": {
            "raises": "ArgumentException"
        },
        "conditions": {
            "prov": ["none"]
        }
    },
    {
        "results": {
            "raises": "AuthoriseException"
        },
        "conditions": {
            "account": ["publisher"]
        }
    },
    {
        "results": {
            "raises": "SaveException"
        },
        "conditions": {
            "save": ["fail"]
        }
    }
]

fields = order
counters = {}
for f in fields:
    counters[f] = { "current" : 0, "max" : len(params[f]) - 1 }

combinations = []
combinations.append(_generate(fields, counters, params))
while True:
    counted = _count(fields, counters)
    if not counted:
        break
    combinations.append(_generate(fields, counters, params))

final = []
for combo in combinations:
    if _filter(filters, combo):
        _add_results(results, combo)
        final.append(combo)

fields += results_order
combinations = final
with open(out, "w", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["test_id"] + fields)
    counter = 0
    for comb in combinations:
        counter += 1
        row = [str(counter)]
        for field in fields:
            row.append(comb.get(field, ""))
        writer.writerow(row)
