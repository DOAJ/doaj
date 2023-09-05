#!/usr/bin/env bash

# Just run all of the doc generation scripts in default mode in the right order.
# Note: you must have git@github.com:DOAJ/doaj-docs checked out alongside DOAJ as a destination for the docs

# Supply arg --nocov to skip the test run and coverage report.

./forms.sh;
./data_models.sh;
./featuremap.sh;

if [ "$1" != '--nocov' ]
then
  ./coverage.sh;
fi

./testbook.sh;
./index.sh