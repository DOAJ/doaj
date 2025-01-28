// ~~ AdminNotifications:Edge -> Notifications:Feature ~~
// ~~-> Edges:Technology ~~
$.extend(true, doaj, {

    adminNotificationsSearch : {
        activeEdges : {},

        createdByMap : {
            "application:assed:acceptreject:notify": "Application: AssEd: Accepted/Rejected",
            "application:assed:assigned:notify" : "Application: AssEd: Assigned",
            "application:assed:inprogress:notify" : "Application: AssEd: Referred back",
            "application:editor:acceptreject:notify": "Application: Editor: Accepted/Rejected",
            "application:editor:completed:notify" : "Application: Editor: Completed",
            "application:editor_group:assigned:notify" : "Application: Editor: Group assigned",
            "application:editor:inprogress:notify" : "Application: Editor: Referred back",
            "application:maned:ready:notify" : "Application: ManEd: Editor Sets Ready",
            "application:publisher:accepted:notify" : "Application: Publisher: Accepted",
            "application:publisher:assigned:notify" : "Application: Publisher: Assigned Editor",
            "application:publisher:created:notify" : "Application: Publisher: Received",
            "application:publisher:inprogress:notify" : "Application: Publisher: In progress",
            "application:publisher:rejected:notify" : "Application: Publisher: Rejected",
            "application:publisher:quickreject:notify" : "Application: Publisher: Quick-rejected",
            "application:publisher:revision:notify" : "Application: Publisher: Requires revisions",
            "bg:job_finished:notify" : "Background Job: Admin: Finished",
            "journal:assed:assigned:notify" : "Journal: AssEd: Assigned",
            "journal:editor_group:assigned:notify": "Journal: Editor: Group assigned",
            "update_request:maned:editor_group_assigned:notify": "UR: ManEd: Assigned",
            "update_request:publisher:accepted:notify": "UR: Publisher: Accepted",
            "update_request:publisher:assigned:notify": "UR: Publisher: Assigned Editor",
            "update_request:publisher:rejected:notify": "UR: Publisher: Rejected",
            "update_request:publisher:submitted:notify": "UR: Publisher: Submitted"
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
