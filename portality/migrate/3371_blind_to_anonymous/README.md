# 20 03 2023; Issue 3371 - Remove Ableist Terms 

This migration changes the ableist terms present in our models

This migration changes all occurance of "Blind peer review" and "Double blind peer review" values of editorial process 
field and changes it into "Anonymous peer review" and "Double anonymous peer review" accordingly 


## Execution

Run the migration with

    python portality/upgrade.py -u portality/migrate/3371_blind_to_anonymous/migrate.json