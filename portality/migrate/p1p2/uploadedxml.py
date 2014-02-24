import os, csv
from lxml import etree
from portality import article, models
from datetime import datetime

xml_dir = "/home/richard/tmp/doaj/uploads/doaj-xml"
xml_files = [f for f in os.listdir(xml_dir) if f.endswith(".xml")]

out_dir = "/home/richard/tmp/doaj/uploads/output"
success_file = os.path.join(out_dir, "success.csv")
malformed_file = os.path.join(out_dir, "malformed.csv")
invalid_file = os.path.join(out_dir, "invalid.csv")
orphan_file = os.path.join(out_dir, "orphan.csv")

success_writer = csv.writer(open(success_file, "wb"))
malformed_writer = csv.writer(open(malformed_file, "wb"))
invalid_writer = csv.writer(open(invalid_file, "wb"))
orphan_writer = csv.writer(open(orphan_file, "wb"))

success_writer.writerow(["DOAJ Filename", "Publisher", "Original Filename", "Date Uploaded"])
malformed_writer.writerow(["DOAJ Filename", "Publisher", "Original Filename", "Date Uploaded", "Contact Email"])
invalid_writer.writerow(["DOAJ Filename", "Publisher", "Original Filename", "Date Uploaded", "Contact Email"])
orphan_writer.writerow(["DOAJ Filename", "Publisher", "Original Filename", "Date Uploaded"])

xwalk = article.DOAJXWalk()   

def article_callback(article):
    article.save()
    print "saved article", article.id

failed = 0
valid = 0
invalid = 0
for f in xml_files:
    # first get all the meta information about the upload
    id = f.split(".")[0]
    txt_file = os.path.join(xml_dir, id + ".txt")
    txt = open(txt_file)
    publisher = txt.readline().strip()
    filename = txt.readline().strip()
    lm = os.path.getmtime(txt_file)
    uploaded = datetime.fromtimestamp(lm).strftime("%Y-%m-%d %H:%M:%S")
    txt.close()
    
    # now determine if the publisher is legitimate.  If we don't find
    # a user account, then we ignore the file
    acc = models.Account.pull(publisher)
    if acc is None:
        print f, "No such publisher -", publisher
        orphan_writer.writerow([f, publisher, filename, uploaded])
        continue
    
    # now try and parse the file
    doc = None
    try:
        doc = etree.parse(open(os.path.join(xml_dir, f)))
    except:
        failed += 1
        print f, "Malformed XML"
        malformed_writer.writerow([f, publisher, filename, uploaded, acc.email])
        continue
    
    # now try and validate the file
    validates = xwalk.validate(doc)
    print f, ("Valid" if validates else "Invalid")
    
    if validates: 
        valid += 1
        success_writer.writerow([f, publisher, filename, uploaded])
    
    if not validates: 
        invalid += 1
        invalid_writer.writerow([f, publisher, filename, uploaded, acc.email])
    
    if validates:
        xwalk.crosswalk_doc(doc, article_callback=article_callback)
    

print "valid", valid, "invalid", invalid, "failed", failed
