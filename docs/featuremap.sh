#!/usr/bin/env bash

# Generate the feature map documentation
#
# To run this file you will need featuremap installed into your DOAJ env
#
# source [doaj env]/bin/activate
# git clone git@github.com:CottageLabs/FeatureMap.git
# cd FeatureMap
# pip install -r requirements.txt
#
# ~~FeatureMap:Script->FeatureMap:Technology~~

# Set up the variables we need for the script
DOAJ_DOCS="docs/generated"
BRANCH=$(git branch 2>/dev/null | grep '^*' | colrm 1 2)
OUTDIR=$DOAJ_DOCS/$BRANCH/featuremap

# make sure that we have the documentation submodule up-to-date
git submodule update --init --recursive
(cd $DOAJ_DOCS && git checkout master && git pull origin master)

# ensure that the output directory exists
mkdir -p $OUTDIR

featuremap -c docs/featuremap/config.yml -s https://github.com/DOAJ/doaj/blob/$BRANCH -o $OUTDIR