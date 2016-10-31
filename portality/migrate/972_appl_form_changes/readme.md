#### ```appl_form_changes.py``` & ```missed_journals.py```
*E.T. Oct 2016*

Migration scripts to fix issue 972.

Run

1. ```stdbuf -o0 -e0 python portality/migrate/972_appl_form_changes/appl_form_changes.py > ~/appl_form_changes_`date +%F-%H-%M-%S`.log 2>&1```
2. ```stdbuf -o0 -e0 python portality/migrate/972_appl_form_changes/missed_journals.py > ~/appl_form_changes_missed_journals_`date +%F-%H-%M-%S`.log 2>&1 ```