from portality import constants
from portality.lib import dates
from portality.models import Account


CUTOFF_DATE = dates.parse("2026-09-03T00:00:00Z")
ROLES_TO_ASSIGN = [constants.ROLE_PUBLISHER, constants.ROLE_API]


class AccountsCreatedSinceQuery(object):
    def __init__(self, since):
        self.since = since

    def query(self):
        return {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"created_date": {"gte": dates.format(self.since)}}}
                    ]
                }
            }
        }


def assign_roles():
    checked = 0
    updated = 0
    query = AccountsCreatedSinceQuery(CUTOFF_DATE)

    for acc in Account.iterate(q=query.query(), page_size=1000, keepalive="5m"):
        checked += 1
        changed = False

        for role in ROLES_TO_ASSIGN:
            if acc.has_role(role):
                continue
            acc.add_role(role)
            changed = True

        if changed:
            acc.save()
            updated += 1

    return checked, updated


if __name__ == "__main__":
    checked, updated = assign_roles()
    print("Checked {} accounts".format(checked))
    print("Updated {} accounts".format(updated))
