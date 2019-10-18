$.extend(true, doaj, {

    publisherUpdatesSearch : {
        activeEdges : {},

        publisherStatusMap: function(value) {
            if (doaj.valueMaps.applicationStatus.hasOwnProperty(value)) {
                return doaj.valueMaps.applicationStatus[value];
            }
            return value;
        },

        editUpdateRequest : function (value, resultobj, renderer) {
            if (resultobj['suggestion']) {
                if (resultobj.admin && resultobj.admin.application_status) {
                    var status = resultobj.admin.application_status;
                    var result = "";
                    var view = '(<a href="' + doaj.publisherUpdatesSearchConfig.journalReadOnlyUrl + resultobj['id'] + '">view request</a>)';
                    if (status === "update_request" || status == "revisions_required") {
                        var actionUrl = doaj.publisherUpdatesSearchConfig.journalUpdateUrl + resultobj.admin.current_journal;
                        result = '<span><a class="edit_suggestion_link" href="' + actionUrl;
                        result += '"';
                        result += '>Edit this update request</a> | <a href="' + actionUrl + '" class="delete_suggestion_link">Delete this update request</a></span>';
                    } else  if (status !== "rejected" && status !== "accepted") {
                        result = '<span>This update request is currently being reviewed by an Editor ' + view + '.</span>';
                    } else if (status === "rejected") {
                        result = '<span>This update request has been rejected ' + view + '.</span>';
                    } else if (status === "accepted") {
                        result = '<span>This update request has been accepted, and your journal in DOAJ updated ' + view + '.</span>';
                    }
                    return result;
                }
            }
            return false;
        },

        init : function(params) {
            if (!params) {
                params = {}
            }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#publisher_update_requests";
            var search_url = current_scheme + "//" + current_domain + doaj.publisherUpdatesSearchConfig.searchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                // facets
                edges.newRefiningANDTermSelector({
                    id: "application_status",
                    category: "facet",
                    field: "admin.application_status.exact",
                    display: "Application Status",
                    deactivateThreshold: 1,
                    valueFunction: doaj.publisherUpdatesSearch.publisherStatusMap,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: false,
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
                        {'display': 'Date created', 'field': 'created_date'},
                        {'display': 'Last updated', 'field': 'last_manual_update'},
                        {'display': 'Title', 'field': 'index.unpunctitle.exact'}
                    ],
                    fieldOptions: [
                        {'display': 'Title', 'field': 'index.title'},
                        {'display': 'Alternative Title', 'field': 'bibjson.alternative_title'},
                        {'display': 'Subject', 'field': 'index.subject'},
                        {'display': 'Classification', 'field': 'index.classification'},
                        {'display': 'ISSN', 'field': 'index.issn.exact'},
                        {'display': 'Country of publisher', 'field': 'index.country'},
                        {'display': 'Journal Language', 'field': 'index.language'},
                        {'display': 'Publisher', 'field': 'index.publisher'},
                        {'display': 'Platform, Host, Aggregator', 'field': 'bibjson.provider'}
                    ],
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: 1000,
                        searchButton: true,
                        searchPlaceholder: "Search Update Requests in progress"
                    })
                }),

                // the pager, with the explicitly set page size options (see the openingQuery for the initial size)
                edges.newPager({
                    id: "top-pager",
                    category: "top-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [10, 25, 50, 100],
                        numberFormat: countFormat,
                        scrollSelector: "html, body"
                    })
                }),
                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [10, 25, 50, 100],
                        numberFormat: countFormat,
                        scrollSelector: "html, body"
                    })
                }),

                // results display
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer: edges.bs3.newResultsFieldsByRowRenderer({
                        noResultsText: "<p>You do not have any active update requests that meet your search criteria</p>" +
                            "<p>If you have not set any search criteria, you do not have any update requests at this time.</p>",
                        rowDisplay: [
                            [
                                {
                                    valueFunction: doaj.fieldRender.titleField
                                }
                            ],
                            [
                                {
                                    "pre": '<span class="alt_title">Alternative title: ',
                                    "field": "bibjson.alternative_title",
                                    "post": "</span>"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Date applied</strong>: ",
                                    valueFunction: doaj.fieldRender.suggestedOn
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Last updated</strong>: ",
                                    valueFunction: doaj.fieldRender.lastManualUpdate
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>ISSN(s)</strong>: ",
                                    valueFunction: doaj.fieldRender.issns
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Application status</strong>: ",
                                    valueFunction: doaj.fieldRender.applicationStatus
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Description</strong>: ",
                                    "field": "suggestion.description"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Contact</strong>: ",
                                    "field": "admin.contact.name"
                                },
                                {
                                    "field": "admin.contact.email"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Application by</strong>: ",
                                    "field": "suggestion.suggester.name",
                                    "post": " "
                                },
                                {
                                    "pre": "<strong>Applicant email</strong>: ",
                                    "field": "suggestion.suggester.email"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Classification</strong>: ",
                                    "field": "index.classification"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Keywords</strong>: ",
                                    "field": "bibjson.keywords"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Publisher</strong>: ",
                                    "field": "bibjson.publisher"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Platform, Host, Aggregator</strong>: ",
                                    "field": "bibjson.provider"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Publication charges?</strong>: ",
                                    valueFunction: doaj.fieldRender.authorPays
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Started publishing Open Access content in</strong>: ",
                                    "field": "bibjson.oa_start.year"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Stopped publishing Open Access content in</strong>: ",
                                    "field": "bibjson.oa_end.year"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Country of publisher</strong>: ",
                                    valueFunction: doaj.fieldRender.countryName
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Journal Language</strong>: ",
                                    "field": "bibjson.language"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Journal License</strong>: ",
                                    valueFunction: doaj.fieldRender.journalLicense
                                }
                            ],
                            [
                                {
                                    valueFunction: doaj.fieldRender.links
                                }
                            ],
                            [
                                {
                                    valueFunction: doaj.publisherUpdatesSearch.editUpdateRequest
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
                        'admin.application_status.exact': 'Application Status'
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
                manageUrl: true,
                openingQuery: es.newQuery({
                    sort: {"field": "last_manual_update", "order": "asc"}
                }),
                components: components,
                callbacks: {
                    "edges:query-fail": function () {
                        alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact us.");
                    }
                }
            });
            doaj.publisherUpdatesSearch.activeEdges[selector] = e;

            $(selector).on("edges:post-render", function () {
                $(".delete_suggestion_link").unbind("click").click(function (event) {
                    console.log("click registered")
                    event.preventDefault();

                    function success_callback(data) {
                        alert("The update request was successfully deleted");
                        doaj.publisherUpdatesSearch.activeEdges[selector].cycle();
                    }

                    function error_callback() {
                        alert("There was an error deleting the update request")
                    }

                    var c = confirm("Are you really really sure?  You can't undo this operation!");
                    if (c) {
                        var href = $(this).attr("href");
                        var obj = {"delete": "true"};
                        $.ajax({
                            type: "DELETE",
                            url: href,
                            data: obj,
                            success: success_callback,
                            error: error_callback
                        })
                    }
                });
            });
        }
    }
});


jQuery(document).ready(function($) {
    doaj.publisherUpdatesSearch.init();
});
