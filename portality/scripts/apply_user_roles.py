from portality.models import Account
import csv
from portality.core import app


def apply_user_roles(source):
    report = {"upgraded": [], "missing": []}
    with open(source, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            username = row[0]
            roles = [r.strip() for r in row[3].split(",")]
            acc = apply_roles(username, roles)
            if acc is None:
                report["missing"].append(username)
            else:
                report["upgraded"].append(username)
    return report


def apply_roles(username, roles, overwrite_roles=False):
    acc = Account.pull(username)
    if not acc:
        return None

    for role in roles:
        acc.add_role(role)
    acc.set_role(roles)
    acc.save()
    return acc

if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, script cannot run")
        exit()

    import argparse, getpass
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--csv", help="csv of users, and roles to assign/add")
    
    args = parser.parse_args()
    
    if not args.csv:
        print("Please specify a csv of users to create")
        exit()

    report = apply_user_roles(args.csv)

    print("The following users were upgraded: ")
    for u in report["upgraded"]:
        print("  - " + u)
    if len(report["missing"]) > 0:
        print("The following users were not found: ")
        for u in report["missing"]:
            print("  - " + u)

