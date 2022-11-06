#!/usr/bin/env bash

# ~~Forms:Script->ApplicationForms:Feature~~

DOAJ_DOCS="../../doaj-docs"
BASE_DIR=$(dirname $(cd $(dirname "${BASH_SOURCE[0]}") && pwd))

while getopts 'd:' OPTION; do
  case "$OPTION" in
    d)
      DOAJ_DOCS="$OPTARG"
      ;;
  esac
done

echo "Generating form documentation CSVs"

# Set up the variables we need for the script
BRANCH=$(git branch 2>/dev/null | grep '^*' | colrm 1 2)
OUTDIR=$DOAJ_DOCS/$BRANCH/forms

# make sure that we have the documentation up-to-date
(cd $DOAJ_DOCS && git checkout master && git pull origin master)

# ensure that the output directory exists
mkdir -p $OUTDIR

# Generete the CSVs describing each form context
python $BASE_DIR/portality/forms/application_forms.py -t application -c public -o $OUTDIR/application.public.csv
python $BASE_DIR/portality/forms/application_forms.py -t application -c update_request -o $OUTDIR/application.update_request.csv
python $BASE_DIR/portality/forms/application_forms.py -t application -c associate_editor -o $OUTDIR/application.associate_editor.csv
python $BASE_DIR/portality/forms/application_forms.py -t application -c editor -o $OUTDIR/application.editor.csv
python $BASE_DIR/portality/forms/application_forms.py -t application -c admin -o $OUTDIR/application.admin.csv

python $BASE_DIR/portality/forms/application_forms.py -t journal -c readonly -o $OUTDIR/journal.readonly.csv
python $BASE_DIR/portality/forms/application_forms.py -t journal -c associate_editor -o $OUTDIR/journal.associate_editor.csv
python $BASE_DIR/portality/forms/application_forms.py -t journal -c editor -o $OUTDIR/journal.editor.csv
python $BASE_DIR/portality/forms/application_forms.py -t journal -c admin -o $OUTDIR/journal.admin.csv
python $BASE_DIR/portality/forms/application_forms.py -t journal -c bulk_edit -o $OUTDIR/journal.bulk_edit.csv