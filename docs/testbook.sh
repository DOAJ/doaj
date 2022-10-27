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

echo "Generating Testbook"
# Set up the variables we need for the script
DOAJ_DOCS="docs/generated"
BRANCH=$(git branch 2>/dev/null | grep '^*' | colrm 1 2)
OUTDIR=$DOAJ_DOCS/$BRANCH/testbook

# make sure that we have the documentation submodule up-to-date
git submodule update --init --recursive
(cd $DOAJ_DOCS && git checkout master && git pull origin master)

# ensure that the output directory exists
mkdir -p $OUTDIR

testbook doajtest/testbook $OUTDIR -t https://doaj.github.io/doaj-docs/$BRANCH/testbook -a http://testdoaj.cottagelabs.com/ -r https://raw.githubusercontent.com/DOAJ/doaj/$BRANCH/doajtest
