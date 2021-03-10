#!/usr/bin/env bash

# Run this script in this directory to compile the fixed query widget

# where we'll write the output to
OUT="fq_widget_depends_compiled.js"
BUILD="fq_widget_build_info.txt"

# path to dependencies


# combine all the dependencies into a single file in the right order (without jquery)
cat ../vendor/edges/src/es.js <(echo) \
    ../vendor/edges/src/edges.js <(echo) \
    ../vendor/edges/src/components/search.js <(echo) \
    ../js/doaj.fieldrender.edges.js <(echo) \
    ../vendor/edges/src/renderers/bs3.PagerRenderer.js <(echo) \
    > $OUT

# Record the Build time

echo "Build $(date -u +"%Y-%m-%dT%H:%M:%SZ")" > $BUILD