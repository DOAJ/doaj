# Migration for new data models underlying application form

## Before migration

DOAJ needs to be set to `Read-Only Mode` for the duration of the migration

## The migration

Because this migration touches the actual storage mechanism itself,
we can't use the usual upgrade script, which assumes that the storage layer
behaves in a certain way.

So in this directory, just run

    python migrate.py

Finally, run a basic migration on the articles:

```
python portality/upgrade.py -u portality/migrate/20200423_af_redesign/patch_20200919_migrate.json
```


## Cleanup

Once the migration has successfully run, and you have confirmed that everything
is working, then you can delete the old.

NOTE that we should keep the `suggestion` and `journal` types from the old
index around, so don't delete the whole index just now.

    curl -X DELETE [es host]/doaj
    
    
# Patch migrations

These are migrations that you DO NOT need to run during the deployment to production
but which you will need to run if you ran the first version of the migration and
need to update your system to fix bugs without doing a full re-migration

## License display fix

Fixes an issue with the `license_display` field capitalisation

Run

```
python license_display_fix_for_test.py
```

## Enhance Schema Codes for Subject Browse

Adds additional subject information to the `index` portion of the Journal and Application models
for use by the new subject browser

First update the mapping for the new field:

```
curl -XPUT 'http://localhost:9200/doaj-journal/_mapping/doc' -d '
{
	"doc" : {
		"properties" : {
			"index" : {
				"properties" : {
					"schema_codes_tree": {
						"type": "string",
						"fields": {
							"exact": {
								"type": "string",
								"index": "not_analyzed",
								"store": true
							}
						}
					}
				}
			}
		}
	}
}
'
```

Then run the trivial migration:

```
python portality/upgrade.py -u portality/migrate/20200423_af_redesign/patch_20200904_migrate.json
```

## Set 'has preservation' to False when there is a URL but no services

Sets `has_preservation=False` to records when there is a preservation url, but no preservation service selected

Run

```
python has_preservation_fix_for_test.py
```