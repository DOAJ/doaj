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