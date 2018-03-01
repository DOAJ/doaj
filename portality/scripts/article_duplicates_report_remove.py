"""
This script will run through the entire catalogue, detecting duplicates
of articles and removing them. It could take a long time and you should
take great care running it - at minimum double check there is a recent
backup available, there should always be one anyway.
"""

from portality.models import Article, Journal, Account
from portality.article import XWalk
from portality.core import app
from datetime import datetime
import time
import esprit


def duplicates_per_article(connection, delete, snapshot, owner=None, query_override=None):
    """Scroll through all articles, finding (and deleting if set) duplicates for each."""
    dupcount = 0
    deleted_ids = set()

    if query_override:
        scroll_query = query_override
    else:
        scroll_query = {                                                                  # scroll from newest to oldest
            "query": {"match_all": {}},
            "sort": [{"last_updated": {"order": "desc"}}]
        }

    for a in esprit.tasks.scroll(connection, 'article', q=scroll_query):
        article = Article(_source=a)

        if article.id in deleted_ids:                               # only delete its duplicates if it isn't a duplicate
            continue

        duplicates = XWalk.discover_duplicates(article, owner)
        if duplicates:
            doi_dups = [d.id for d in duplicates.get('doi', [])]
            fulltext_dups = [d.id for d in duplicates.get('fulltext', [])]
            fuzzy_dups = [d.id for d in duplicates.get('fuzzy', [])]
            doi_dups.sort(), fulltext_dups.sort(), fuzzy_dups.sort()         # Sort so we can visually compare the lists
            print "\n{0}".format(article.id)
            if doi_dups:
                print "\t{0} DOI duplicates: {1}".format(len(doi_dups), ", ".join(doi_dups))
            if fulltext_dups:
                print "\t{0} fulltext duplicates: {1}".format(len(fulltext_dups), ", ".join(fulltext_dups))
            if fuzzy_dups:
                print "\t{0} fuzzy duplicates: {1}".format(len(fuzzy_dups), ", ".join(fuzzy_dups))

            # Only consider duplicates that appear in at least 2 lists (we should be cautious with deletes) TODO: 3 - way comparison
            set_of_duplicates = set(doi_dups).intersection(set(fulltext_dups))
            dupcount += len(set_of_duplicates) + 1                     # The detected duplicates plus the article itself

            if set_of_duplicates:
                print "\t{0} in intersection: {1}".format(len(set_of_duplicates), ", ".join(set_of_duplicates))

            if delete:
                for dup in set_of_duplicates:
                    dup_art = article.pull(dup)
                    if dup_art is not None:
                        if snapshot:
                            dup_art.snapshot()
                        dup_art.delete()
                        deleted_ids.add(dup)
            else:
                deleted_ids = deleted_ids | set_of_duplicates

    return dupcount, len(deleted_ids)


def duplicates_per_account(connection, delete, snapshot):
    dupcount = 0
    delcount = 0

    for acc in esprit.tasks.scroll(connection, 'account'):
        account = Account(**acc)

        # Get all articles belonging to an account via ISSNs
        issns = Journal.issns_by_owner(account.id)
        if issns:
            print "Account {0}".format(account.id)

            # Term limit of ES is 1024 by default, split up the queries.
            for i in range(0, len(issns), 1000):
                scroll_query = {
                    "query": {
                        "filtered": {
                            "filter": {
                                "bool": {
                                    "must": [
                                        {"terms": {"index.issn.exact": issns[i:i+1000]}}
                                     ]
                                }
                            },
                            "query": {"match_all": {}}
                        }
                    },
                    "sort": [{"last_updated": {"order": "desc"}}]
                }
                acc_dupcount, acc_delcount = duplicates_per_article(connection,
                                                                    delete,
                                                                    snapshot,
                                                                    owner=account.id,
                                                                    query_override=scroll_query)
                dupcount += acc_dupcount
                delcount += acc_delcount

    return dupcount, delcount


if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print "System is in READ-ONLY mode, script cannot run"
        exit()

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-a", "--account", help="search for duplicates per account, rather than globally.", action="store_true")
    parser.add_argument("-g", "--ghost", help="specify if you want the articles being deleted not to be snapshot.", action="store_true")
    parser.add_argument("-d", "--delete", help="delete articles detected as duplicates. Unspecified, this script returns the report only.", action="store_true")
    parser.add_argument("-y", "--yes", help="are you running this script with output redirection e.g. DOAJENV=production python portality/scripts/article_duplicates_report_remove.py >> ~/dedupe_`date +\%%F_\%%H\%%M\%%S`.log 2>&1 ? You really should.", action="store_true")

    args = parser.parse_args()

    if not args.yes:
        raise Exception('Please run this script with output redirection, see --help if needed, and also confirm you are running it with output redirection by passing -y on run.')

    snapshot = not args.ghost
    snapshot_report = "with snapshotting" if snapshot else "without snapshotting"

    start = datetime.now()

    if args.delete:
        print 'Starting {0} {snapshot} in 5 seconds, Ctrl+C to exit.'.format(start.isoformat(), snapshot=snapshot_report)
        time.sleep(5)
    else:
        print 'Starting {0} report-only.'.format(start.isoformat())

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    if args.account:
        dupcount, delcount = duplicates_per_account(conn, args.delete, snapshot)
    else:
        dupcount, delcount = duplicates_per_article(conn, args.delete, snapshot)

    end = datetime.now()
    length = end - start
    if args.delete:
        print "Ended {0}. {1} articles duplicated, {2} duplicates deleted. Took {3}.".format(end.isoformat(), dupcount, delcount, str(length))
    else:
        print "Ended {0}. {1} articles duplicated, {2} duplicates would be deleted. Took {3}.".format(end.isoformat(), dupcount, delcount, str(length))
