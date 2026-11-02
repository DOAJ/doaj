# Searchable rich-text titles and abstracts

https://github.com/DOAJ/doajPM/issues/2861

Articles can store inline formatting tags (`<sub>`, `<i>`, ...) in `bibjson.title` / `bibjson.abstract`,
which makes terms like `TiOx` unsearchable. Articles now also index tag-free copies in `index.title` and
`index.abstract`, and the Title / Abstract field searches use them.

This migration will:

* Add the `index.title` and `index.abstract` mappings to the existing article index (no reindex, no downtime)
* Re-save the articles whose title or abstract contains one of the formatting tags, so their index fields
  are regenerated (expect roughly 6% of articles; ~1 minute per 6k articles)

Run in each environment, in this order:

1. Deploy the new code, but **do not restart the app or huey yet**. Then update the index mappings:

   ```bash
   python portality/migrate/2861_rich_text_index/update_mappings.py
   ```

   Expected output: `Updating mapping via alias <prefix>article for article; status: {'acknowledged': True}`

   This must run before the new code saves any article. Otherwise Elasticsearch auto-maps `index.title` with
   the wrong analyzer and this step fails with a mapping conflict (fixing that would need a full reindex).

2. Restart the app and huey.

3. Migrate the data:

   ```bash
   python portality/upgrade.py -u portality/migrate/2861_rich_text_index/migrate.json
   ```

   Expected output ends with `Finished <timestamp>.` It is safe to re-run.

## Check

```bash
curl -s "<es-host>/<prefix>article/_mapping/field/index.title,index.abstract"
```

Both fields should show `"analyzer": "ascii_folded"`. In the public article search, choosing "Title" and
searching for `TiOx` should find articles whose title contains `TiO<sub>x</sub>`.

## Notes

* Re-saved articles get a new `last_updated` date.
* Rollback: reverting the code is safe; the extra mapping fields and index values are simply unused.
