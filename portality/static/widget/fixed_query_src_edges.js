    $.extend(true, doaj, {

        publicSearch : {
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

                let selector = params.selector || ".facetview";
                let search_url = doaj_url + doaj.publicSearchConfig.publicSearchPath;
                let countFormat = edges.numFormat({
                    thousandsSeparator: ','
                });


                let components = [

                    // the pager, with the explicitly set page size options (see the openingQuery for the initial size)
                    edges.newPager({
                        id: "top-pager",
                        category: "top-pager",
                        renderer: edges.bs3.newPagerRenderer({
                            sizeOptions: [10, 25, 50, 100],
                            numberFormat: countFormat,
                            scrollSelector: "html, body"
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
                    template: doaj.templates.newPublicSearch({
                        titleBar: false,
                        resultsOnly: false
                    }),
                    search_url: search_url,
                    manageUrl : false,
                    openingQuery: this.buildQuery(params),
                    components : components,
                    callbacks : {
                        "edges:query-fail" : function() {
                            alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact us.");
                        }
                    }
                });
                doaj.publicSearch.activeEdges[selector] = e;
            }
        }

    });
    doaj.publicSearch.init();
