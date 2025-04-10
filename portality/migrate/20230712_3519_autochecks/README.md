Once this feature has been deployed to production, the following steps should be taken to ensure that the autochecks are run on all existing journals and applications:

```bash
python portality/scripts/autochecks.py -J -A
```

