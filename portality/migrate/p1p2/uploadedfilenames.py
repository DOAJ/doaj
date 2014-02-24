import os, csv
from datetime import datetime

upload_dir = "/home/richard/tmp/doaj/uploads/doaj-xml"
txt_files = [f for f in os.listdir(upload_dir) if f.endswith(".txt")]

out_file = "/home/richard/tmp/doaj/uploads/summary.csv"
writer = csv.writer(open(out_file, "wb"))
writer.writerow(["Publisher/Username", "Filename", "Date uploaded", "Upload ID"])

for f in txt_files:
    path = os.path.join(upload_dir, f)
    txt = open(path)
    publisher = txt.readline()
    filename = txt.readline()
    lm = os.path.getmtime(path)
    id = f.split(".")[0]
    
    writer.writerow([publisher.strip(), filename.strip(), datetime.fromtimestamp(lm).strftime("%Y-%m-%d %H:%M:%S"), id])
