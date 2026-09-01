# Premium

The following migration will:

* remove the journal CSV cache record 
* migrate the public data dump cache record to the new format

```
python portality/migrate/20250521_4008_premium/migrate.py
```

It does not migrate the Journal CSV, so as soon as possible the following script should also be run in production:

```
python portality/scripts/journalcsv.py
```

Once these scripts have been run, we will also want to upgrade all the users who will be given premium from the start. 
This can be done with:

```
python portality/scripts/apply_user_roles.py [csv of users and roles]
```