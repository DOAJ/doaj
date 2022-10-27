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

echo "Generating (Local) Testbook"
# Set up the variables we need for the script
DOAJ_DOCS="/home/richard/tmp/doaj/testbook2"
TESTBOOK_URL="http://localhost8000"
DOAJ_URL="http://localhost:5004"
DOAJ_TEST_FILEBASE="file:///home/richard/Code/External/doaj3/doajtest"

BRANCH=$(git branch 2>/dev/null | grep '^*' | colrm 1 2)
OUTDIR=$DOAJ_DOCS/$BRANCH

# ensure that the output directory exists
mkdir -p $OUTDIR

testbook doajtest/testbook $OUTDIR -t $TESTBOOK_URL -a $DOAJ_URL -r $DOAJ_TEST_FILEBASE

echo "Now go to $OUTDIR and run 'python -m SimpleHTTPServer'"
