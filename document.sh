#!/usr/bin/env bash
# In order to run this you need to have epydoc (http://epydoc.sourceforge.net/) installed, which can be done
# on Ubuntu with
#
# sudo apt-get install python-epydoc

rm docs/code/*
epydoc --html -o docs/code/ --name "DOAJ" --url https://github.com/DOAJ/doaj --graph all --inheritance grouped --docformat restructuredtext portality

# Generate the model documentation in markdown
python portality/lib/modeldoc.py -k portality.models.Journal -o docs/system/Journal.md -f docs/system/field_descriptions.txt
python portality/lib/modeldoc.py -k portality.models.Suggestion -o docs/system/Suggestion.md -f docs/system/field_descriptions.txt
