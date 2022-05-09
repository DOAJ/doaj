$.extend(true, doaj, {

    notificationsSearch: {
        activeEdges: {},

        init: function (params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#notifications";
            var search_url = current_scheme + "//" + current_domain + doaj.notificationsSearchConfig.searchPath;

            var components = [
                doaj.components.searchingNotification(),

                // configure the search controller
                edges.newFullSearchController({
                    id: "search-controller",
                    category: "controller",
                    sortOptions: [
                        // {'display':'Date applied','field':'admin.date_applied'},
                        // {'display':'Last updated','field':'last_manual_update'},   // Note: last updated on UI points to when last updated by a person (via form)
                        // {'display':'Title','field':'index.unpunctitle.exact'}
                    ],
                    fieldOptions: [
                        // {'display':'Title','field':'index.title'},
                        // {'display':'Keywords','field':'bibjson.keywords'},
                        // {'display':'Classification','field':'index.classification'},
                        // {'display':'ISSN', 'field':'index.issn.exact'},
                        // {'display':'Country of publisher','field':'index.country'},
                        // {'display':'Journal Language','field':'index.language'},
                        // {'display':'Publisher','field':'bibjson.publisher.name'},
                        // {'display':'Journal: Alternative Title','field':'bibjson.alternative_title'}
                    ],
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: -1,
                        searchButton: true,
                        searchPlaceholder: "Search All Notifications",
                        clearButton: false
                    })
                }),

                // the pager, with the explicitly set page size options (see the openingQuery for the initial size)
                doaj.components.pager("top-pager", "top-pager"),
                doaj.components.pager("bottom-pager", "bottom-pager"),

                // results display
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer: edges.bs3.newResultsFieldsByRowRenderer({
                        rowDisplay: [
                            [
                                {
                                    "field": "created_date"
                                }
                            ],
                            [
                                {
                                    "field": "message"
                                }
                            ],
                            [
                                {
                                    "pre": '<a class="button" href="',
                                    "field": "action",
                                    "post": '">Action!</a>'
                                }
                            ],
                            [
                                {
                                    "field": "created_by"
                                },
                                {
                                    "pre": " - ",
                                    "field": "classification"
                                }
                            ]
                        ]
                    })
                }),

                // selected filters display, with all the fields given their display names
                edges.newSelectedFilters({
                    id: "selected-filters",
                    category: "selected-filters",
                    fieldDisplays: {}
                })
            ];

            var e = edges.newEdge({
                selector: selector,
                template: edges.bs3.newFacetview(),
                search_url: search_url,
                manageUrl: false,
                openingQuery : es.newQuery({
                    sort: {"field" : "created_date", "order" : "desc"},
                    size: 25
                }),
                components: components,
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact an administrator.");
                    }
                }
            });
            doaj.notificationsSearch.activeEdges[selector] = e;
        }
    }

});

jQuery(document).ready(function($) {
    doaj.notificationsSearch.init();
});