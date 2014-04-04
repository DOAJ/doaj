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
        print "Generating ToC for journal", journal.id, "with ISSNs", issns#, "and volumes", known_volumes
        
        if len(known_volumes) == 0:
            skipped += 1
            continue
        js += 1
        
        for kv in known_volumes:
            print "...Generating Volume ToC for", unicode(kv).encode("utf-8", "replace")
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
                    print "......Generating Issue ToC for number", unicode(num).encode("utf-8", "replace")#, "(year:", bj.year, "month:", bj.month, ")"
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
            
            
        
        







    
