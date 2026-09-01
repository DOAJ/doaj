from portality.models import Account
import csv
from portality.core import app


def apply_user_roles(source):
    report = {"upgraded": [], "missing": []}
    with open(source, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 0:
                continue
            username = row[0]
            if username is None or username.strip() == "":
                continue
            roles = [r.strip() for r in row[1].split(",")]
            if len(roles) == 0:
                continue
            acc, applied, skipped = apply_roles(username, roles)
            if acc is None:
                report["missing"].append(username)
            else:
                report["upgraded"].append({"username": username, "applied": applied, "skipped": skipped})
    return report


def apply_roles(username, roles):
    acc = Account.pull(username)
    if not acc:
        return None, None, None

    allowed = app.config.get("TOP_LEVEL_ROLES", [])
    apply = [r for r in roles if r in allowed]
    skip = [r for r in roles if r not in allowed]
    for role in apply:
        acc.add_role(role)

    acc.save()
    return acc, apply, skip

if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, script cannot run")
        exit()

    import argparse, getpass
    parser = argparse.ArgumentParser()

    parser.add_argument("csv", help="csv of users, and roles to assign/add")

    args = parser.parse_args()
    
    if not args.csv:
        print("Please specify a csv of existing users and their new roles to add")
        exit()

    report = apply_user_roles(args.csv)

    print("The following users were upgraded: ")
    for u in report["upgraded"]:
        print("  - " + u["username"] + " (applied: " + ", ".join(u["applied"]) + "; skipped: " + ", ".join(u["skipped"]) + ")")
    if len(report["missing"]) > 0:
        print("The following users were not found: ")
        for u in report["missing"]:
            print("  - " + u)

