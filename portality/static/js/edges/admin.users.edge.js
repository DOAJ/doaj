// ~~ AdminUserSearch:Feature ~~
doaj.userSearch = {
    activeEdges: {},

    editUserLink : function (val, resultobj, renderer) {
        var result = '<a class="edit_user_link button" href="';
        result += doaj.userSearchConfig.userEditUrl;
        result += resultobj['id'];
        result += '">Edit this user</a>';
        return result;
    },

    userJournalsLink : function (val, resultobj, renderer) {
        var q = {
            "query": {
                "bool": {
                    "must": [{
                        "term": {"admin.owner.exact": resultobj.id}
                    }]
                }
            }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#users";
            var search_url = current_scheme + "//" + current_domain + doaj.userSearchConfig.userSearchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                doaj.components.searchingNotification(),

                // facets
                edges.newRefiningANDTermSelector({
                    id: "role",
                    category: "facet",
                    field: "role.exact",
                    display: "Role",
                    deactivateThreshold: 1,
                    size: 20,
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
                    interval: "year",
                    display: "Created Date",
                    displayFormatter : function(val) {
                        return (new Date(parseInt(val))).getUTCFullYear();
                    },
                    sortFunction : function(values) {
                        values.reverse();
                        return values;
                    },
                    renderer: edges.bs3.newDateHistogramSelectorRenderer({
                        countFormat: countFormat,
                        hideInactive: true,
                        open: true,
                        togglable: true
                    })
                }),

                // configure the search controller
                edges.newFullSearchController({
                    id: "search-controller",
                    category: "controller",
                    sortOptions: [
                        {'display':'Created Date','field':'created_date'},
                        {'display':'Last Modified Date','field':'last_updated'},
                        {'display':'User ID','field':'id.exact'},
                        {'display':'Email address','field':'email.exact'}
                    ],
                    fieldOptions: [
                        {'display':'User ID','field':'id'},
                        {'display':'Email address','field':'email'}
                    ],
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: -1,
                        searchButton: true,
                        searchPlaceholder: "Search Users"
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
                                    "pre" : "<h3>",
                                    "field" : "id",
                                    "post" : "</h3>"
                                }
                            ],
                            [
                                {
                                    "pre": '<a href="mailto:',
                                    "field": "email",
                                    "post": '">'
                                },
                                {
                                    "field": "email",
                                    "post": '</a>'
                                }
                            ],
                            [
                                {
                                    "pre" : "<strong>Role(s)</strong>: <em>",
                                    "field" : "role",
                                    "post" : "</em>"
                                }
                            ],
                            [
                                {
                                    "pre" : "<strong>Account Created</strong>: ",
                                    "field" : "created_date"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Account Last Modified</strong>: ",
                                    "field": "last_updated"
                                }
                            ],
                            [
                                {
                                    "valueFunction" : doaj.userSearch.userJournalsLink
                                },
                                {
                                    "valueFunction": doaj.userSearch.editUserLink
                                }
                            ]
                        ]
                    ]
                })
            }),
            fieldDisplays: {
                "role.exact": "Role",
                "created_date": "Created Date"
            },
            rangeFunctions: {
                "created_date": doaj.valueMaps.displayYearPeriod
            },
            openingQuery: es.newQuery({size: 25})
        });

        doaj.userSearch.activeEdges[selector] = e;
    }
}

jQuery(document).ready(function($) {
    doaj.userSearch.init();
});
