// ~~ AdminAlerts:Edge ~~
// ~~-> Edges:Technology ~~
doaj.adminRISSearch = {
    activeEdges : {},

    init : function(params) {
        if (!params) { params = {} }

        var selector = params.selector || "#ris";

        var e = doaj.components.makeSearch({
            selector: selector,
            searchUrl: doaj.edgeUtil.url.build(doaj.adminRISSearchConfig.searchPath),
            sortOptions: [
                {'display': 'Created Date', 'field': 'created_date'},
                {'display': 'Last Updated', 'field': 'last_updated'}
            ],
            searchPlaceholder: "Search All RIS Exports",
            resultsDisplay: edges.newResultsDisplay({
                id: "results",
                category: "results",
                renderer: edges.bs3.newResultsFieldsByRowRenderer({
                    noResultsText: "No RIS exports match the selected criteria.",
                    rowDisplay: [
                        [{field: "created_date", pre: "Created Date: "}],
                        [{field: "created_date", pre: "Last Updated: "}],
                        [{field: "id", pre: "Article ID: "}],
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
            }),
            openingQuery: es.newQuery({
                sort: [{field: "last_updated", order: "desc"}],
                size: 25
            }),
            callbacks: {
                "edges:post-render": function() {
                    let resultsComponent = doaj.adminRISSearch.activeEdges[selector].getComponent({id: "results"});

                    let deleteSelector = edges.css_class_selector(resultsComponent.renderer.namespace, "delete");
                    $(deleteSelector).on("click", function(e) {
                        e.preventDefault();
                        let a = e.currentTarget;
                        let id = a.getAttribute("data-id");
                        let proceed = confirm("Deleting the RIS export will cause it to be regenerated the next time it is requested, or the regular RIS export runs")
                        if (!proceed) { return; }
                        $.ajax({
                            method: "POST",
                            url: "/admin/ris/" + id + "/delete",
                            success: function(data) {
                                alert("Deleted successfully, reload the page to see the changes");
                            },
                            error: function(xhr, status, error) {
                                alert("There was an unexpected error processing your request.");
                            }
                        })
                    });

                    let regenerateSelector = edges.css_class_selector(resultsComponent.renderer.namespace, "regenerate");
                    $(regenerateSelector).on("click", function(e) {
                        e.preventDefault();
                        let a = e.currentTarget;
                        let id = a.getAttribute("data-id");
                        let proceed = confirm("Regenerate the RIS Export?")
                        if (!proceed) { return; }
                        $.ajax({
                            method: "POST",
                            url: "/admin/ris/" + id + "/regenerate",
                            success: function(data) {
                                alert("Regenerated successfully, reload the page to see the changes");
                            },
                            error: function(xhr, status, error) {
                                alert("There was an unexpected error processing your request.");
                            }
                        })
                    });
                }
            }
        });

        doaj.adminRISSearch.activeEdges[selector] = e;
    }
}

jQuery(document).ready(function($) {
    doaj.adminRISSearch.init();
});
