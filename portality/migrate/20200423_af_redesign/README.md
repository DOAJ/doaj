# Migration for new data models underlying application form

## Before migration

DOAJ needs to be set to `Read-Only Mode` for the duration of the migration

## The migration

Because this migration touches the actual storage mechanism itself,
we can't use the usual upgrade script, which assumes that the storage layer
behaves in a certain way.

So in this directory, just run

    python migrate.py

## Cleanup

Once the migration has successfully run, and you have confirmed that everything
is working, then you can delete the old.

NOTE that we should keep the `suggestion` and `journal` types from the old
index around, so don't delete the whole index just now.

    curl -X DELETE [es host]/doaj