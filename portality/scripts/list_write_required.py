from portality.app import app
import csv
from portality.lib.paths import rel2abs

def list_write_required_routes(app):
    """Return a list of dicts for all URL rules whose view is marked by write_required."""
    writable = []
    readable = []
    for rule in app.url_map.iter_rules():
        view = app.view_functions.get(rule.endpoint)
        if view is None:
            continue
        if getattr(view, "_write_required", False):
            methods = sorted(m for m in rule.methods if m not in ("HEAD", "OPTIONS"))
            writable.append({
                "rule": rule.rule,
                "endpoint": rule.endpoint,
                "methods": methods
            })
        else:
            methods = sorted(m for m in rule.methods if m not in ("HEAD", "OPTIONS"))
            readable.append({
                "rule": rule.rule,
                "endpoint": rule.endpoint,
                "methods": methods
            })
    return writable, readable

writable, readable = list_write_required_routes(app)
out = rel2abs(__file__, "..", "..", "deploy", "write_required_routes.csv")
with open(out, "w", newline='') as csvfile:
    fieldnames = ["rule", "endpoint", "methods"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for route in writable:
        writer.writerow({
            "rule": route["rule"],
            "endpoint": route["endpoint"],
            "methods": ", ".join(route["methods"])
        })

out = rel2abs(__file__, "..", "..", "deploy", "read_only_routes.csv")
with open(out, "w", newline='') as csvfile:
    fieldnames = ["rule", "endpoint", "methods"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for route in readable:
        writer.writerow({
            "rule": route["rule"],
            "endpoint": route["endpoint"],
            "methods": ", ".join(route["methods"])
        })

