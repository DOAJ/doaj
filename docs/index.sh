#!/usr/bin/env bash

# ~~GeneratedDocsIndex:Script~~

DOAJ_DOCS="../../doaj-docs"
BASE_DIR=$(dirname $(cd $(dirname "${BASH_SOURCE[0]}") && pwd))

while getopts 'd:' OPTION; do
  case "$OPTION" in
    d)
      DOAJ_DOCS="$OPTARG"
      ;;
  esac
done

echo "Generating the documentation index file"
BRANCH=$(git branch 2>/dev/null | grep '^*' | colrm 1 2)
OUTDIR=$DOAJ_DOCS/$BRANCH

# make sure that we have the documentation submodule up-to-date
(cd $DOAJ_DOCS && git checkout master && git pull origin master)

# ensure that the output directory exists
mkdir -p $OUTDIR

# generate the index for the specific branch
OUTFILE=$OUTDIR/README.md
python $BASE_DIR/portality/scripts/generate_docs_index.py -b -f $OUTFILE -d $OUTDIR

# generate the global index for the docs repo
README=$DOAJ_DOCS/README.md
python $BASE_DIR/portality/scripts/generate_docs_index.py -g -f $README -d $DOAJ_DOCS