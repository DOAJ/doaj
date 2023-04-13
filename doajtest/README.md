# Test suite

## Unit Tests

To run the unit tests, the recommended approach is:

```
cd doaj/doajtest/unit
pytest 2>&1 | tee test-output.txt
```

To analyse for slow tests, use

```
cd doaj/doajtest/unit
pytest --duration=0 2>&1 | tee test-output.txt
```

How to run parallelised unit test
-------------------------------------
```shell
$PATH_VENV_DOAJ/bin/pytest --color=yes --code-highlight=yes -n 8 --dist loadfile $DOAJ_CODE_HOME/doajtest/unit
```


Guide for writing parallelised unit test 
---------
Following are the guide to write unit test for parallelised:
* avoid use same folder path in difference test case
* if you need folder for test case, you can use `create_tmp_dir` to create new folder with random name.
* if test case required `STORE_IMPL`, `StoreLocal`, `STORE_TMP_IMPL`, you may need to use `StoreLocalPatcher`, it will create random path for `StoreLocal`

## Testbook

See: Testbook section from ../docs/README.md


## How to run testcase with docker
Developer can run selenium testcases with docker OR local chrome.

### [Option 1] prepare selenium with docker
```shell
docker-compose -f $DOAJ_CODE_HOME/docker/docker-compose.yml up
```

### [Option 2] prepare selenium with local chrome
* download chromedriver of you version from https://sites.google.com/chromium.org/driver/
* set environment variable in dev.cfg
```shell
SELENIUM_CHROME_DRIVER_PATH = '<YOUR_CHROMEDIRVER_PATH>/chromedriver'
```

### after your selenium setup is ready, run selenium testcases
* run your elastic search server
* run following command to run selenium testcases
```shell
$DOAJ_VENV/bin/pytest --color=yes --code-highlight=yes $DOAJ_CODE_HOME/doajtest/seleniumtest 
```
