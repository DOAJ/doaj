#!/usr/bin/env bash

# Run this script in this directory to compile the fixed query widget

# where we'll write the output to
OUT="fq_widget_depends_compiled.js"
BUILD="fq_widget_build_info.txt"

# path to facetview2
FV="../portality/vendor/facetview2"

# path to doaj js
DOAJ="../doaj/js"

# combine all the dependencies into a single file in the right order (without jquery)
cat $FV/es.js <(echo) \
    $FV/bootstrap2.facetview.theme.js <(echo) \
    $DOAJ/doaj.facetview.theme.js <(echo) \
    $FV/jquery.facetview2.js <(echo) \
    fixed_query_src.js <(echo) \
    > $OUT

# Record the Build time

echo "Build $(date -u +"%Y-%m-%dT%H:%M:%SZ")" > $BUILD