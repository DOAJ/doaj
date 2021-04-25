#!/usr/bin/env bash
# In order to run this you need to have epydoc (http://epydoc.sourceforge.net/) installed, which can be done
# on Ubuntu with
#
# sudo apt-get install python-epydoc

# rm docs/code/*
# epydoc --html -o docs/code/ --name "DOAJ" --url https://github.com/DOAJ/doaj --graph all --inheritance grouped --docformat restructuredtext portality

DOAJ_DOCS="../doaj-docs"
BRANCH=$(git branch 2>/dev/null | grep '^*' | colrm 1 2)
OUTDIR=$DOAJ_DOCS/docs/$BRANCH/data_models
mkdir -p $OUTDIR

# Generate the model documentation in markdown
python portality/lib/seamlessdoc.py -k portality.models.Journal -o $OUTDIR/Journal.md -f docs/system/field_descriptions.txt
python portality/lib/seamlessdoc.py -k portality.models.Application -o $OUTDIR/Application.md -f docs/system/field_descriptions.txt
python portality/lib/modeldoc.py -k portality.api.v2.data_objects.article.IncomingArticleDO -o $OUTDIR/IncomingAPIArticle.md -f docs/system/IncomingAPIArticleFieldDescriptions.txt
python portality/lib/seamlessdoc.py -k portality.api.v2.data_objects.application.IncomingApplication -o $OUTDIR/IncomingAPIApplication.md -f docs/system/IncomingAPIApplicationFieldDescriptions.txt
python portality/lib/seamlessdoc.py -k portality.api.v2.data_objects.journal.OutgoingJournal -o $OUTDIR/OutgoingAPIJournal.md -f docs/system/OutgoingAPIJournalFieldDescriptions.txt
