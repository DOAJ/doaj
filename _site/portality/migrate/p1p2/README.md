# Phase 1 to Phase 2 Migration Scripts

This directory contains the scripts that need to be run in order to migrate from Phase 1 of DOAJ to Phase 2 of DOAJ

They should be run individually in the following order:


1. userroles.py - adds the "publisher" role to user accounts where appropriate.  Should be run a couple of times, since for some reason it doesn't always get everyone.  Weird.
2. journalowners.py - adds the "owner" field to the journals for the relevant user accounts.  As with (1) needs to be run a couple of times.  Debug if time permits.
3. country_cleanup.py - data clean-up of journal country data. Run once, check the country facet on /search and proceed. Produces country_cleanup.csv, a list of old and new country values.

    Takes current countries (e.g. "Iran") and matches them to their ISO codes (e.g. "IR") and regenerates the index portion of each journal to contain the ISO name ("Iran, Islamic Republic of").
    This script can also be run with the --dry-run flag. It will produce country_cleanup.csv without saving to index.
    This script can also be run with the -t flag after it has been run live or with --dry-run. -t will read the CSV and output a list of countries which changed, for review.

4. /scripts/journalinfo.py - this script is in the standard doaj scripts folder.  Running it will correct any issues with the in_doaj flag on articles.  Check the size of the article index before and after to see the effect it has on the amount of content.
5. flushuploads.py - remove all the old uploaded file records in the index, and set it up for its new usage
6. uploadcorrections.py - builds the corrections table for the next script (uploadedxml.py).  You will need to modify the file to point to the relevant file-paths
7. uploadedxml.py - migrates all the new articles from uploaded files into the database.  You will need to modify the file to point to the directory of the XML files, and the script itself could take upwards of 10 minutes to run. 
8. Do this yourself: move the upload directory out of the way and make a new empty one (we should keep the old upload directory in case we need the content again)
9. /scripts/journalcsv.py - generate the initial csv file
10. Set up the cron jobs for ingesting articles
11. Set up cron job to generate CSV.

==============================

12. journalrestructure.py - data model restructuring on journal objects: remove author_pays/author_pays_url and DOAJ subject classifications
13. suggestionrestructure.py - data model restructuring on suggestion objects: remove author_pays/author_pays_url
14. loadlcc.py - load the LCC subject codes into the index.
15. Run journal info again ...


The following files are scripts generated in the development of the migrate scripts and should NOT be run as part of the migration:

1. uploadedfilenames.py - investigates uploaded files for the filenames and publishers to see if there are any obvious duplicates

The following files are supporting information:

1. orphan_analysis.csv - source data for uploadcorrections.py
