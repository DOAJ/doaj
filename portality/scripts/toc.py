from portality import models
import os, json, argparse
from copy import deepcopy

SKIPPED = 1
PROCESSED = 2


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

def _get_omitted(existing, planned):
    return [e for e in existing if e not in planned]

def generate_toc(journal, verbose=False):
    issns = journal.known_issns()
    if verbose:
        print "Generating ToC for journal", journal.id, "with ISSNs", issns

    # get the volumes we are going to create, the volumes that already exist, and therefore
    # the list of existing toc volumes which are no longer needed
    known_volumes = models.Article.list_volumes(issns)
    toc_volumes = models.JournalVolumeToC.list_volumes(journal.id)
    unneeded_volumes = _get_omitted(toc_volumes, known_volumes)

    # for any unneeded volumes, delete them
    for v in unneeded_volumes:
        if verbose:
            print "...Deleting unwanted volume " + unicode(v).encode("utf-8", "replace")
        models.JournalVolumeToC.delete_by_volume(journal.id, v)

    if len(known_volumes) == 0:
        return SKIPPED, 0

    for kv in known_volumes:
        if verbose:
            print "...Generating Volume ToC for", unicode(kv).encode("utf-8", "replace")

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
                if verbose:
                    print "......Generating Issue ToC for number", unicode(num).encode("utf-8", "replace")#, "(year:", bj.year, "month:", bj.month, ")"
                table.add_issue(iss)

            # iss is now bound to the toc, so we can update it without
            # adding it to the table again
            iss.add_article(minimise_article(article))

        # figure out if this replaces an existing record
        existing_id = models.JournalVolumeToC.get_id(journal.id, kv)
        if existing_id is not None:
            if verbose:
                print "......Replacing existing ToC at", existing_id
            table.set_id(existing_id)

        table.save()

    return PROCESSED, len(known_volumes)

def generate_tocs(verbose=False):
    skipped = 0
    js = 0
    volumes = 0

    journals = models.Journal.iterall(page_size=1000)
    for journal in journals:
        result, value = generate_toc(journal, verbose)
        if result == SKIPPED:
            skipped += 1
            continue
        js += 1
        volumes += value

    print "Skipped", skipped, "journals. Created ToCs for", js, "journals.  A total of", volumes, "volumes"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-j", "--journal", help="journal id to generate ToC for")
    args = parser.parse_args()

    if not args.journal:
        print "Generating all ToCs"
        generate_tocs(verbose=True)
    else:
        print "Generating ToC for " + args.journal
        journal = models.Journal.pull(args.journal)
        if journal is not None:
            generate_toc(journal, verbose=True)
        else:
            print "Unable to find journal with that ID"
            
            
        
        







    
