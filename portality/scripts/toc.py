from portality import models
import os, json
from copy import deepcopy

def minimise_article(full_article):
    # we want to keep the id and the bibjson
    id = full_article.id
    bibjson = deepcopy(full_article.bibjson())
    
    # remove the issns from the bibjson
    bibjson.remove_identifiers(idtype=bibjson.P_ISSN)
    bibjson.remove_identifiers(idtype=bibjson.E_ISSN)
    
    # remove all the journal metadata
    bibjson.remove_journal_metadata()
    
    # remove all the subject classifications
    bibjson.remove_subjects()
    
    # remove the year and the month (they are held elsewhere in this case)
    del bibjson.month
    del bibjson.year
    
    # create a minimised version of the article
    minimised = models.Article()
    minimised.set_id(id)
    minimised.set_bibjson(bibjson)
    
    return minimised
    

if __name__ == "__main__":
    skipped = 0
    js = 0
    volumes = 0
    
    journals = models.Journal.iterall(page_size=1000)
    for journal in journals:
        issns = journal.known_issns()
        known_volumes = models.Article.list_volumes(issns)
        print "Generating ToC for journal", journal.id, "with ISSNs", issns, "and volumes", known_volumes
        
        if len(known_volumes) == 0:
            skipped += 1
            continue
        js += 1
        
        for kv in known_volumes:
            print "...Generating Volume ToC for", kv
            volumes += 1
            articles = models.Article.get_by_volume(issns, kv)
            
            table = models.JournalVolumeToC()
            table.set_about(journal.id)
            table.set_issn(issns)
            table.set_volume(kv)
            
            for article in articles:
                bj = article.bibjson()
                
                # get the issue number, or "unknown" if there isn't one
                num = bj.number
                if num is None:
                    num = "unknown"
                
                # there may already be an issue for this number.  If not
                # make a new one and add it
                iss = table.get_issue(num)
                if iss is None:
                    iss = models.JournalIssueToC()
                    iss.number = num
                    if bj.year is not None:
                        iss.year = bj.year
                    if bj.month is not None:
                        iss.month = bj.month
                    print "......Generating Issue ToC for number", num, "(year:", bj.year, "month:", bj.month, ")"
                    table.add_issue(iss)
                
                # iss is now bound to the toc, so we can update it without
                # adding it to the table again
                iss.add_article(minimise_article(article))
            
            # figure out if this replaces an existing record
            existing_id = models.JournalVolumeToC.get_id(journal.id, kv)
            if existing_id is not None:
                print "......Replacing existing ToC at", existing_id
                table.set_id(existing_id)
            
            table.save()
    
    print "Skipped", skipped, "journals. Created ToCs for", js, "journals.  A total of", volumes, "volumes"
            
            
        
        
"""
volume_table = {}
year_table = {}
vol_num_table = {}
year_month_table = {}
year_to_vol = []
yearmonth_to_volnum = []
missing = {
    "totally" : [],
    "month" : [],
    "number" : []
}

for article in articles:
    tracked = False
    b = article.bibjson()
    vol = b.volume
    num = b.number
    year = b.year
    month = b.month
    
    # record the article against volume/issue
    if vol is not None:
        tracked = True
        
        # record the article against the volume, whether we have the number or not
        if vol not in volume_table:
            volume_table[vol] = []
        volume_table[vol].append(article.id)
        
        if num is not None: # we have the volume and the issue
            if vol not in vol_num_table:
                vol_num_table[vol] = {}
            if num not in vol_num_table[vol]:
                vol_num_table[vol][num] = []
            vol_num_table[vol][num].append(article.id)
        else:
            missing["number"].append(article.id)
        
    # record the article against year/month
    if year is not None:
        tracked = True
        # record the article against the year, whether we have the month or not
        if year not in year_table:
            year_table[year] = []
        year_table[year].append(article.id)
        
        if month is not None: # we have the year and the month
            if year not in year_month_table:
                year_month_table[year] = {}
            if month not in year_month_table[year]:
                year_month_table[year][month] = []
            year_month_table[year][month].append(article.id)
        else:
            missing["month"].append(article.id)
    
    # record year/month to vol/issue equivalences
    if vol is not None and year is not None:
        # record the year to vol relationship
        year_to_vol.append((year, vol))
        
        if num is not None and month is not None: # we have issue number and month
            yearmonth_to_volnum.append(((year, month), (vol, num)))
    
    if not tracked:
        missing["totally"].append(article.id)

# deduplicate the year/volume mappings
year_to_vol = list(set(year_to_vol))
yearmonth_to_volnum = list(set(yearmonth_to_volnum))

outdir = "/home/richard/tmp/doaj/toc"

with open(os.path.join(outdir, "volume.json"), "wb") as f:
    f.write(json.dumps(volume_table, sort_keys=True, indent=2))

with open(os.path.join(outdir, "year.json"), "wb") as f:
    f.write(json.dumps(year_table, sort_keys=True, indent=2))

with open(os.path.join(outdir, "vol_num.json"), "wb") as f:
    f.write(json.dumps(vol_num_table, sort_keys=True, indent=2))

with open(os.path.join(outdir, "year_month.json"), "wb") as f:
    f.write(json.dumps(year_month_table, sort_keys=True, indent=2))

with open(os.path.join(outdir, "year_to_vol.json"), "wb") as f:
    f.write(json.dumps(year_to_vol, sort_keys=True, indent=2))

with open(os.path.join(outdir, "yearmonth_to_volnum.json"), "wb") as f:
    f.write(json.dumps(yearmonth_to_volnum, sort_keys=True, indent=2))

with open(os.path.join(outdir, "missing.json"), "wb") as f:
    f.write(json.dumps(missing, sort_keys=True, indent=2))
"""























    
