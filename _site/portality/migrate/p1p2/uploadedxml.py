import os, csv
from lxml import etree
from portality import models, settings
from portality.models import article
from datetime import datetime

start = datetime.now()

corrections_csv = os.path.join(os.path.dirname(os.path.realpath(__file__)), "corrections.csv")
xml_dir = settings.UPLOAD_DIR

# xml_dir = "/home/richard/tmp/doaj/uploads/doaj-xml"
# corrections_csv = "/home/richard/Dropbox/Documents/DOAJ/corrections.csv"

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

txt_files = [f for f in os.listdir(xml_dir) if f.endswith(".txt")]

# out_dir = "/home/richard/tmp/doaj/uploads/output"
out_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)))
success_file = os.path.join(out_dir, "success.csv")
malformed_file = os.path.join(out_dir, "malformed.csv")
invalid_file = os.path.join(out_dir, "invalid.csv")
orphan_file = os.path.join(out_dir, "orphan.csv")
duplicate_file = os.path.join(out_dir, "duplicate.csv")
failed_articles = os.path.join(out_dir, "failed_articles.csv")

success_writer = csv.writer(open(success_file, "wb"))
malformed_writer = csv.writer(open(malformed_file, "wb"))
invalid_writer = csv.writer(open(invalid_file, "wb"))
orphan_writer = csv.writer(open(orphan_file, "wb"))
duplicate_writer = csv.writer(open(duplicate_file, "wb"))
failed_articles_writer = csv.writer(open(failed_articles, "wb"))

success_writer.writerow(["DOAJ Filename", "Publisher", "Original Filename", "Date Uploaded"])
malformed_writer.writerow(["DOAJ Filename", "Publisher", "Original Filename", "Date Uploaded", "Contact Email"])
invalid_writer.writerow(["DOAJ Filename", "Publisher", "Original Filename", "Date Uploaded", "Contact Email"])
orphan_writer.writerow(["DOAJ Filename", "Publisher", "Original Filename", "Date Uploaded"])
duplicate_writer.writerow(["Old ID", "Publisher", "Original Filename", "Date Uploaded"])
failed_articles_writer.writerow(["File ID", "Publisher", "Original Filename", "Date Uploaded", "ISSN", "E-ISSN", "Article Title"])

xwalk = article.DOAJXWalk()

total = len(txt_files)
orphaned = 0
duplicate = 0
failed = 0
valid = 0
invalid = 0
processed = 0
attempted = 0
articles_in = 0
articles_failed = 0
articles_updated = 0
articles_new = 0

print("importing", total, "files from", xml_dir)

def article_save_closure(upload_id):
    def article_callback(article):
        global articles_in
        articles_in += 1
        article.set_upload_id(upload_id)
        article.save()
        print("saved article", article.id)
    return article_callback

"""
def article_callback(article):
    global articles_in
    articles_in += 1
    article.save()
    print "saved article", article.id
"""

def fail_closure(id, publisher, filename, uploaded):
    def fail_callback(article):
        global articles_failed
        articles_failed += 1
        b = article.bibjson()
        title = b.title
        pissn = b.get_identifiers(b.P_ISSN)
        eissn = b.get_identifiers(b.E_ISSN)
        if title is not None:
            title = title.encode("ascii", errors="ignore")
        print("illegitimate owner", title)
        failed_articles_writer.writerow([id, publisher, filename, uploaded, ", ".join(pissn), ", ".join(eissn), title])
    return fail_callback

