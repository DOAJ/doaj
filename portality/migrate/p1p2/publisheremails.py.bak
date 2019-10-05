import os, csv
from portality import models, settings
from datetime import datetime
from StringIO import StringIO

corrections_csv = os.path.join(os.path.dirname(os.path.realpath(__file__)), "corrections.csv")
malformed_csv = os.path.join(os.path.dirname(os.path.realpath(__file__)), "malformed.csv")
invalid_csv = os.path.join(os.path.dirname(os.path.realpath(__file__)), "invalid.csv")

malformed_sio = StringIO()
malformed_writer = csv.writer(malformed_sio)
malformed_file = open(malformed_csv)
malformed_reader = csv.reader(malformed_file)

invalid_sio = StringIO()
invalid_writer = csv.writer(invalid_sio)
invalid_file = open(invalid_csv)
invalid_reader = csv.reader(invalid_file)

malformed_writer.writerow(["DOAJ Filename", "Publisher", "Original Filename", "Date Uploaded", "Contact Email"])
invalid_writer.writerow(["DOAJ Filename", "Publisher", "Original Filename", "Date Uploaded", "Contact Email"])

# start by reading in the publisher id corrections 
corrections = {}
reader = csv.reader(open(corrections_csv))
first = True
for row in reader:
    if first:
        first = False
        continue
    id = row[0]
    publisher = row[4]
    corrections[id] = publisher

first = True
for row in malformed_reader:
    if first:
        first = False
        continue
    id = row[0].split(".")[0]
    publisher = row[1]
    if id in corrections:
        publisher = corrections[id]
    acc = models.Account.pull(publisher)
    if acc is None:
        print publisher, "fail - shouldn't happen"
        continue
    
    new_row = row[:4] + [acc.email]
    malformed_writer.writerow(new_row)
malformed_file.close()
f = open(malformed_csv, "wb")
f.write(malformed_sio.getvalue())
f.close()

first = True
for row in invalid_reader:
    if first:
        first = False
        continue
    id = row[0].split(".")[0]
    publisher = row[1]
    if id in corrections:
        publisher = corrections[id]
    acc = models.Account.pull(publisher)
    if acc is None:
        print publisher, "fail - shouldn't happen"
        continue
    
    new_row = row[:4] + [acc.email]
    invalid_writer.writerow(new_row)
invalid_file.close()
f = open(invalid_csv, "wb")
f.write(invalid_sio.getvalue())
f.close()


