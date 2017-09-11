"""
This script will run through the entire catalogue, detecting duplicates
of articles and removing them. It could take a long time and you should
take great care running it - at minimum double check there is a recent
backup available, there should always be one anyway.
"""

"""
New functionality for issue 1296:
* For each article does a global check to see if there are any other articles which are "duplicate"
* Outputs each "set" of duplicate articles, along with the criteria for which they were determined duplicate
* Further identifies articles which are duplicate within a single user's account
* Identifies articles which appear in more than one "set" - that is, they may be duplicate with one set of articles by DOI, and duplicate with a different set by URL, etc
"""

from portality.models import Article
from portality.article import XWalk
from portality.core import app
from datetime import datetime
import time
import esprit


def duplicates_per_article(connection, delete, snapshot):
    """Scroll through all articles, finding (and deleting if set) duplicates for each."""
    dupcount = 0
    delcount = 0

    scroll_query = {                                                                      # scroll from newest to oldest
        "query": {"match_all": {}},
        "sort": [{"last_updated": {"order": "desc"}}]
    }

    for a in esprit.tasks.scroll(connection, 'article', q=scroll_query):
        article = Article(_source=a)
        duplicates = XWalk.discover_duplicates(article)
        if duplicates:
            dupcount += 1
            doi_dups = [d.id for d in duplicates.get('doi', [])]
            fulltext_dups = [d.id for d in duplicates.get('fulltext', [])]
            doi_dups.sort(), fulltext_dups.sort()                            # Sort so we can visually compare the lists
            print "\n{0}".format(article.id)
            if doi_dups:
                print "\t{0} DOI duplicates: {1}".format(len(doi_dups), ", ".join(doi_dups))
            if fulltext_dups:
                print "\t{0} fulltext duplicates: {1}".format(len(fulltext_dups), ", ".join(fulltext_dups))

            if delete:
                for dup in set(doi_dups + fulltext_dups):
                    if snapshot:
                        dup.snapshot()
                    dup.delete()
                    delcount += 1
            else:
                delcount += len(set(doi_dups + fulltext_dups))
    return dupcount, delcount


if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print "System is in READ-ONLY mode, script cannot run"
        exit()

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-g", "--ghost", help="specify if you want the articles being deleted not to be snapshot.", action="store_true")
    parser.add_argument("-d", "--delete", help="delete articles detected as duplicates. Unspecified, this script returns the report only.", action="store_true")
    parser.add_argument("-y", "--yes", help="are you running this script with output redirection e.g. DOAJENV=production python portality/scripts/article_duplicates_report_remove.py >> ~/dedupe_`date +\%%F_\%%H\%%M\%%S`.log 2>&1 ? You really should.", action="store_true")

    args = parser.parse_args()

    if not args.yes:
        raise Exception('Please run this script with output redirection, see --help if needed, \
        and also confirm you are running it with output redirection by passing -y on run.')

    snapshot = not args.ghost
    snapshot_report = "with snapshotting" if snapshot else "without snapshotting"

    start = datetime.now()

    if args.delete:
        print 'Starting {0} {snapshot} in 5 seconds, Ctrl+C to exit.'.format(start.isoformat(), snapshot=snapshot_report)
        time.sleep(5)
    else:
        print 'Starting {0} report-only.'.format(start.isoformat())

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])
    dupcount, delcount = duplicates_per_article(conn, args.delete, snapshot)

    end = datetime.now()
    length = end - start
    if args.delete:
        print "Ended {0}. {1} articles duplicated, {2} duplicates deleted. Took {3}.".format(end.isoformat(), dupcount, delcount, str(length))
    else:
        print "Ended {0}. {1} articles duplicated, {2} would be deleted. Took {3}.".format(end.isoformat(), dupcount, delcount, str(length))
