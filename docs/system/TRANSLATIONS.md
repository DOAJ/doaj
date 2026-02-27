# Internationalization

Use the following process to internationalize the text. For example to add support for French language

## Coding

### Python files

Edit text in python files as mentioned below

```
from flask_babel import lazy_gettext
...
lazy_gettext("Does the journal adhere to DOAJ’s definition of open access?")
```

### Jinja2 templates

Edit text in .html files as mentioned below

```
{{ _("About the journal") }}
```

### Javascript

JS files can be translated by adding the appropriate translations to the `_i18n_translations.html`
template, and then using the translation function in the JS.

```javascript
doaj.i18n.init({
    "English Key": "{{ _('English Key') }}"
});
```

then

```javascript
let valInLang = doaj.i18n.get("English Key");
```


## Managing

### Generate message files 

cd to `portality` directory

```shell
bash scripts/locale_translation.sh
```

Select option 1 from the list

```
******************************
Please select an option:
1. Extract and update Messages
2. Show statistics
3. Compile messages
4. Exit
```

Select option 4 to exit the script

Messages files will be generated at the location `portality/ui/translations` directory.

If there are pre-existing translations, any changes to the messages will be marked as fuzzy in the messages.po file. This means that these messages need to be reviewed and updated by the translator.

### Generate CSV file for translation

Execute the following command to generate the CSV file
```
python po_csv_converter.py po2csv <po_file> <csv_file>
```

To generate the csv with only updated messages then execute the script with --fuzzy parameter
```
python po_csv_converter.py po2csv <po_file> <csv_file> --fuzzy
```

Example to generate CSV file for French messages
```
python scripts/po_csv_converter.py po2csv translations/fr/LC_MESSAGES/messages.po translations/messages_fr.csv
or the following for only updated messages
python scripts/po_csv_converter.py po2csv translations/fr/LC_MESSAGES/messages.po translations/messages_fr.csv -fuzzy 
```

### Sharing and translating

The CSV should be added as a new sheet to the master translations file here:

https://docs.google.com/spreadsheets/d/1bFlc8_KjBRED8LF-kL4NXZPCQk1L_Q-XM0470J_-b5Y/edit

This can then be shared with the translator to add the messages in the required language. 

### Applying the translations

Once the updated CSV file is available, update the messages.po file

```
python po_csv_converter.py csv2po <csv_file> <po_file>
```

Example to update messages.po file from CSV file
```
python scripts/po_csv_converter.py csv2po translations/messages_fr.csv translations/fr/LC_MESSAGES/messages.po
```

This script will also generate a file with name as translations/messages_fr_<date>.csv format. 
This file contains the messages that were not updated in the po file because of the reasons like broken html tags etc.
Review this file before moving to next step.

Once the messages.po file is updated, generate the messages.mo binary file

cd to `portality` directory

```shell
python scripts/locale_translation.sh
```

Select option 3 from the list

```
******************************
Please select an option:
1. Extract and update Messages
2. Show statistics
3. Compile messages
4. Exit
```

Select option 4 to exit the script
