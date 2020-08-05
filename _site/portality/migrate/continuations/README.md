# Continuations

This migrate script removes the existing "history" portion of a record in the index, and turns each record in
that list into a first-class journal object

    python portality/upgrade.py -u portality/migrate/continuations/continuations.json -v
    
    
You will also need to update the ES mappings so that the new search interface changes work:

    python portality/migrate/continuations/mappings.py

    
Once the migration here has been completed, it is necessary to run the article_cleanup_sync script to ensure that the ToCs are correct from the start

    python portality/scripts/article_cleanup_sync.py -wp
    
