import csv, re, os
from portality import models

analysis = os.path.join(os.path.dirname(os.path.realpath(__file__)), "orphan_analysis.csv")
# analysis = "/home/richard/Dropbox/Documents/DOAJ/orphan_analysis2.csv"

out_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)))
corrections = os.path.join(out_dir, "corrections.csv")
ambiguous = os.path.join(out_dir, "ambiguous.csv")
failed = os.path.join(out_dir, "failed.csv")
summary = os.path.join(out_dir, "summary.csv")

reader = csv.reader(open(analysis))
correction_writer = csv.writer(open(corrections, "wb"))
correction_writer.writerow(["Upload ID", "Original Publisher", "Original Filename", "Correction Note", "Corrected Publisher"])
ambiguous_writer = csv.writer(open(ambiguous, "wb"))
ambiguous_writer.writerow(["Upload ID", "Original Publisher", "Original Filename", "Correction Note", "Possible Publishers"])
failed_writer = csv.writer(open(failed, "wb"))
failed_writer.writerow(["Upload ID", "Original Publisher", "Original Filename", "Correction Note"])
summary_writer = csv.writer(open(summary, "wb"))
summary_writer.writerow(["Upload ID", "Possible ISSNs", "Possible Publisher", "Corrected", "Ambiguous", "Failed"])

ISSN_REGEX = re.compile(r'^\d{4}-\d{3}(\d|X|x){1}$')

def extract_owners(journals):
    owners = [j.owner for j in journals if j.owner is not None]
    owners = list(set(owners))
    return owners

def record_ownership(owners, id, original_publisher, original_filename, correction, record):
    corrected_publisher = None
    if len(owners) > 0:
        if len(owners) == 1:
            corrected_publisher = owners[0]
            record[3] = "x"
            correction_writer.writerow([id, original_publisher, original_filename, correction, corrected_publisher])
            return corrected_publisher
        else:
            record[4] = "x"
            ambiguous_writer.writerow([id, original_publisher, original_filename, correction, ",".join(owners)])
    return corrected_publisher

first = True
for row in reader:
    if first:
        first = False
        continue
    
    xml_filename = row[0]
    original_publisher = row[1].strip()
    correction = row[2].strip()
    original_filename = row[3]
    
    corrected_publisher = None
    id = xml_filename.split(".")[0]
    
    # corrections could be issns, possibly comma separated
    possible_issns = [c.strip() for c in correction.split(",") if ISSN_REGEX.match(c.strip())]
    
    # or could be the name of a publisher, or some other note
    possible_publisher = None
    if len(possible_issns) == 0:
        possible_publisher = correction if correction is not None and correction != "" else None
    
    # start a record of what happened to each upload
    record = [id, ",".join(possible_issns), possible_publisher, "", "", ""]
    
    # try to locate a journal for each of the possible issns until we find one
    possible_owners = []
    for issn in possible_issns:
        journals = models.Journal.find_by_issn(issn)
        possible_owners += extract_owners(journals)
    possible_owners = list(set(possible_owners))
    corrected_publisher = record_ownership(possible_owners, id, original_publisher, original_filename, correction, record)
    
    # corrected_publisher = extract_owners(journals, id, original_publisher, original_filename, correction)
    # NOTE: if there is more than one ISSN, then this could happen multiple times for the same upload
    # or even be ambiguous for one ISSN and corrected for another
    
    # if we didn't find a corrected publisher but we do have a possible publisher
    # take a look for a user account
    if corrected_publisher is None and possible_publisher is not None:
        journals = models.Journal.find_by_publisher(possible_publisher) # exact match
        possible_owners = extract_owners(journals)
        corrected_publisher = record_ownership(possible_owners, id, original_publisher, original_filename, correction, record)
    
    # if we didn't find a corrected publisher yet, let's try searching on the original
    # publisher to see if we can get a result
    if corrected_publisher is None:
        journals = models.Journal.find_by_publisher(original_publisher) # exact match
        possible_owners = extract_owners(journals)
        corrected_publisher = record_ownership(possible_owners, id, original_publisher, original_filename, correction, record)
        
    # now try a more fuzzy match on both of the above
    if corrected_publisher is None and possible_publisher is not None:
        journals = models.Journal.find_by_publisher(possible_publisher, exact=False)
        possible_owners = extract_owners(journals)
        corrected_publisher = record_ownership(possible_owners, id, original_publisher, original_filename, correction, record)
    
    if corrected_publisher is None:
        journals = models.Journal.find_by_publisher(original_publisher, exact=False)
        possible_owners = extract_owners(journals)
        corrected_publisher = record_ownership(possible_owners, id, original_publisher, original_filename, correction, record)
    
    # lets try the publisher name against the journal title
    if corrected_publisher is None:
        journals = models.Journal.find_by_title(possible_publisher) # exact match
        possible_owners = extract_owners(journals)
        corrected_publisher = record_ownership(possible_owners, id, original_publisher, original_filename, correction, record)
    
    if corrected_publisher is None:
        journals = models.Journal.find_by_title(original_publisher) # exact match
        possible_owners = extract_owners(journals)
        corrected_publisher = record_ownership(possible_owners, id, original_publisher, original_filename, correction, record)
    
    if corrected_publisher is None:
        # we have failed to make a correction
        record[5] = "x"
        failed_writer.writerow([id, original_publisher, original_filename, correction])
    
    summary_writer.writerow(record)



















