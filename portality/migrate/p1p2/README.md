# Phase 1 to Phase 2 Migration Scripts

This directory contains the scripts that need to be run in order to migrate from Phase 1 of DOAJ to Phase 2 of DOAJ

They should be run individually in the following order:


1. userroles.py - adds the "publisher" role to user accounts where appropriate
2. journalowners.py - adds the "owner" field to the journals for the relevant user accounts
3. uploadedxml.py - migrates all the new articles from uploaded files into the database.  You will need to modify the file to point to the directory of the XML files, and the script itself could take upwards of 30 minutes to run.
4. flushuploads.py - remove all the old uploaded file records, and set the index up for its new usage


The following files are scripts generated in the development of the migrate scripts and should NOT be run as part of the migration:

1. uploadedfilenames.py - investigates uploaded files for the filenames and publishers to see if there are any obvious duplicates
