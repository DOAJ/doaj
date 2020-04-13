#!/usr/bin/env bash

###############################################
# Execute the test coverage analysis
#
# You will need to activate your virtualenv and have coverage installed: pip install coverage
###############################################

# Specify the directory you want the output data and report to go to
OUTDIR=../doaj-docs/python3_edges_bs3_xml/coverage


COVERAGE_FILE=$OUTDIR/coverage.data
export COVERAGE_FILE

coverage run --source=portality,esprit,combinatrix,dictdiffer $(which nosetests) doajtest/unit/
coverage html --include=portality*.py --omit=*/migrate/*,*/scripts/* -d $OUTDIR/report

