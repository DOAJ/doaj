// ~~ AdminAlerts:Edge ~~
// ~~-> Edges:Technology ~~
$.extend(true, doaj, {

    adminAlertsSearch : {
        activeEdges : {},

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#admin_alerts";
            var search_url = current_scheme + "//" + current_domain + doaj.adminAlertsSearchConfig.searchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                doaj.components.searchingNotification(),

                // facets

                edges.newRefiningANDTermSelector({
                    id: "source",
                    category: "facet",
                    field: "source.exact",
                    display: "Source",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "state",
                    category: "facet",
                    field: "state.exact",
                    display: "State",
                    orderBy: "term",
                    orderDir: "asc",
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
                    id: "created_date",
                    category: "facet",
                    field : "created_date",
                    interval: "month",
                    display: "Date",
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
                        {'display':'Alert Date','field':'created_date'}
                    ],
                    fieldOptions: [
                        {'display':'Message','field':'message'},
                        {'display':'Source','field':'source'}
                    ],
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: -1,
                        searchButton: true,
                        searchPlaceholder: "Search All Alerts"
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
                                    pre : "From <strong>",
                                    field: "source",
                                    post: "</strong>"
                                },
                                {
                                    pre: " at <strong> ",
                                    field: "created_date",
                                    post: "</strong>"
                                }
                            ],
                            [
                                {
                                    pre : "<p>",
                                    field: "message",
                                    post: "</p>"
                                }
                            ],
                            [
                                {
                                    valueFunction: function(val, res, component) {
                                        let frag = `<a href="${doaj.adminAlertsSearchConfig.managePath}/${res.id}/in_progress" class="btn btn-primary">Set In Progress</a>
                                                            <a href="${doaj.adminAlertsSearchConfig.managePath}/${res.id}/closed" class="btn btn-success">Resolved</a>`;
                                    }
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
                        "source.exact" : "Source",
                        "state.exact" : "State",
                        "created_date" : "Alert Date"
                    },
                    rangeFunctions : {
                        "created_date" : doaj.valueMaps.displayYearMonthPeriod
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
                    must: [es.newTermFilter({field: "state.exact", value: "new"})],
                    sort: [{field: "created_date", order: "desc"}],
                    size: 25
                }),
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error. Please reload the page and try again. If the issue persists please contact an administrator.");
                    }
                }
            });
            doaj.adminAlertsSearch.activeEdges[selector] = e;
        }
    }
});


jQuery(document).ready(function($) {
    doaj.adminAlertsSearch.init();
});
