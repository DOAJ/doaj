from portality.models import Account
import csv

OUT = "emails.csv"

f = open(OUT, "wb")
writer = csv.writer(f)
writer.writerow(["ID", "Name", "Journal Count", "Email"])

for a in Account.iterall():
    id = a.id
    name = a.name
    count = len(a.journal) if a.journal is not None else 0
    email = a.email
    if name is not None:
        name = name.encode("ascii", "ignore")
    if name is None or name == "":
        name = "no name available"
    if email is not None and email != "":
        email = email.encode("ascii", "ignore")
        writer.writerow([id, name, count, email])

f.close()
