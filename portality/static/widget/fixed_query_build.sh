#!/usr/bin/env bash

# Run this script in this directory to compile the fixed query widget

# where we'll write the output to
OUT="fq_widget_depends_compiled.js"
BUILD="fq_widget_build_info.txt"

# path to dependencies

#first add doaj.js to the file

# combine all the dependencies into a single file in the right order (without jquery)
cat ../js/doaj.js <(echo) \
    public_search_config.js <(echo) \
    ../vendor/edges/src/es7x.js <(echo) \
    ../vendor/edges/src/edges.js <(echo) \
    ../vendor/edges/src/components/search.js <(echo) \
    ../js/doaj.fieldrender.edges.js <(echo) \
    ../vendor/edges/src/renderers/bs3.ResultCountRenderer.js \
    ../vendor/edges/src/renderers/bs3.PagerRenderer.js <(echo) \
    > $OUT

#replace all $ with jQuery
# sed -i 's/\$/jQuery/g' $OUT


# Record the Build time
echo "Build $(date -u +STD_DATETIME_FMT)" > $BUILD