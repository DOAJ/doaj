import codecs, json, os
from portality import clcsv

DATE = "2018-05-10"

JOURNAL_CSV = "/home/richard/tmp/doaj/history/journals.csv"

OUT_DIR = "/home/richard/tmp/doaj/history/workspace/"

def history_records_analyse(date, source, out_dir):
    ids = set()
    with codecs.open(source, "rb", "utf-8") as f:
        reader = clcsv.UnicodeReader(f)
        for row in reader:
            if row[1] == date:
                ids.add(row[0])

    records = {}
    with codecs.open(source, "rb", "utf-8") as f:
        reader = clcsv.UnicodeReader(f)
        for row in reader:
            if row[0] in ids:
                if row[0] not in records:
                    records[row[0]] = []
                records[row[0]].append(row)

    count = 1
    out = os.path.join(out_dir, "owners.csv")
    with codecs.open(out, "wb", "utf-8") as o:
        writer = clcsv.UnicodeWriter(o)
        writer.writerow(["count", "id", "reverted", "change history"])
        writer.writerow([])

        for id, rows in records.iteritems():
            rows = sorted(rows, key=lambda x: x[1])
            owners = []
            lastOwner = False
            ownerTransitions = []
            flagged = False
            for row in rows:
                with codecs.open(row[2], "rb", "utf-8") as f:
                    data = json.load(f)
                owner = data.get("admin", {}).get("owner")
                if len(ownerTransitions) == 0 or owner != ownerTransitions[-1]:
                    ownerTransitions.append(owner)
                if owner != lastOwner and row[1] == date:
                    flagged = True
                owners.append((row[1], owner))
                lastOwner = owner

            reverted = False
            if len(ownerTransitions) != len(set(ownerTransitions)):
                reverted = True

            out_row_1 = [o[0] for o in owners]
            out_row_2 = [o[1] for o in owners]
            owner_set = set(out_row_2)

            if len(owner_set) > 1 and flagged:
                writer.writerow([count, id, "X" if reverted else ""] + out_row_1)
                writer.writerow(["", "", "X" if reverted else ""] + out_row_2)
                writer.writerow([])
                count += 1


if __name__ == "__main__":
    history_records_analyse(DATE, JOURNAL_CSV, OUT_DIR)