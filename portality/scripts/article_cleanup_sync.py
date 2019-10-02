"""
For each article in the DOAJ index:
    * Checks that it has a corresponding journal, deletes it otherwise
    * Ensures that the article in_doaj status is the same as the journal's
    * Applies the journal's information to the article metadata as needed
"""
from datetime import datetime
from portality.core import app

from portality.tasks import article_cleanup_sync as asc
from portality.background import BackgroundApi


if __name__ == "__main__":
    start = datetime.now()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--write", action='store_true', default=False, help="when set, the script will write changes to the index")
    parser.add_argument("-p", "--prepall", action='store_true', default=False, help="prepare all articles, not just changed ones (i.e. update article's index)")
    args = parser.parse_args()

    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print ("System is in READ-ONLY mode, enforcing read-only for this script")
        args.write = False

    if args.prepall and not args.write:
        print ("Prep all must be used with the -w flag set too (why prep but not save?). Exiting.")
        exit(1)
    elif args.prepall:
        print ("Prep all arg set. 'unchanged' articles will also have their indexes refreshed.")

    job = asc.ArticleCleanupSyncBackgroundTask.prepare("testuser", prepall=args.prepall, write=args.write)
    task = asc.ArticleCleanupSyncBackgroundTask(job)
    BackgroundApi.execute(task)

    end = datetime.now()
    print (start, "-", end)

    for a in job.audit:
        print (a)
