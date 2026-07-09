// ~~ AdminJournalsSearch:Feature ~~
$.extend(true, doaj, {

    adminWorkflowSearch : {
        activeEdges : {},

        openWorkflowOverview : function(val, resultobj, renderer) {
            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;
            let overviewUrl = current_scheme + "//" + current_domain + doaj.adminWorkflowSearchConfig.workflowPage + resultobj.application.id;
            return `<a href="${overviewUrl}" style="margin-right: 20px;">Manage Item</a>`;
        },

        openWorkflowForm : function(val, resultobj, renderer) {
            if (doaj.session.currentUserId === resultobj.state.reviewer) {
                var current_domain = document.location.host;
                var current_scheme = window.location.protocol;
                let overviewUrl = current_scheme + "//" + current_domain + doaj.adminWorkflowSearchConfig.triageForm + resultobj.application.id;
                return `<a href="${overviewUrl}">Continue Review</a>`;
            }
        },

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#admin_workflow";
            var search_url = current_scheme + "//" + current_domain + doaj.adminWorkflowSearchConfig.searchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                doaj.components.searchingNotification(),

                // facets
                edges.newRefiningANDTermSelector({
                    id: "module",
                    category: "facet",
                    field: "state.module.exact",
                    display: "Current Module",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: false,
                        open: true,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "stage",
                    category: "facet",
                    field: "state.stage.exact",
                    display: "Current Stage",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: false,
                        open: true,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "reviewer",
                    category: "facet",
                    field: "state.reviewer.exact",
                    display: "Assigned Reviewer",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: true,
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
                    display: "Created Date",
                    displayFormatter : function(val) {
                        return (new Date(parseInt(val))).toLocaleDateString(undefined, {
                            month: "short",
                            year: "numeric"
                        })
                    },
                    sortFunction : function(values) {
                        values.reverse();
                        return values;
                    },
                    renderer: edges.bs3.newDateHistogramSelectorRenderer({
                        countFormat: countFormat,
                        hideInactive: true,
                        open: true
                    })
                }),
                edges.newDateHistogramSelector({
                    id: "last_updated",
                    category: "facet",
                    field : "last_updated",
                    interval: "month",
                    display: "Last Updated",
                    displayFormatter : function(val) {
                        return (new Date(parseInt(val))).toLocaleDateString(undefined, {
                            month: "short",
                            year: "numeric"
                        })
                    },
                    sortFunction : function(values) {
                        values.reverse();
                        return values;
                    },
                    renderer: edges.bs3.newDateHistogramSelectorRenderer({
                        countFormat: countFormat,
                        hideInactive: true,
                        open: true
                    })
                }),

                // configure the search controller
                edges.newFullSearchController({
                    id: "search-controller",
                    category: "controller",
                    sortOptions: [
                        {'display':'Date added to DOAJ','field':'created_date'},
                        {'display':'Last updated','field':'last_updated'}, // Note: last updated on UI points to when last updated by a person (via form)
                        {'display':'Application Title','field':'application.title.exact'}
                    ],
                    fieldOptions: [
                        {'display':'Application Title','field':'application.title'}
                    ],
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: -1,
                        searchButton: true,
                        searchPlaceholder: "Search All Items in the Workflow"
                    })
                }),

                // the pager, with the explicitly set page size options (see the openingQuery for the initial size)
                edges.newPager({
                    id: "top-pager",
                    category: "top-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [10, 25, 50, 100],
                        numberFormat: countFormat,
                        scroll: false
                    })
                }),
                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [10, 25, 50, 100],
                        numberFormat: countFormat,
                        scroll: false
                    })
                }),

                // results display
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer: doaj.renderers.newAdminBasicResultsRenderer({
                        topRowDisplay: [
                            [
                                {
                                    field: "application.title"
                                }
                            ]
                        ],
                        leftRowDisplay : [
                            [
                                {
                                    "pre": 'Created Date: ',
                                    "field": "created_date"
                                }
                            ],
                            [
                                {
                                    "pre": "Last Updated: ",
                                    "field": "last_updated"
                                }
                            ]
                        ],
                        rightRowDisplay : [
                            [
                                {
                                    "pre" : "Module: ",
                                    field: "state.module"
                                }
                            ],
                            [
                                {
                                    "pre" : "Stage: ",
                                    field: "state.stage"
                                }
                            ],
                            [
                                {
                                    "pre" : "Reviewer: ",
                                    "field" : "state.reviewer"
                                }
                            ]
                        ],
                        bottomRowDisplay: [
                            [
                                {
                                    valueFunction: doaj.adminWorkflowSearch.openWorkflowOverview
                                },
                                {
                                    valueFunction: doaj.adminWorkflowSearch.openWorkflowForm
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
                        "state.module" : "Module",
                        "state.stage" : "Stage",
                        "state.reviewer" : "Reviewer",
                        "created_date" : "Created Date",
                        "last_updated" : "Last Updated"
                    },
                    renderer : doaj.renderers.newSelectedFiltersRenderer({}),
                    rangeFunctions : {
                        "created_date" : doaj.valueMaps.displayYearMonthPeriod,
                        "last_updated": doaj.valueMaps.displayYearMonthPeriod
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
                    sort: [{field: "created_date", order: "desc"}]
                }),
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error. Please reload the page and try again. If the issue persists please contact an administrator.");
                    }
                }
            });
            doaj.adminWorkflowSearch.activeEdges[selector] = e;
        }
    }
});


jQuery(document).ready(function($) {
    doaj.adminWorkflowSearch.init();
});
