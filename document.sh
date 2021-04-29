#!/usr/bin/env bash
# In order to run this you need to have epydoc (http://epydoc.sourceforge.net/) installed, which can be done
# on Ubuntu with
#
# sudo apt-get install python-epydoc

# rm docs/code/*
# epydoc --html -o docs/code/ --name "DOAJ" --url https://github.com/DOAJ/doaj --graph all --inheritance grouped --docformat restructuredtext portality

# Generate the model documentation in markdown
python portality/lib/seamlessdoc.py -k portality.models.Journal -o docs/system/data_models/Journal.md -f docs/system/field_descriptions.txt
python portality/lib/seamlessdoc.py -k portality.models.Application -o docs/system/data_models/Application.md -f docs/system/field_descriptions.txt
python portality/lib/modeldoc.py -k portality.api.v2.data_objects.article.IncomingArticleDO -o docs/system/data_models/IncomingAPIArticle.md -f docs/system/IncomingAPIArticleFieldDescriptions.txt
python portality/lib/seamlessdoc.py -k portality.api.v2.data_objects.application.IncomingApplication -o docs/system/data_models/IncomingAPIApplication.md -f docs/system/IncomingAPIApplicationFieldDescriptions.txt
python portality/lib/seamlessdoc.py -k portality.api.v2.data_objects.journal.OutgoingJournal -o docs/system/data_models/OutgoingAPIJournal.md -f docs/system/OutgoingAPIJournalFieldDescriptions.txt

# Generete the CSVs describing each form context
python portality/forms/application_forms.py -t application -c public -o docs/system/forms/application.public.csv
python portality/forms/application_forms.py -t application -c update_request -o docs/system/forms/application.update_request.csv
python portality/forms/application_forms.py -t application -c associate_editor -o docs/system/forms/application.associate_editor.csv
python portality/forms/application_forms.py -t application -c editor -o docs/system/forms/application.editor.csv
python portality/forms/application_forms.py -t application -c admin -o docs/system/forms/application.admin.csv

python portality/forms/application_forms.py -t journal -c readonly -o docs/system/forms/journal.readonly.csv
python portality/forms/application_forms.py -t journal -c associate_editor -o docs/system/forms/journal.associate_editor.csv
python portality/forms/application_forms.py -t journal -c editor -o docs/system/forms/journal.editor.csv
python portality/forms/application_forms.py -t journal -c admin -o docs/system/forms/journal.admin.csv
python portality/forms/application_forms.py -t journal -c bulk_edit -o docs/system/forms/journal.bulk_edit.csv