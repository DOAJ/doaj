# Open References on Articles

https://github.com/DOAJ/doajPM/issues/3985

Articles gain a new optional field `bibjson.reference` (a list of strings).

# Issue 3985

No data migration is required but mapping update is needed.

This must be run before publishers start depositing articles with references

Update the index mappings

   ```bash
   python portality/migrate/3985_article_references/update_mappings.py
   ```
