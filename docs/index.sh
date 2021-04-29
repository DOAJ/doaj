#!/usr/bin/env bash

# Generate the documentation index file

DOAJ_DOCS="docs/generated"
BRANCH=$(git branch 2>/dev/null | grep '^*' | colrm 1 2)
OUTDIR=$DOAJ_DOCS/$BRANCH

# make sure that we have the documentation submodule up-to-date
git submodule update --init --recursive
(cd $DOAJ_DOCS && git checkout master && git pull origin master)

# ensure that the output directory exists
mkdir -p $OUTDIR

OUTFILE=$OUTDIR/index.md

python portality/scripts/generate_docs_index.py -f $OUTFILE -d $OUTDIR