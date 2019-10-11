import codecs, json, os, csv
from portality import clcsv

# DATE = "2018-05-10"
DATE=None

REVERTED_ONLY = True

JOURNAL_CSV = "/home/richard/tmp/doaj/history/journals.csv"

OUT_DIR = "/home/richard/tmp/doaj/history/workspace/"

def history_records_analyse(source, out_dir, reverted_only=False, date=None):
    ids = set()
    if date is not None:
        with codecs.open(source, "rb", "utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row[1] == date:
                    ids.add(row[0])

    records = {}
    with codecs.open(source, "rb", "utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if date is None or row[0] in ids:
                if row[0] not in records:
                    records[row[0]] = []
                records[row[0]].append(row[:3])

    count = 1
    out = os.path.join(out_dir, "owners.csv")
    with codecs.open(out, "wb", "utf-8") as o:
        writer = csv.writer(o)
        writer.writerow(["count", "id", "reverted", "change history"])
        writer.writerow([])

        for id, rows in records.items():
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

            out_row_1 = [o[0] for o in owners]
            out_row_2 = [o[1] for o in owners]
            owner_set = set(out_row_2)

            if date is None: flagged = True

            if len(owner_set) > 1 and flagged:
                reverted = False
                for i in range(len(ownerTransitions)):
                    o = ownerTransitions[i]
                    if i + 2 < len(ownerTransitions):
                        for j in range(i + 2, len(ownerTransitions)):
                            comp = ownerTransitions[j]
                            if o == comp:
                                reverted = True
                                break
                    if reverted:
                        break

                if not reverted_only or (reverted_only and reverted):
                    writer.writerow([count, id, "X" if reverted else ""] + out_row_1)
                    writer.writerow(["", "", "X" if reverted else ""] + out_row_2)
                    writer.writerow([])
                    count += 1


if __name__ == "__main__":
    history_records_analyse(JOURNAL_CSV, OUT_DIR, REVERTED_ONLY, DATE)