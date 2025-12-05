from portality.app import app
import csv

def list_write_required_routes(app):
    """Return a list of dicts for all URL rules whose view is marked by write_required."""
    routes = []
    for rule in app.url_map.iter_rules():
        view = app.view_functions.get(rule.endpoint)
        if view is None:
            continue
        if getattr(view, "_write_required", False):
            methods = sorted(m for m in rule.methods if m not in ("HEAD", "OPTIONS"))
            routes.append({
                "rule": rule.rule,
                "endpoint": rule.endpoint,
                "methods": methods
            })
    return routes

routes = list_write_required_routes(app)
with open("write_required_routes.csv", "w", newline='') as csvfile:
    fieldnames = ["rule", "endpoint", "methods"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for route in routes:
        writer.writerow({
            "rule": route["rule"],
            "endpoint": route["endpoint"],
            "methods": ", ".join(route["methods"])
        })