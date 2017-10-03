"""
This script will run through the entire catalogue, detecting duplicates
of articles and removing them. It could take a long time and you should
take great care running it - at minimum double check there is a recent
backup available, there should always be one anyway.
"""

from portality import models
from portality.article import XWalk
from portality.core import app
from datetime import datetime
import time

if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print "System is in READ-ONLY mode, script cannot run"
        exit()

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-g", "--ghost", help="specify if you want the articles being deleted not to be snapshot", action="store_true")
    parser.add_argument("-y", "--yes", help="are you running this script with output redirection e.g. DOAJENV=production python portality/scripts/remove_duplicate_articles.py >> ~/dedupe_`date +\%%F_\%%H\%%M\%%S`.log 2>&1 ? You really should.", action="store_true")

    args = parser.parse_args()

    if not args.yes:
        raise Exception('Please run this script with output redirection, see --help if needed, and also confirm you are running it with output redirection by passing -y on run.')

    snapshot = not args.ghost
    snapshot_report = "with snapshotting" if snapshot else "without snapshotting"

    start = datetime.now()
    count = 0
    print 'Starting {0} {snapshot} in 5 seconds, Ctrl+C to exit.'.format(start.isoformat(), snapshot=snapshot_report)
    time.sleep(5)

    originals = []  # make sure we only delete FORWARD. So, if articles
    # A, B and C are duplicates, we stumble upon A first, and delete B and C.
    # We must then ensure we do not delete A if we chance upon B or C
    # (because they are still in Python memory even though they are not in ES).
    article_iterator = models.Article.iterall(page_size=5000)
    for a in article_iterator:
        originals.append(a.id)
        duplicates = XWalk().get_duplicate(a, all_duplicates=True)
        if duplicates:
            print '{0}:'.format(a.id),  # original: ...
            for d in duplicates:
                if not d.id in originals:
                    if snapshot:
                        d.snapshot()
                    d.delete()
                    count += 1
                    print '{0},'.format(d.id)  # ... duplicate_deleted1, duplicate_deleted2, etc.
                    time.sleep(1)
            print

    end = datetime.now()
    length = end - start
    print "Ended {0}. {1} articles deleted. Took {2}.".format(end.isoformat(), count, str(length))