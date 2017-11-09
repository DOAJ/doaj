#### ```filename```
*S.E. 2017-11-07*

Fix for issue 1390 - incorrectly spelled subjects affecting discovery.
Refresh the subject name saved on journals, applications, article bibjson.

Run

    python portality/upgrade.py -u portality/migrate/1390_lcc_regen_subjects/regen_subjects.json
