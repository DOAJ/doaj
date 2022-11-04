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
