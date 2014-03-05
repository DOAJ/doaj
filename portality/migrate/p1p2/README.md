# Phase 1 to Phase 2 Migration Scripts

This directory contains the scripts that need to be run in order to migrate from Phase 1 of DOAJ to Phase 2 of DOAJ

They should be run individually in the following order:


1. userroles.py - adds the "publisher" role to user accounts where appropriate.  Should be run a couple of times, since for some reason it doesn't always get everyone.  Weird.
2. journalowners.py - adds the "owner" field to the journals for the relevant user accounts.  As with (1) needs to be run a couple of times.  Debug if time permits.
3. flushuploads.py - remove all the old uploaded file records in the index, and set it up for its new usage
4. uploadcorrections.py - builds the corrections table for the next script (uploadedxml.py).  You will need to modify the file to point to the relevant file-paths
5. uploadedxml.py - migrates all the new articles from uploaded files into the database.  You will need to modify the file to point to the directory of the XML files, and the script itself could take upwards of 10 minutes to run. 
6. Do this yourself: delete all of the files from the /upload directory


The following files are scripts generated in the development of the migrate scripts and should NOT be run as part of the migration:

1. uploadedfilenames.py - investigates uploaded files for the filenames and publishers to see if there are any obvious duplicates

The following files are supporting information:

1. orphan_analysis.csv - source data for uploadcorrections.py
