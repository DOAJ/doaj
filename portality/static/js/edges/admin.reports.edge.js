$.extend(true, doaj, {

    adminReportsSearch : {
        activeEdges : {},

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#reports";
            var search_url = current_scheme + "//" + current_domain + doaj.adminReportsSearchConfig.searchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                doaj.components.searchingNotification(),

                // facets

                edges.newRefiningANDTermSelector({
                    id: "requester",
                    category: "facet",
                    field: "requester.exact",
                    display: "Produced By",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newDateHistogramSelector({
                    id: "generated_date",
                    category: "facet",
                    field : "generated_date",
                    interval: "month",
                    display: "Generated Date",
                    displayFormatter : function(val) {
                        let d = new Date(parseInt(val))
                        return d.getUTCFullYear().toString() + "-" + doaj.valueMaps.monthPadding(d.getUTCMonth() + 1);
                    },
                    sortFunction : function(values) {
                        values.reverse();
                        return values;
                    },
                    renderer: edges.bs3.newDateHistogramSelectorRenderer({
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),

                // configure the search controller
                edges.newFullSearchController({
                    id: "search-controller",
                    category: "controller",
                    sortOptions: [
                        {'display':'Generated Date','field':'generated_date'},
                        {"display": "Report Name", "field": "name.exact"}
                    ],
                    fieldOptions: [
                        {'display':'Requested by','field':'requester'},
                        {'display':'Report Name','field':'name'},
                        {'display':'Filename','field':'filename'}
                    ],
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: -1,
                        searchButton: true,
                        searchPlaceholder: "Search All Reports"
                    })
                }),

                // the pager, with the explicitly set page size options (see the openingQuery for the initial size)
                edges.newPager({
                    id: "top-pager",
                    category: "top-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [25, 50, 100],
                        numberFormat: countFormat,
                        scroll: false
                    })
                }),
                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [25, 50, 100],
                        numberFormat: countFormat,
                        scroll: false
                    })
                }),

                // results display
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer: edges.bs3.newResultsFieldsByRowRenderer({
                        rowDisplay : [
                            [
                                {
                                    pre: "<strong>",
                                    field: "name",
                                    post: "</strong>"
                                }
                            ],
                            [
                                {
                                    "pre": "A <strong>",
                                    field: "model",
                                    post: "</strong> report"
                                },
                                {
                                    pre : "requested by <strong>",
                                    field: "requester",
                                    post: "</strong>"
                                },
                                {
                                    pre: " at <strong> ",
                                    field: "request_date",
                                    post: "</strong>"
                                },
                                {
                                    pre: " and generated at <strong> ",
                                    field: "generated_date",
                                    post: "</strong>"
                                }
                            ],
                            [
                                {
                                    field: "constraints"
                                }
                            ],
                            // [
                            //     {
                            //         valueFunction: function(val, res, component) {
                            //             return markdownConverter.makeHtml(res.long);
                            //         }
                            //     }
                            // ],
                            [
                                {
                                    field: "filename"
                                }
                            ]
                        ]
                    })
                }),

                // selected filters display, with all the fields given their display names
                edges.newSelectedFilters({
                    id: "selected-filters",
                    category: "selected-filters",
                    fieldDisplays: {
                        "requester.exact" : "Requested By",
                        "generated_date" : "Generated Date"
                    },
                    rangeFunctions : {
                        "generated_date" : doaj.valueMaps.displayYearMonthPeriod
                    }
                })
            ];

            var e = edges.newEdge({
                selector: selector,
                template: edges.bs3.newFacetview(),
                search_url: search_url,
                manageUrl: true,
                components: components,
                openingQuery: es.newQuery({
                    sort: [{field: "generated_date", order: "desc"}],
                    size: 25
                }),
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error. Please reload the page and try again. If the issue persists please contact an administrator.");
                    }
                }
            });
            doaj.adminReportsSearch.activeEdges[selector] = e;
        }
    }
});


jQuery(document).ready(function($) {
    doaj.adminReportsSearch.init();
});
