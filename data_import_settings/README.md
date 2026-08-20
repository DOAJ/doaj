Files in this directory can be used to import anonymised data in a variety of settings

usage: e.g. for test server, run the import from project root:

    DOAJENV=test python portality/scripts/anon_import.py data_import_settings/test_server.json

Note, the default data source is S3 so it will automatically set `'STORE_IMPL' = "portality.store.StoreS3"`
for you, then return it to its previous value.

If you wish to perform an anonymous import from a local export, use the arg:

    DOAJENV=dev python portality/scripts/anon_import.py --storeimpl local data_import_settings/dev_basics.json

The script can also download the test users from Google Sheets if the config value `TEST_USERS_CSV_DL_PATH`
is correctly supplied.

**UPDATE 2026-07-07** - Significantly reduced the number of articles imported in test servers by default,
edit `data_import_settings/test_server.json` with limit `-1` and re-run import to get them all.

<!-- ~~AnonExport:Feature~~ -->

* article_sample.json <!-- ~~->ArticleSample:Data~~ -->
* dev_basics.json <!-- ~~->DevBasics:Data~~ -->
* test_server.json <!-- ~~->TestServer:Data~~ -->