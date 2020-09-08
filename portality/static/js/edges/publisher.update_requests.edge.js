$.extend(true, doaj, {

    publisherUpdatesSearch : {
        activeEdges : {},

        publisherStatusMap: function(value) {
            if (doaj.valueMaps.applicationStatus.hasOwnProperty(value)) {
                return doaj.valueMaps.applicationStatus[value];
            }
            return value;
        },

        editUpdateRequest : function (resultobj) {
            if (resultobj.admin && resultobj.admin.application_status) {
                var result = {label : "", link : ""};
                var status = resultobj.admin.application_status;
                result.link = doaj.publisherUpdatesSearchConfig.journalReadOnlyUrl + resultobj['id'];
                result.label = "View";

                if (status === "update_request" || status === "revisions_required") {
                    result.link = doaj.publisherUpdatesSearchConfig.journalUpdateUrl + resultobj.admin.current_journal;
                    result.label = "Edit";
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
                edges.newORTermSelector({
                    id: "application_status",
                    category: "facet",
                    field: "admin.application_status.exact",
                    display: "Application Status",
                    size: 99,
                    valueFunction: doaj.publisherUpdatesSearch.publisherStatusMap,
                    syncCounts: false,
                    lifecycle: "update",
                    renderer : doaj.renderers.newORTermSelectorRenderer({
                        showCount: true,
                        hideEmpty: true,
                        open: true,
                        togglable: false
                    })
                }),

                // edges.newRefiningANDTermSelector({
                //     id: "application_status",
                //     category: "facet",
                //     field: "admin.application_status.exact",
                //     display: "Application Status",
                //     deactivateThreshold: 1,
                //     valueFunction: doaj.publisherUpdatesSearch.publisherStatusMap,
                //     renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                //         controls: false,
                //         open: true,
                //         togglable: false,
                //         countFormat: countFormat,
                //         hideInactive: true
                //     })
                // }),

                edges.newFullSearchController({
                    id: "sort_by",
                    category: "controller",
                    sortOptions : [
                        {'display':'Added to DOAJ (newest first)','field':'created_date', "dir" : "desc"},
                        {'display':'Added to DOAJ (oldest first)','field':'created_date', "dir" : "asc"},
                        {'display':'Last updated (most recent first)','field':'last_updated', "dir" : "desc"},
                        {'display':'Last updated (less recent first)','field':'last_updated', "dir" : "asc"},
                        {'display':'Title (A-Z)','field':'index.unpunctitle.exact', "dir" : "asc"},
                        {'display':'Title (Z-A)','field':'index.unpunctitle.exact', "dir" : "desc"},
                        {'display':'Relevance','field':'_score'}
                    ],
                    renderer: edges.bs3.newSortRenderer({
                        prefix: "Sort by",
                        dirSwitcher: false
                    })
                }),


                // configure the search controller
                // edges.newFullSearchController({
                //     id: "search-controller",
                //     category: "controller",
                //     sortOptions: [
                //         {'display': 'Date created', 'field': 'created_date'},
                //         {'display': 'Last updated', 'field': 'last_manual_update'},
                //         {'display': 'Title', 'field': 'index.unpunctitle.exact'}
                //     ],
                //     fieldOptions: [
                //         {'display': 'Title', 'field': 'index.title'},
                //         {'display': 'Alternative Title', 'field': 'bibjson.alternative_title'},
                //         {'display': 'Subject', 'field': 'index.subject'},
                //         {'display': 'Classification', 'field': 'index.classification'},
                //         {'display': 'ISSN', 'field': 'index.issn.exact'},
                //         {'display': 'Country of publisher', 'field': 'index.country'},
                //         {'display': 'Journal Language', 'field': 'index.language'},
                //         {'display': 'Publisher', 'field': 'bibjson.publisher'},
                //         {'display': 'Platform, Host, Aggregator', 'field': 'bibjson.provider'}
                //     ],
                //     defaultOperator: "AND",
                //     renderer: doaj.renderers.newFullSearchControllerRenderer({
                //         freetextSubmitDelay: 1000,
                //         searchButton: true,
                //         searchPlaceholder: "Search Update Requests in progress"
                //     })
                // }),

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
                    renderer : doaj.renderers.newPublisherUpdateRequestRenderer({
                        actions: [
                            doaj.publisherUpdatesSearch.editUpdateRequest
                        ]
                    })
                }),

                // edges.newResultsDisplay({
                //     id: "results",
                //     category: "results",
                //     renderer: edges.bs3.newResultsFieldsByRowRenderer({
                //         noResultsText: "<p>You do not have any active update requests that meet your search criteria</p>" +
                //             "<p>If you have not set any search criteria, you do not have any update requests at this time.</p>",
                //         rowDisplay: [
                //             [
                //                 {
                //                     valueFunction: doaj.fieldRender.titleField
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": '<span class="alt_title">Alternative title: ',
                //                     "field": "bibjson.alternative_title",
                //                     "post": "</span>"
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>Date applied</strong>: ",
                //                     valueFunction: doaj.fieldRender.suggestedOn
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>Last updated</strong>: ",
                //                     valueFunction: doaj.fieldRender.lastManualUpdate
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>ISSN(s)</strong>: ",
                //                     valueFunction: doaj.fieldRender.issns
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>Application status</strong>: ",
                //                     valueFunction: doaj.fieldRender.applicationStatus
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>Description</strong>: ",
                //                     "field": "suggestion.description"
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>Contact</strong>: ",
                //                     "field": "admin.contact.name"
                //                 },
                //                 {
                //                     "field": "admin.contact.email"
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>Application by</strong>: ",
                //                     "field": "suggestion.suggester.name",
                //                     "post": " "
                //                 },
                //                 {
                //                     "pre": "<strong>Applicant email</strong>: ",
                //                     "field": "suggestion.suggester.email"
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>Classification</strong>: ",
                //                     "field": "index.classification"
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>Keywords</strong>: ",
                //                     "field": "bibjson.keywords"
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>Publisher</strong>: ",
                //                     "field": "bibjson.publisher"
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>Platform, Host, Aggregator</strong>: ",
                //                     "field": "bibjson.provider"
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>Publication charges?</strong>: ",
                //                     valueFunction: doaj.fieldRender.authorPays
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>Started publishing Open Access content in</strong>: ",
                //                     "field": "bibjson.oa_start.year"
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>Stopped publishing Open Access content in</strong>: ",
                //                     "field": "bibjson.oa_end.year"
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>Country of publisher</strong>: ",
                //                     valueFunction: doaj.fieldRender.countryName
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>Journal Language</strong>: ",
                //                     "field": "bibjson.language"
                //                 }
                //             ],
                //             [
                //                 {
                //                     "pre": "<strong>Journal License</strong>: ",
                //                     valueFunction: doaj.fieldRender.journalLicense
                //                 }
                //             ],
                //             [
                //                 {
                //                     valueFunction: doaj.fieldRender.links
                //                 }
                //             ],
                //             [
                //                 {
                //                     valueFunction: doaj.publisherUpdatesSearch.editUpdateRequest
                //                 }
                //             ]
                //         ]
                //     })
                // }),

                // selected filters display, with all the fields given their display names
                edges.newSelectedFilters({
                    id: "selected-filters",
                    category: "selected-filters",
                    fieldDisplays: {
                        'admin.application_status.exact': 'Application Status'
                    }
                })
            ];

            var e = edges.newEdge({
                selector: selector,
                template: doaj.templates.newPublicSearch({
                    titleBar: false,
                    title: "Update requests"
                }),
                search_url: search_url,
                manageUrl: true,
                openingQuery: es.newQuery({
                    sort: [{"field" : "created_date", "order" : "desc"}],
                    size: 50
                }),
                components: components,
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact us.");
                    },
                    "edges:post-init" : function() {
                        feather.replace();
                    },
                    "edges:post-render" : function() {
                        feather.replace();
                    }
                }
            });
            doaj.publisherUpdatesSearch.activeEdges[selector] = e;

            // $(selector).on("edges:post-render", function () {
            //     $(".delete_suggestion_link").unbind("click").click(function (event) {
            //         event.preventDefault();
            //
            //         function success_callback(data) {
            //             alert("The update request was successfully deleted");
            //             doaj.publisherUpdatesSearch.activeEdges[selector].cycle();
            //         }
            //
            //         function error_callback() {
            //             alert("There was an error deleting the update request")
            //         }
            //
            //         var c = confirm("Are you really really sure?  You can't undo this operation!");
            //         if (c) {
            //             var href = $(this).attr("href");
            //             $.ajax({
            //                 type: "DELETE",
            //                 url: href,
            //                 success: success_callback,
            //                 error: error_callback
            //             })
            //         }
            //     });
            // });
        }
    }
});


jQuery(document).ready(function($) {
    doaj.publisherUpdatesSearch.init();
});
