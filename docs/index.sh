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

# generate the index for the specific branch
OUTFILE=$OUTDIR/README.md
python portality/scripts/generate_docs_index.py -b -f $OUTFILE -d $OUTDIR

# generate the global index for the docs repo
README=$DOAJ_DOCS/README.md
python portality/scripts/generate_docs_index.py -g -f $README -d $DOAJ_DOCS