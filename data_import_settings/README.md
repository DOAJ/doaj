Files in this directory can be used to import anonymised data in a variety of settings

usage: e.g. for test server, check storage is set to "portality.store.StoreS3" in `test.cfg`:
    
    #STORE_IMPL = "portality.store.StoreLocal"
    #STORE_LOCAL_EXPOSE = True
    STORE_IMPL = "portality.store.StoreS3"

Then run the import from project root:

    DOAJENV=test python portality/scripts/anon_import.py data_import_settings/test_server.json

And re-toggle the storage to StoreLocal


* article_sample.json ~~ArticleSample:Data~~
* dev_basics.json ~~DevBasics:Data~~
* test_server.json ~~TestServer:Data~~