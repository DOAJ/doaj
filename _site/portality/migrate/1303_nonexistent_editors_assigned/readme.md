#### ```nonexistent_editors_assigned.py```
*E.T. May 2017*

Migration scripts to fix issue 1303.

Run (prepend with `DOAJENV=dev_or_test_or_production`)

1. ```stdbuf -o0 -e0 python portality/migrate/1303_nonexistent_editors_assigned/nonexistent_editors_assigned.py > ~/nonexistent_editors_assigned_`date +%F-%H-%M-%S`.log 2>&1```
