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
                result.label = '<span data-feather="eye" aria-hidden="true"></span><span>View</span>';

                if (status === "update_request" || status === "revisions_required") {
                    result.link = doaj.publisherUpdatesSearchConfig.journalUpdateUrl + resultobj.admin.current_journal;
                    result.label = '<span data-feather="edit-3" aria-hidden="true"></span><span>Edit</span>';
                }
                return result;
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
                    renderer: doaj.renderers.newSortRenderer({
                        prefix: "Sort by",
                        dirSwitcher: false
                    })
                }),

                edges.newPager({
                    id: "rpp",
                    category: "pager",
                    renderer : doaj.renderers.newPageSizeRenderer({
                        sizeOptions: [50, 100, 200],
                        sizeLabel: "Results per page"
                    })
                }),

                // the pager, with the explicitly set page size options (see the openingQuery for the initial size)
                edges.newPager({
                    id: "top-pager",
                    category: "top-pager",
                    renderer : doaj.renderers.newPagerRenderer({
                        numberFormat: countFormat,
                        scrollSelector: "#top-pager"
                    })
                }),
                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer : doaj.renderers.newPagerRenderer({
                        numberFormat: countFormat,
                        scrollSelector: "#top-pager"    // FIXME: these selectors don't work, why not?
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

                // selected filters display, with all the fields given their display names
                edges.newSelectedFilters({
                    id: "selected-filters",
                    category: "selected-filters",
                    fieldDisplays: {
                        'admin.application_status.exact': 'Application Status'
                    },
                    renderer : doaj.renderers.newSelectedFiltersRenderer()
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
