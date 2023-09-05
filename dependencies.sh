#!/bin/sh

rm -rf dependencies_analysis
mkdir dependencies_analysis

pipdeptree --json --reverse >> dependencies_analysis/dependencies.json
pip list --format json -o >> dependencies_analysis/upgrade.json