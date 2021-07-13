#!/usr/bin/env bash
# Before running this file you must auto-generate the form documentation using `forms.sh`

# ~~DataModels:Script->Forms:Script~~
# ~~->FieldDescriptions:Documentation~~
# ~~->Seamless:Technology~~
# ~~->DataObj:Technology~~
# ~~->Journal:Model~~
# ~~->Application:Model~~
# ~~->IncomingArticle:Model~~
# ~~->IncomingApplication:Model~~
# ~~->OutgoingJournal:Model~~


echo "Generating data model documentation"
# Set up the variables we need for the script
DOAJ_DOCS="docs/generated"
BRANCH=$(git branch 2>/dev/null | grep '^*' | colrm 1 2)
BRANCHDIR=$DOAJ_DOCS/$BRANCH
OUTDIR=$BRANCHDIR/data_models
FORMFILE=$BRANCHDIR/forms/application.public.csv

# make sure that we have the documentation submodule up-to-date
git submodule update --init --recursive
(cd $DOAJ_DOCS && git checkout master && git pull origin master)

# ensure that the output directory exists
mkdir -p $OUTDIR
mkdir -p $OUTDIR/descriptions

# generate the field description files from the forms
python portality/scripts/form_description_to_field_description.py -f $FORMFILE -o $OUTDIR/descriptions/public.application.txt

# Generate the model documentation in markdown
python portality/lib/seamlessdoc.py -k portality.models.Journal -o $OUTDIR/Journal.md \
        -f $OUTDIR/descriptions/public.application.txt \
        -f docs/data_models/field_descriptions.txt

python portality/lib/seamlessdoc.py -k portality.models.Application -o $OUTDIR/Application.md \
        -f $OUTDIR/descriptions/public.application.txt \
        -f docs/data_models/field_descriptions.txt

python portality/lib/modeldoc.py -k portality.api.v2.data_objects.article.IncomingArticleDO -o $OUTDIR/IncomingAPIArticle.md \
        -f docs/data_models/IncomingAPIArticleFieldDescriptions.txt

python portality/lib/seamlessdoc.py -k portality.api.v2.data_objects.application.IncomingApplication \
        -o $OUTDIR/IncomingAPIApplication.md \
        -f $OUTDIR/descriptions/public.application.txt \
        -f docs/data_models/IncomingAPIApplicationFieldDescriptions.txt

python portality/lib/seamlessdoc.py -k portality.api.v2.data_objects.journal.OutgoingJournal \
        -o $OUTDIR/OutgoingAPIJournal.md \
        -f $OUTDIR/descriptions/public.application.txt \
        -f docs/data_models/OutgoingAPIJournalFieldDescriptions.txt

