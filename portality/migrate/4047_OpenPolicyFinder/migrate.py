import json, csv
import time
from collections import OrderedDict

from portality.upgrade import do_upgrade
from portality.models import Journal, Application

SR = {
    "query": {
        "bool": {
            "must": [{
                "term": {
                    "bibjson.deposit_policy.service.exact": "Sherpa/Romeo"
                }
            }]
        }
    }
}

OPF = {
    "query": {
        "bool": {
            "must": [{
                "term": {
                    "bibjson.deposit_policy.service.exact": "Open Policy Finder"
                }
            }]
        }
    }
}

if __name__ == "__main__":
    records_to_change = {}
    records_changed = {}

    for journal in Journal.iterate(q=SR, keepalive='5m', wrap=True):
        records_to_change[journal.id] = journal.bibjson().deposit_policy

    for app in Application.iterate(q=SR, keepalive='5m', wrap=True):
        records_to_change[app.id] = app.bibjson().deposit_policy

    with open("migrate.json") as f:
        try:
            instructions = json.loads(f.read(), object_pairs_hook=OrderedDict)
        except:
            print("migrate.json does not parse as JSON")
            exit()

    do_upgrade(definition=instructions, verbose=False)

    print("verify")

    time.sleep(3)

    for journal in Journal.iterate(q=OPF, keepalive='5m', wrap=True):
        records_changed[journal.id] = journal.bibjson().deposit_policy

    for app in Application.iterate(q=OPF, keepalive='5m', wrap=True):
        records_changed[app.id] = app.bibjson().deposit_policy

    incorrect_changes = {
        rid for rid, old_values in records_to_change.items() if
        records_changed.get(rid) and ["Open Policy Finder" if val == "Sherpa/Romeo" else val for val in old_values] != records_changed[rid]
    }

    unexpected_changes = {rid for rid in records_changed if rid not in records_to_change}
    records_not_changed = {rid for rid in records_to_change if rid not in records_changed}

    if incorrect_changes or unexpected_changes or records_not_changed:
        with open("output.csv", "w", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Old deposit policy value", "New deposit policy value", "status"])
            for rid in incorrect_changes:
                writer.writerow([rid, records_to_change[rid], records_changed[rid], "incorrect change"])
            for rid in records_not_changed:
                writer.writerow([rid, records_to_change[rid], "", "no change"])
            for rid in unexpected_changes:
                writer.writerow([rid, "", records_changed[rid], "unexpected change"])
        print("Something went wrong, check 'output.csv' log file for details")
    else:
        print("Success")

