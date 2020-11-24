import csv
import esprit

from portality import models
from portality.core import es_connection
from portality.util import ipt_prefix


def make_csv(start, end, out):
    q = {
        "query" : {
            "bool" : {
                "must" : [
                    {"range" : {"last_updated" : {"gte" : start, "lte" : end}}},
                    {"term" : {"admin.application_status" : "rejected"}}
                ]
            }
        }
    }

    conn = es_connection

    with open(out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Last Updated", "Is Quick Reject?", "Suggester Name", "Suggester Email", "Owner ID", "Owner Name", "Owner Email",
                         "Title", "ISSNS", "Quick Reject Note Date", "All Notes"])
        for source in esprit.tasks.scroll(conn, ipt_prefix("suggestion"), q):
            application = models.Suggestion(**source)

            qr_note = None
            for n in application.notes:
                if ": This application was rejected with the reason '" in n.get("note"):
                    qr_note = n
                    break

            owner_id = application.owner
            owner = None
            if owner_id is not None:
                owner = models.Account.pull(owner_id)

            summary = {
                "id" : application.id,
                "last_updated" : application.last_updated,
                "quick_reject_note_date" : "" if qr_note is None else qr_note.get("date"),
                "suggester_name" : application.suggester.get("name"),
                "suggester_email" : application.suggester.get("email"),
                "owner" : application.owner,
                "owner_name" : owner.name if owner is not None else "",
                "owner_email" : owner.email if owner is not None else "",
                "notes" : "\n".join([n.get("date") + " - " + n.get("note") for n in application.notes]),
                "is_quick_reject" : "True" if qr_note is not None else "",
                "title" : application.bibjson().title,
                "issns" : ",".join(application.bibjson().issns())
            }

            writer.writerow([summary["id"], summary["last_updated"], summary["is_quick_reject"], summary["suggester_name"],
                             summary["suggester_email"], summary["owner"], summary["owner_name"], summary["owner_email"],
                             summary["title"], summary["issns"], summary["quick_reject_note_date"], summary["notes"]])



if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--out",
                        help="Output file for CSV of rejection report",
                        default="missing_quick_rejects.csv")
    parser.add_argument("-s", "--start",
                        help="Last updated timestamp to consider rejections from (inclusive)",
                        default="2018-11-29T00:00:00Z")
    parser.add_argument("-e", "--end",
                        help="Last updated timestamp to consider rejections to (inclusive)",
                        default="2018-12-13T23:59:59Z")

    args = parser.parse_args()

    make_csv(args.start, args.end, args.out)