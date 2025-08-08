// ~~ AdminAlerts:Edge ~~
// ~~-> Edges:Technology ~~
$.extend(true, doaj, {

    adminAutoassignSearch : {
        activeEdges : {},

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#autoassign";
            var search_url = current_scheme + "//" + current_domain + doaj.adminAutoassignSearchConfig.searchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                doaj.components.searchingNotification(),

                // facets
                edges.newRefiningANDTermSelector({
                    id: "target",
                    category: "facet",
                    field: "target.exact",
                    display: "Editor Group",
                    orderBy: "term",
                    orderDir: "asc",
                    size: 50,
                    deactivateThreshold: 0,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),

                edges.newRefiningANDTermSelector({
                    id: "account",
                    category: "facet",
                    field: "account_id.exact",
                    display: "Publisher",
                    orderBy: "term",
                    orderDir: "asc",
                    deactivateThreshold: 0,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),

                edges.newRefiningANDTermSelector({
                    id: "country_name",
                    category: "facet",
                    field: "country_name.exact",
                    display: "Country Name",
                    orderBy: "term",
                    orderDir: "asc",
                    deactivateThreshold: 0,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),

                // configure the search controller
                edges.newFullSearchController({
                    id: "search-controller",
                    category: "controller",
                    sortOptions: [
                        {'display':'Import Date','field':'created_date'},
                        {'display':'Publisher','field':'account_id.exact'},
                        {'display':'Country Name','field':'country_name.exact'},
                        {'display':'Editor Group','field':'target.exact'}
                    ],
                    fieldOptions: [
                        {'display':'Editor Group','field':'target'},
                        {'display':'Publisher','field':'account_id'},
                        {'display':'Country Name','field':'country_name'}
                    ],
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: -1,
                        searchButton: true,
                        searchPlaceholder: "Search All Routers"
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
                    renderer: edges.bs3.newTabularResultsRenderer({
                        // the fields to display in the results table
                        fieldDisplay: [
                            {
                                field: "account_id",
                                display: "Publisher",
                                valueFunction: function(value, result) {
                                    if (value && value !== "-") {
                                        return `<a href="/account/${value}">${value}</a>`;
                                    }
                                    return value;
                                }
                            },
                            {
                                field: "country_name",
                                display: "Country Name",
                            },
                            {
                                field: "country_code",
                                display: "Country Code"
                            },
                            {
                                field: "target",
                                display: "Editor Group",
                                valueFunction: function(value, result) {
                                    if (value && value !== "-") {
                                        let source = doaj.searchQuerySource({
                                            queryString: value,
                                            defaultField: "name",
                                        })
                                        return `<a href="/admin/editor_groups?source=${source}">${value}</a>`;
                                    }
                                    return value;
                                }
                            },
                            {
                                field: "created_date",
                                display: "Import Date"
                            }
                        ]
                    })
                }),

                // selected filters display, with all the fields given their display names
                edges.newSelectedFilters({
                    id: "selected-filters",
                    category: "selected-filters",
                    fieldDisplays: {
                        "target.exact" : "Editor Group",
                        "country_name.exact" : "Country Name",
                        "account_id.exact" : "Publisher"
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
            doaj.adminAutoassignSearch.activeEdges[selector] = e;
        }
    }
});


jQuery(document).ready(function($) {
    doaj.adminAutoassignSearch.init();
});
