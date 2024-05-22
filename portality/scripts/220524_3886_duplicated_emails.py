from portality.models import Account
from portality.bll.services.query import QueryService
from portality.core import app
import csv

QUERY = {
    "size": 0,
    "query": {
        "match_all": {}
    },
    "aggs": {
        "duplicate_emails": {
            "terms": {
                "script": {
                    "source": "doc['email.exact'].value.toLowerCase()",
                    "lang": "painless"
                },
                "size": 10000,
                "min_doc_count": 2
            }
        }
    }
}

HEADERS = ["EMAIL", "Count"]

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path", required=True)
    args = parser.parse_args()

    admin_account = Account.make_account(email="admin@test.com", username="admin", name="Admin", roles=["admin"])   # create dummy admin account for search purposes
    admin_account.set_password('password123')
    admin_account.save()

    qsvc = QueryService()
    res = qsvc.search('admin_query', 'account', raw_query=QUERY, account=admin_account, additional_parameters={})

    buckets = res["aggregations"]["duplicate_emails"]["buckets"]

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS);

        for row in buckets:
            writer.writerow([row["key"], row["doc_count"]])

    admin_account.delete() # delete dummy account