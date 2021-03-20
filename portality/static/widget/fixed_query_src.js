$.extend(true, doaj, {

    fqwidget : {
        activeEdges : {},

        buildQuery: function(params){
            let query;
            if (params.rawQuery){
                query = es.newQuery({raw: params.queryString});
            }
            else {
                query = es.newQuery(params.initialParams);
                query.setQueryString(es.newQueryString(params.queryString));
                if(params.hasOwnProperty(`sortFilter`)) {
                    query.setSortBy(es.newSort(params.sortFilter));
                }
                if(params.hasOwnProperty(`es_type`)) {
                    query.addMust(es.newTermFilter({field: "es_type", value: params.es_type}));
                }
            }
            return query;
        },

        buildParams: function() {
            let widget_fv_opts = {};

            // If options have been set using the Export method, use only those
            if (typeof SEARCH_CONFIGURED_OPTIONS !== 'undefined') {
                widget_fv_opts.queryString = SEARCH_CONFIGURED_OPTIONS;
                widget_fv_opts.rawQuery = true;
            }
            // Otherwise, use options provided.
            else if (typeof QUERY_OPTIONS !== 'undefined') {
                widget_fv_opts.rawQuery = false;

                if(QUERY_OPTIONS.hasOwnProperty('selector')){
                    widget_fv_opts.selector = QUERY_OPTIONS.selector;
                }

                widget_fv_opts.initialParams = {};
                if (QUERY_OPTIONS.hasOwnProperty('page_size')) {
                    widget_fv_opts.initialParams.size = QUERY_OPTIONS.page_size;
                }
                if (QUERY_OPTIONS.hasOwnProperty('page_from')) {
                    widget_fv_opts.initialParams.from = QUERY_OPTIONS.page_from;
                }

                widget_fv_opts.queryString = {};
                if (QUERY_OPTIONS.hasOwnProperty('query_string')) {
                    widget_fv_opts.queryString.queryString = QUERY_OPTIONS.query_string;
                }
                if (QUERY_OPTIONS.hasOwnProperty('query_field')) {
                    widget_fv_opts.queryString.defaultField = QUERY_OPTIONS.query_field;
                }
                if (QUERY_OPTIONS.hasOwnProperty('search_operator')) {
                    widget_fv_opts.queryString.defaultOperator = QUERY_OPTIONS.search_operator;
                }

                widget_fv_opts.sortFilter = {};
                if (QUERY_OPTIONS.hasOwnProperty('sort_field')) {
                    widget_fv_opts.sortFilter.field = QUERY_OPTIONS.sort_field;
                }
                if (QUERY_OPTIONS.hasOwnProperty('sort_direction')) {
                    widget_fv_opts.sortFilter.sort_direction = QUERY_OPTIONS.sort_direction;
                }

                if (QUERY_OPTIONS.hasOwnProperty('search_type')) {
                    widget_fv_opts.es_type = QUERY_OPTIONS.search_type;
                }

            }

            return widget_fv_opts;
        },

        init : function() {

            let params = this.buildParams();
            let query = this.buildQuery(params);

            let selector = params.selector || ".facetview";
            let search_url = doaj_url + doaj.publicSearchConfig.publicSearchPath;
            let countFormat = edges.numFormat({
                thousandsSeparator: ','
            });


            let components = [

                edges.newPager({
                    id: "result-count",
                    category: "pager",
                    renderer : edges.bs3.newResultCountRenderer({
                        countFormat: countFormat,
                        suffix: ` results found for <code>` + query.queryString.queryString + `</code>`,
                        htmlContainerWrapper: false
                    })
                }),
                // the pager, with the explicitly set page size options (see the openingQuery for the initial size)
                edges.newPager({
                    id: "rpp",
                    category: "pager",
                    renderer : doaj.renderers.newPageSizeRenderer({
                        sizeOptions: [5, 50, 100, 200],
                        sizeLabel: "Results per page"
                    })
                }),
                edges.newPager({
                    id: "top-pager",
                    category: "top-pager",
                    renderer : doaj.renderers.newPagerRenderer({
                        numberFormat: countFormat,
                        scrollSelector: "#top-pager"
                    })
                }),
                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer : doaj.renderers.newPagerRenderer({
                        numberFormat: countFormat,
                        scrollSelector: "#top-pager"    // FIXME: these selectors don't work, why not?
                    })
                }),
                // results display
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer : doaj.renderers.newPublicSearchResultRenderer()
                }),
            ];

            let e = edges.newEdge({
                selector: selector,
                template: doaj.templates.newFQWidget({
                    titleBar: false,
                    resultsOnly: false
                }),
                search_url: search_url,
                manageUrl : false,
                openingQuery: query,
                components : components,
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact us.");
                    }
                }
            });
            doaj.fqwidget.activeEdges[selector] = e;
        }
    }

});
doaj.fqwidget.init();
