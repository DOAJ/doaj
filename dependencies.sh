#!/bin/sh

rm dependencies.json
rm dependencies.csv

pipdeptree --json --reverse >> dependencies.json