import csv, re
from portality import models

analysis = "/home/richard/Dropbox/Documents/DOAJ/orphan_analysis.csv"
corrections = "/home/richard/Dropbox/Documents/DOAJ/corrections.csv"
ambiguous = "/home/richard/Dropbox/Documents/DOAJ/ambiguous.csv"
failed = "/home/richard/Dropbox/Documents/DOAJ/failed.csv"

reader = csv.reader(open(analysis))
correction_writer = csv.writer(open(corrections, "wb"))
correction_writer.writerow(["Upload ID", "Original Publisher", "Original Filename", "Correction Note", "Corrected Publisher"])
ambiguous_writer = csv.writer(open(ambiguous, "wb"))
ambiguous_writer.writerow(["Upload ID", "Original Publisher", "Original Filename", "Correction Note", "Possible Publishers"])
failed_writer = csv.writer(open(failed, "wb"))
failed_writer.writerow(["Upload ID", "Original Publisher", "Original Filename", "Correction Note"])

ISSN_REGEX = re.compile(r'^\d{4}-\d{3}(\d|X|x){1}$')

def extract_owners(journals, id, original_publisher, original_filename, correction):
    corrected_publisher = None
    owners = [j.owner for j in journals if j.owner is not None]
    owners = list(set(owners))
    if len(owners) > 0:
        if len(owners) == 1:
            corrected_publisher = owners[0]
            correction_writer.writerow([id, original_publisher, original_filename, correction, corrected_publisher])
            return corrected_publisher
        else:
            ambiguous_writer.writerow([id, original_publisher, original_filename, correction, ",".join(owners)])
    return corrected_publisher

first = True
for row in reader:
    if first:
        first = False
        continue
    
    xml_filename = row[0]
    original_publisher = row[1]
    correction = row[2]
    original_filename = row[3]
    
    corrected_publisher = None
    id = xml_filename.split(".")[0]
    
    # corrections could be issns, possibly comma separated
    possible_issns = [c.strip() for c in correction.split(",") if ISSN_REGEX.match(c.strip())]
    
    # or could be the name of a publisher, or some other note
    possible_publisher = None
    if len(possible_issns) == 0:
        possible_publisher = correction if correction is not None and correction != "" else None
    
    # try to locate a journal for each of the possible issns until we find one
    for issn in possible_issns:
        journals = models.Journal.find_by_issn(issn)
        corrected_publisher = extract_owners(journals, id, original_publisher, original_filename, correction)
        # NOTE: if there is more than one ISSN, then this could happen multiple times for the same upload
        # or even be ambiguous for one ISSN and corrected for another
    
    # if we didn't find a corrected publisher but we do have a possible publisher
    # take a look for a user account
    if corrected_publisher is None and possible_publisher is not None:
        journals = models.Journal.find_by_publisher(possible_publisher) # exact match
        corrected_publisher = extract_owners(journals, id, original_publisher, original_filename, correction)
    
    # if we didn't find a corrected publisher yet, let's try searching on the original
    # publisher to see if we can get a result
    if corrected_publisher is None:
        journals = models.Journal.find_by_publisher(original_publisher) # exact match
        corrected_publisher = extract_owners(journals, id, original_publisher, original_filename, correction)
    
    # now try a more fuzzy match on both of the above
    if corrected_publisher is None and possible_publisher is not None:
        journals = models.Journal.find_by_publisher(possible_publisher, exact=False)
        corrected_publisher = extract_owners(journals, id, original_publisher, original_filename, correction)
    
    if corrected_publisher is None:
        journals = models.Journal.find_by_publisher(original_publisher, exact=False)
        corrected_publisher = extract_owners(journals, id, original_publisher, original_filename, correction)
    
    if corrected_publisher is None:
        # we have failed to make a correction
        failed_writer.writerow([id, original_publisher, original_filename, correction])




















