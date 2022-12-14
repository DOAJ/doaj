#!/usr/bin/env bash

###############################################
# Execute the test coverage analysis
#
# You will need to activate your virtualenv and have coverage installed: pip install coverage
#
# ~~TestCoverage:Script->UnitTests:Test~~
###############################################

BASE_DIR=$(dirname $(cd $(dirname "${BASH_SOURCE[0]}") && pwd))
DOAJ_DOCS="$(dirname $BASE_DIR)/doaj-docs"

while getopts 'd:' OPTION; do
  case "$OPTION" in
    d)
      DOAJ_DOCS="$OPTARG"
      ;;
  esac
done

echo "Running tests for coverage report (this will take a while)"
# Set up the variables we need for the script
BRANCH=$(git branch 2>/dev/null | grep '^*' | colrm 1 2)
OUTDIR=$DOAJ_DOCS/$BRANCH/coverage

# make sure that we have the documentation submodule up-to-date
(cd $DOAJ_DOCS && git checkout master && git pull origin master)

COVERAGE_FILE=$OUTDIR/coverage.data
export COVERAGE_FILE

echo "coverage run --source=portality,esprit,combinatrix,dictdiffer $(which pytest) $BASE_DIR/doajtest/unit/"
coverage run --source=portality,esprit,combinatrix,dictdiffer $(which pytest) $BASE_DIR/doajtest/unit/

echo "coverage html --include=portality*.py --omit=*/migrate/*,*/scripts/* -d $OUTDIR/report"
coverage html --include=portality*.py --omit=*/migrate/*,*/scripts/* -d $OUTDIR/report

