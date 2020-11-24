$.extend(true, doaj, {

    userSearch: {
        activeEdges: {},

        editUserLink : function (val, resultobj, renderer) {
            var result = '<a class="edit_user_link button" href="';
            result += doaj.userSearchConfig.userEditUrl;
            result += resultobj['id'];
            result += '" target="_blank"';
            result += '>Edit this user</a>';
            return result;
        },

        userJournalsLink : function (val, resultobj, renderer) {
            var q = {
                "query":{
                    "filtered":{
                        "filter":{
                            "bool":{
                                "must":[{"term":{"admin.owner.exact":resultobj.id}}]
                            }
                        },
                        "query":{"match_all":{}}
                    }
                }
            };
            return '<br/><a class="button" href="/admin/journals?source=' + encodeURIComponent(JSON.stringify(q)) + '">View Journals</a>'
        },

        init : function(params) {
            if (!params) {
                params = {}
            }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#users";
            var search_url = current_scheme + "//" + current_domain + doaj.userSearchConfig.userSearchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                // facets
                edges.newRefiningANDTermSelector({
                    id: "role",
                    category: "facet",
                    field: "role",
                    display: "Role",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: true,
                        togglable: false,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),

                // configure the search controller
                edges.newFullSearchController({
                    id: "search-controller",
                    category: "controller",
                    sortOptions: [
                        {'display':'Created Date','field':'created_date'},
                        {'display':'Last Modified Date','field':'last_updated'},
                        {'display':'User ID','field':'id'},
                        {'display':'Email address','field':'email'}
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
                        scrollSelector: "html, body"
                    })
                }),
                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [25, 50, 100],
                        numberFormat: countFormat,
                        scrollSelector: "html, body"
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
                    })
                }),

                // selected filters display, with all the fields given their display names
                edges.newSelectedFilters({
                    id: "selected-filters",
                    category: "selected-filters",
                    fieldDisplays: {
                        "role": "Role"
                    }
                }),

                // the standard searching notification
                edges.newSearchingNotification({
                    id: "searching-notification",
                    category: "searching-notification"
                })
            ];

            var e = edges.newEdge({
                selector: selector,
                template: edges.bs3.newFacetview(),
                search_url: search_url,
                openingQuery : es.newQuery({size: 25}),
                manageUrl: true,
                components: components,
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact an administrator.");
                    }
                }
            });
            doaj.userSearch.activeEdges[selector] = e;
        }
    }
});

jQuery(document).ready(function($) {
    doaj.userSearch.init();
});
