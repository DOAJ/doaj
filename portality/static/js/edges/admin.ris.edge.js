// ~~ AdminAlerts:Edge ~~
// ~~-> Edges:Technology ~~
$.extend(true, doaj, {

    adminRISSearch : {
        activeEdges : {},

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#ris";
            var search_url = current_scheme + "//" + current_domain + doaj.adminRISSearchConfig.searchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                doaj.components.searchingNotification(),

                // configure the search controller
                edges.newFullSearchController({
                    id: "search-controller",
                    category: "controller",
                    sortOptions: [
                        {'display':'Created Date','field':'created_date'},
                        {'display':'Last Updated','field':'last_updated'}
                    ],
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: -1,
                        searchButton: true,
                        searchPlaceholder: "Search All RIS Exports"
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
                        noResultsText: "No RIS exports match the selected criteria.",
                        // the fields to display in the results table
                        rowDisplay: [
                            [{
                                field: "created_date",
                                pre: "Created Date: "
                            }],
                            [{
                                field: "created_date",
                                pre: "Last Updated: "
                            }],
                            [{
                                field: "id",
                                pre: "Article ID: "
                            }],
                            [{
                                field: "ris",
                                pre: "<code>",
                                post: "</code>",
                                valueFunction: function(val, res, component) {
                                    return val.replace(/\n/g, "<br/>");
                                }
                            }],
                            [{
                                valueFunction: function(val, res, renderer) {
                                    const del_class = edges.css_classes(renderer.namespace, "delete", renderer);
                                    const regen_class = edges.css_classes(renderer.namespace, "regenerate", renderer);
                                    return `<button class="${del_class}" data-id="${res.id}">Delete Record</button>
                                            <button class="${regen_class}" data-id=${res.id}">Regenerate</button>`;
                                }
                            }]
                        ]
                    })
                })
            ];

            var e = edges.newEdge({
                selector: selector,
                template: edges.bs3.newFacetview(),
                search_url: search_url,
                manageUrl: true,
                components: components,
                openingQuery: es.newQuery({
                    sort: [{field: "last_updated", order: "desc"}],
                    size: 25
                }),
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error. Please reload the page and try again. If the issue persists please contact an administrator.");
                    },
                    "edges:post-render" : function() {
                        let resultsComponent = doaj.adminRISSearch.activeEdges[selector].getComponent({id: "results"});
                        let deleteSelector = edges.css_class_selector(resultsComponent.renderer.namespace, "delete");
                        $(deleteSelector).on("click", function(e) {
                            e.preventDefault();
                            let a = e.currentTarget;
                            let id = a.getAttribute("data-id");
                            let proceed = confirm("Deleting the RIS export will cause it to be regenerated the next time it is requested, or the regular RIS export runs")
                            if (!proceed) {
                                return;
                            }
                            $.ajax({
                                method: "POST",
                                url: "/admin/ris/" + id + "/delete",
                                success: function(data) {
                                    // reload the page to see the changes
                                    // window.location.reload();
                                    alert("Deleted successfully, reload the page to see the changes");
                                },
                                error: function(xhr, status, error) {
                                    alert("There was an unexpected error processing your request.");
                                }
                            })
                        })

                        let regenerateSelector = edges.css_class_selector(resultsComponent.renderer.namespace, "regenerate");
                        $(regenerateSelector).on("click", function(e) {
                            e.preventDefault();
                            let a = e.currentTarget;
                            let id = a.getAttribute("data-id");
                            let proceed = confirm("Regenerate the RIS Export?")
                            if (!proceed) {
                                return;
                            }
                            $.ajax({
                                method: "POST",
                                url: "/admin/ris/" + id + "/regenerate",
                                success: function(data) {
                                    // reload the page to see the changes
                                    // window.location.reload();
                                    alert("Regenerated successfully, reload the page to see the changes");
                                },
                                error: function(xhr, status, error) {
                                    alert("There was an unexpected error processing your request.");
                                }
                            })
                        })
                    }
                }
            });
            doaj.adminRISSearch.activeEdges[selector] = e;
        }
    }
});


jQuery(document).ready(function($) {
    doaj.adminRISSearch.init();
});
