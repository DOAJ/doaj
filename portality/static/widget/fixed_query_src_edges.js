jQuery(document).ready(function($) {

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

        init : function(params) {
            if (!params) { params = {} }

            let current_domain = document.location.host;
            let current_scheme = window.location.protocol;

            let selector = params.selector || ".facetview";
            let search_url = current_scheme + "//" + current_domain + doaj.publicSearchConfig.publicSearchPath;
            let countFormat = edges.numFormat({
                thousandsSeparator: ","
            });


            let components = [

                // results display
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer : doaj.renderers.newPublicSearchResultRenderer()
                }),

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
                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [10, 25, 50, 100],
                        numberFormat: countFormat,
                        scrollSelector: "html, body"
                    })
                })
            ];
            let e = edges.newEdge({
                selector: selector,
                template: doaj.templates.newPublicSearch({
                    titleBar: false,
                    resultsOnly: true
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
    doaj.publicSearch.init(widget_fv_opts);

})();