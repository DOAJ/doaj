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

DOAJ_DOCS="../../doaj-docs"
BASE_DIR=$(dirname "${BASH_SOURCE[0]}")

while getopts 'd:' OPTION; do
  case "$OPTION" in
    d)
      DOAJ_DOCS="$OPTARG"
      ;;
  esac
done

echo "Generating FeatureMap"
# Set up the variables we need for the script
BRANCH=$(git branch 2>/dev/null | grep '^*' | colrm 1 2)
OUTDIR=$DOAJ_DOCS/$BRANCH/featuremap

# make sure that we have the documentation submodule up-to-date
(cd $DOAJ_DOCS && git checkout master && git pull origin master)

# ensure that the output directory exists
mkdir -p $OUTDIR

featuremap -c $BASE_DIR/featuremap/config.yml -s https://github.com/DOAJ/doaj/blob/$BRANCH -o $OUTDIR