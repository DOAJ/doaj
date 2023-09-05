// ~~ AdminNotifications:Edge -> Notifications:Feature ~~
// ~~-> Edges:Technology ~~
$.extend(true, doaj, {

    adminNotificationsSearch : {
        activeEdges : {},

        createdByMap : {
            "application:assed:assigned:notify" : "AssEd: Assigned Application",
            "application:assed:inprogress:notify" : "AssEd: Application referred back",
            "application:editor:completed:notify" : "Editor: AssEd Completes Application",
            "application:editor_group:assigned:notify" : "Editor: Group assigned Application",
            "application:editor:inprogress:notify" : "Editor: Application referred back",
            "application:maned:ready:notify" : "ManEd: Editor Sets Application Ready",
            "application:publisher:accepted:notify" : "Publisher: Application Accepted",
            "application:publisher:assigned:notify" : "Publisher: Application assigned Editor",
            "application:publisher:created:notify" : "Publisher: Application received",
            "application:publisher:inprogress:notify" : "Publisher: Application in progress",
            "application:publisher:rejected:notify" : "Publisher: Application rejected",
            "application:publisher:quickreject:notify" : "Publisher: Application quick-rejected",
            "application:publisher:revision:notify" : "Publisher: Application requires revisions",
            "bg:job_finished:notify" : "Admin: Background Job finished",
            "journal:assed:assigned:notify" : "AssEd: Assigned Journal",
            "journal:editor_group:assigned:notify": "Editor: Group assigned Journal",
            "update_request:publisher:accepted:notify": "Publisher: UR accepted",
            "update_request:publisher:assigned:notify": "Publisher: UR assigned Editor",
            "update_request:publisher:rejected:notify": "Publisher: UR rejected"
        },

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#admin_notifications";
            var search_url = current_scheme + "//" + current_domain + doaj.adminNotificationsSearchConfig.searchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            let markdownConverter = new showdown.Converter({
                literalMidWordUnderscores: true
            });

            var components = [
                doaj.components.searchingNotification(),

                // facets

                edges.newRefiningANDTermSelector({
                    id: "who",
                    category: "facet",
                    field: "who.exact",
                    display: "Notification For",
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
                    id: "created_by",
                    category: "facet",
                    field: "created_by.exact",
                    display: "Notification",
                    size: 20,
                    orderBy: "term",
                    orderDir: "asc",
                    deactivateThreshold: 1,
                    valueMap: doaj.adminNotificationsSearch.createdByMap,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "classification",
                    category: "facet",
                    field: "classification.exact",
                    display: "Type",
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
                    display: "Notification Month",
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
                        {'display':'Notification Date','field':'created_date'}
                    ],
                    fieldOptions: [
                        {'display':'Notification For','field':'who'},
                        {'display':'Title','field':'short'},
                        {'display':'Body Text','field':'long'}
                    ],
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: -1,
                        searchButton: true,
                        searchPlaceholder: "Search All Notifications"
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
                                    pre : "For <strong>",
                                    field: "who",
                                    post: "</strong>"
                                },
                                {
                                    pre: " at <strong> ",
                                    field: "created_date",
                                    post: "</strong>"
                                },
                                {
                                    pre: " by <strong> ",
                                    field: "created_by",
                                    post: "</strong>"
                                },
                                {
                                    pre: " (",
                                    field: "classification",
                                    post: ")<br><br>"
                                }
                            ],
                            [
                                {
                                    pre : "<strong>",
                                    field: "short",
                                    post: "</strong>"
                                }
                            ],
                            [
                                {
                                    valueFunction: function(val, res, component) {
                                        return markdownConverter.makeHtml(res.long);
                                    }
                                }
                            ],
                            [
                                {
                                    pre: '<a href="',
                                    field: "action",
                                    post: '" target="_blank">See action</a>'
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
                        "who.exact" : "Who",
                        "created_by.exact" : "Action",
                        "classification.exact" : "Type",
                        "created_date" : "Notification Date"
                    },
                    valueMaps : {
                        "created_by.exact" : doaj.adminNotificationsSearch.createdByMap,
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
                    sort: [{field: "created_date", order: "desc"}],
                    size: 25
                }),
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error. Please reload the page and try again. If the issue persists please contact an administrator.");
                    }
                }
            });
            doaj.adminNotificationsSearch.activeEdges[selector] = e;
        }
    }
});


jQuery(document).ready(function($) {
    doaj.adminNotificationsSearch.init();
});
