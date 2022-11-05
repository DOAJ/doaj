#!/usr/bin/env bash

# Generate the testbook for the functional tests
#
# To run this file you will need testbook installed into your DOAJ env
#
# source [doaj env]/bin/activate
# git clone git@github.com:CottageLabs/testbook.git
# cd testbook
# pip install -r requirements.txt
#
# ~~Testbook:Script->Testbook:Technology~~

BRANCH=$(git branch 2>/dev/null | grep '^*' | colrm 1 2)

DOAJ_DOCS="../../doaj-docs"
TESTBOOK_URL="https://doaj.github.io/doaj-docs/$BRANCH/testbook"
DOAJ_URL="http://testdoaj.cottagelabs.com/"
DOAJ_TEST_FILEBASE="https://raw.githubusercontent.com/DOAJ/doaj/$BRANCH/doajtest"

BASE_DIR=$(dirname "${BASH_SOURCE[0]}")

while getopts 'd:b:t:f:' OPTION; do
  case "$OPTION" in
    d)
      DOAJ_DOCS="$OPTARG"
      ;;
    b)
      TESTBOOK_URL="$OPTARG"
      ;;
    t)
      DOAJ_URL="$OPTARG"
      ;;
    f)
      DOAJ_TEST_FILEBASE="$OPTARG"
      ;;
  esac
done

echo "Generating Testbook"

# Set up the variables we need for the script
OUTDIR=$DOAJ_DOCS/$BRANCH/testbook

# make sure that we have the documentation submodule up-to-date
(cd $DOAJ_DOCS && git checkout master && git pull origin master)

# ensure that the output directory exists
mkdir -p $OUTDIR

testbook $BASE_DIR/../doajtest/testbook $OUTDIR -t $TESTBOOK_URL -a $DOAJ_URL -r $DOAJ_TEST_FILEBASE

echo "If you are running this locally you can now go to $OUTDIR and run 'python -m SimpleHTTPServer'"