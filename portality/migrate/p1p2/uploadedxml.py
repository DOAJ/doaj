import os
from lxml import etree
from portality import article

xml_dir = "/home/richard/tmp/doaj/uploads/doaj-xml"
xml_files = [f for f in os.listdir(xml_dir) if f.endswith(".xml")]

xwalk = article.DOAJXWalk()

def article_callback(article):
    article.save()
    print "saved article", article.id

failed = 0
valid = 0
invalid = 0
for f in xml_files:
    doc = None
    try:
        doc = etree.parse(open(os.path.join(xml_dir, f)))
    except:
        failed += 1
        print f, "Malformed XML"
        continue
        
    validates = xwalk.validate(doc)
    print f, ("Valid" if validates else "Invalid")
    
    if validates: valid += 1
    if not validates: invalid += 1
    
    if validates:
        xwalk.crosswalk_doc(doc, article_callback=article_callback)
    

print "valid", valid, "invalid", invalid, "failed", failed
