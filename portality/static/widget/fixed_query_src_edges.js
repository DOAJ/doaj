jQuery(document).ready(function($) {

    $.extend(true, doaj, {

    publicSearch : {
        activeEdges : {},

        init : function(params) {
            if (!params) { params = {} }

            let current_domain = document.location.host;
            let current_scheme = window.location.protocol;

            let selector = params.selector || ".facetview";
            let search_url = current_scheme + "//" + current_domain + doaj.publicSearchConfig.publicSearchPath;

            let countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            let query = params.queryString || "{'query':{'match_all':{}}";

            let components = [
                edges.newPager({
                    id: "result-count",
                    category: "pager",
                    renderer : edges.bs3.newResultCountRenderer({
                        countFormat: countFormat,
                        suffix: " indexed journals",
                        htmlContainerWrapper: false
                    })
                }),

                edges.newDateHistogramSelector({
                    id : "year_added",
                    category: "facet",
                    field: "created_date",
                    interval: "year",
                    display: "Date added",
                    displayFormatter : function(val) {
                        return (new Date(parseInt(val))).getUTCFullYear();
                    },
                    sortFunction : function(values) {
                        values.reverse();
                        return values;
                    },
                }),

                edges.newPager({
                    id: "top-pager",
                    category: "top-pager",
                    renderer : doaj.renderers.newPagerRenderer({
                        numberFormat: countFormat,
                        scrollSelector: "#top-pager"
                    })
                }),

                // results display
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer : doaj.renderers.newPublicSearchResultRenderer()
                }),

                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer : doaj.renderers.newPagerRenderer({
                        numberFormat: countFormat,
                        scrollSelector: "#top-pager"    // FIXME: these selectors don't work, why not?
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
                manageUrl : true,
                // openingQuery : es.newQuery({
                //     size : 12,
                //     queryString: {queryString: query,
                //         defaultField: "bibjson.publisher.name.exact"},
                //     }),
                openingQuery: es.newQuery({
                    raw: query
                }),
                components : components,
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact us.");
                    },
                    "edges:post-init" : function() {
                        feather.replace();
                    },
                    "edges:post-render" : function() {
                        feather.replace();
                    }
                }
            });
            doaj.publicSearch.activeEdges[selector] = e;
        }
    }

});

    let query = {"query":{"filtered":{"filter":{"bool":{"must":[{"terms":{"bibjson.publisher.name.exact":["MDPI AG"]}},{"terms":{"bibjson.editorial.review_process.exact":["Peer review"]}}]}},"query":{"match_all":{}}}}};
    doaj.publicSearch.init({queryString: query});

})();