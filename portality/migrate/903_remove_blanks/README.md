# Remove Blank 

remove blank from start or end of string in Journal and Application

### Run
```
python portality/upgrade.py -u portality/migrate/903_remove_blanks/migrate.json
```

### verify
```
python -m portality.scripts.blank_field_finder
```