# read in all the txt files to a datastructure that we can then work with
imports = {}
for t in txt_files:
    processed += 1
    
    txt_file = os.path.join(xml_dir, t)
    txt = open(txt_file)
    
    id = t.split(".")[0]
    publisher = txt.readline().strip()
    filename = txt.readline().strip()
    lm = os.path.getmtime(txt_file)
    uploaded = datetime.fromtimestamp(lm).strftime("%Y-%m-%d %H:%M:%S")
    
    # at this point we apply a correction in the event that we have a 
    # correction for this id
    if id in corrections:
        print(t, "correcting publisher", publisher, "-", corrections[id])
        publisher = corrections[id]
    
    acc = models.Account.pull(publisher)
    if acc is None:
        print(t, "No such publisher -", publisher)
        orphaned += 1
        orphan_writer.writerow([id, publisher, filename, uploaded])
        continue
    
    if publisher in imports:
        if filename in imports[publisher]:
            preup = list(imports[publisher][filename].keys())[0]
            duplicate += 1
            if lm > preup:
                rid = imports[publisher][filename][preup]
                ruploaded = datetime.fromtimestamp(preup).strftime("%Y-%m-%d %H:%M:%S")
                #print id, publisher, filename, "seen before, so ignoring", rid
                duplicate_writer.writerow([rid, publisher, filename, ruploaded])
                imports[publisher][filename] = {lm : id}
            else:
                duplicate_writer.writerow([id, publisher, filename, uploaded])
                
        else:
            #print "remembering", publisher, filename, lm, id
            imports[publisher][filename] = {lm : id}
    else:
        #print "remembering", publisher, filename, lm, id
        imports[publisher] = { filename : {lm : id} }

# so what we should have by here is an object listing publishers and then unique filenames
# per publisher, which represent the most recent file of that name, then the last mod date
# then the id of the file to be imported

# our next task is to sequence the items in the order that we're going to import them
# they must be imported in date order for each publisher
# so we're restructuring the data so that we can process it in the order that the
# files were uploaded
lastmods = []
lookup = {}
for publisher, files in imports.items():
    for filename, details in files.items():
        lm = list(details.keys())[0]
        id = details[lm]
        
        lastmods.append(lm)
        if lm not in lookup:
            lookup[lm] = []
        lookup[lm].append({"publisher" : publisher, "filename" : filename, "id" : id})

lastmods = list(set(lastmods))
lastmods.sort()

for lm in lastmods:
    for obj in lookup[lm]:
        attempted += 1
        
        publisher = obj["publisher"]
        filename = obj["filename"]
        id = obj["id"]        
        
        f = id + ".xml"
        xml_file = os.path.join(xml_dir, f)
        uploaded = datetime.fromtimestamp(lm).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        upload = models.FileUpload()
        upload.set_schema(xwalk.format_name)
        upload.upload(publisher, filename)
        upload.set_created(uploaded)
        upload.set_id()
        
        # now try and parse the file
        doc = None
        try:
            doc = etree.parse(open(xml_file))
        except:
            failed += 1
            print(f, "Malformed XML")
            malformed_writer.writerow([f, publisher, filename, uploaded, acc.email])
            upload.failed("Unable to parse file")
            upload.save()
            continue
        
        # now try and validate the file
        validates = xwalk.validate(doc)
        print(f, ("Valid" if validates else "Invalid"))
        
        if validates: 
            valid += 1
            success_writer.writerow([f, publisher, filename, uploaded])
        
        if not validates: 
            invalid += 1
            invalid_writer.writerow([f, publisher, filename, uploaded, acc.email])
            upload.failed("File could not be validated against a known schema")
            upload.save()
            continue
        
        if validates:
            cb = article_save_closure(upload.id)
            result = xwalk.crosswalk_doc(doc, article_callback=cb, limit_to_owner=publisher, fail_callback=fail_closure(f, publisher, filename, uploaded))
            
            success = result["success"]
            fail = result["fail"]
            update = result["update"]
            new = result["new"]
            
            articles_updated += update
            articles_new += new
            
            if success == 0 and fail > 0:
                upload.failed("All articles in file failed to import")
            if success > 0 and fail == 0:
                upload.processed(success, update, new)
            if success > 0 and fail > 0:
                upload.partial(success, fail, update, new)
            upload.save()

end = datetime.now()

print("Total", total, "attempted", attempted, "valid", valid, "invalid", invalid, "failed", failed, "duplicate", duplicate, "orphaned", orphaned)
print("Created Articles", articles_in, "Failed Articles", articles_failed)
print("New Articles", articles_new, "Updated Articles", articles_updated)
print(start, end)
