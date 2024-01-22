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

### How to run parallelised unit test

```shell
$PATH_VENV_DOAJ/bin/pytest --color=yes --code-highlight=yes -n 8 --dist loadfile $DOAJ_CODE_HOME/doajtest/unit
```

### Guide for writing parallelised unit test

Following are the guide to write unit test for parallelised:

* avoid use same folder path in difference test case
* if you need folder for test case, you can use `create_tmp_dir` to create new folder with random name.
* if test case required `STORE_IMPL`, `StoreLocal`, `STORE_TMP_IMPL`, you may need to use `StoreLocalPatcher`, it will
  create random path for `StoreLocal`

----------------------------------------

## Testbook

See: Testbook section from ../docs/README.md


----------------------------------------

## How to run testcase with docker

Developer can run selenium testcases with docker OR local chrome.

### [Option 1] prepare selenium with docker (remote selenium server)

* run docker-compose to start selenium server
```shell
docker-compose -f $DOAJ_CODE_HOME/docker/docker-compose.yml up
```
* you can check selenium server is ready, by open http://localhost:4444/wd/hub on your browser
* set environment variable SELENIUM_REMOTE_URL to docker url in dev.cfg, for
  example `SELENIUM_REMOTE_URL='http://localhost:4444/wd/hub'`

### [Option 2] prepare selenium with local chrome

* set environment variable SELENIUM_REMOTE_URL to empty, for example `SELENIUM_REMOTE_URL=''`

### update ip of doaj server for test
* selenium testcases will run doaj server for test. 
* if you use docker selenium browser container, ip should be a ip of docker network interface such as 172.17.0.1
* otherwise, localhost should be fine
```
SELENIUM_DOAJ_HOST = '172.17.0.1'
```

* you can found ip of docker network interface by following command

```shell
ip a | grep docker -A 2
# or
docker network inspect bridge
```

### after your selenium setup is ready, run selenium testcases

* run your elastic search server
* run following command to run selenium testcases

```shell
$DOAJ_VENV/bin/pytest --color=yes --code-highlight=yes $DOAJ_CODE_HOME/doajtest/seleniumtest 
```

