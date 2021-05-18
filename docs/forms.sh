#!/usr/bin/env bash

# Set up the variables we need for the script
DOAJ_DOCS="docs/generated"
BRANCH=$(git branch 2>/dev/null | grep '^*' | colrm 1 2)
OUTDIR=$DOAJ_DOCS/$BRANCH/forms

# make sure that we have the documentation submodule up-to-date
git submodule update --init --recursive
(cd $DOAJ_DOCS && git checkout master && git pull origin master)

# ensure that the output directory exists
mkdir -p $OUTDIR

# Generete the CSVs describing each form context
python portality/forms/application_forms.py -t application -c public -o $OUTDIR/application.public.csv
python portality/forms/application_forms.py -t application -c update_request -o $OUTDIR/application.update_request.csv
python portality/forms/application_forms.py -t application -c associate_editor -o $OUTDIR/application.associate_editor.csv
python portality/forms/application_forms.py -t application -c editor -o $OUTDIR/application.editor.csv
python portality/forms/application_forms.py -t application -c admin -o $OUTDIR/application.admin.csv

python portality/forms/application_forms.py -t journal -c readonly -o $OUTDIR/journal.readonly.csv
python portality/forms/application_forms.py -t journal -c associate_editor -o $OUTDIR/journal.associate_editor.csv
python portality/forms/application_forms.py -t journal -c editor -o $OUTDIR/journal.editor.csv
python portality/forms/application_forms.py -t journal -c admin -o $OUTDIR/journal.admin.csv
python portality/forms/application_forms.py -t journal -c bulk_edit -o $OUTDIR/journal.bulk_edit.csv