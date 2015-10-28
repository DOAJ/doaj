"""
This script will run through the entire catalogue, detecting duplicates
of articles and removing them. It could take a long time and you should
take great care running it - at minimum double check there is a recent
backup available, there should always be one anyway.
"""

from portality import models
from portality.article import XWalk
import json
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

    args = parser.parse_args()

    snapshot = not args.ghost
    snapshot_report = "with snapshotting" if snapshot else "without snapshotting"

    start = datetime.now()
    count = 0
    print 'Starting {0} {snapshot} in 5 seconds, Ctrl+C to exit.'.format(start.isoformat(), snapshot=snapshot_report)
    time.sleep(5)

    article_iterator = models.Article.iterall(page_size=5000)  # FIXME this doesn't do a scroll search, just normal queries, so we're deleting from a list we're modifying! Currently either because of this or what get_duplicate does, this deletes the original article AND the duplicates when an article with duplicates is found.
    for a in article_iterator:
        duplicates = XWalk().get_duplicate(a, all_duplicates=True)
        for d in duplicates:
            if snapshot:
                d.snapshot()
            d.delete()
            count += 1

    end = datetime.now()
    length = end - start
    print "Ended {0}. {1} articles deleted. Took {2}.".format(end.isoformat(), count, str(length))