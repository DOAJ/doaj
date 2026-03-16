// ~~ AdminAlerts:Edge ~~
// ~~-> Edges:Technology ~~

doaj.adminAlertsSearch = {

    activeEdges: {},

    init: function(params) {
        if (!params) { params = {} }

        var selector = params.selector || "#admin_alerts";

        var e = doaj.components.makeSearch({
            selector: selector,
            searchUrl: doaj.edgeUtil.url.build(doaj.adminAlertsSearchConfig.searchPath),
            facets: [
                doaj.components.refiningAndFacet({id: "source", field: "source.exact", display: "Source"}),
                doaj.components.refiningAndFacet({id: "state", field: "state.exact", display: "State", orderBy: "term", orderDir: "asc"}),
                doaj.components.monthDateHistogramFacet({id: "created_date", field: "created_date", display: "Date"})
            ],
            sortOptions: [
                {'display': 'Alert Date', 'field': 'created_date'}
            ],
            fieldOptions: [
                {'display': 'Message', 'field': 'message'},
                {'display': 'Source', 'field': 'source'}
            ],
            searchPlaceholder: "Search All Alerts",
            resultsDisplay: edges.newResultsDisplay({
                id: "results",
                category: "results",
                renderer: edges.bs3.newResultsFieldsByRowRenderer({
                    noResultsText: "Great news, there are no alerts!",
                    rowDisplay: [
                        [
                            { pre: "<strong>[", field: "state", post: "]</strong> " },
                            { pre: "From <strong>", field: "source", post: "</strong>" },
                            { pre: " at <strong> ", field: "created_date", post: "</strong>" }
                        ],
                        [
                            { pre: "<p>", field: "message", post: "</p>" }
                        ],
                        [
                            {
                                valueFunction: function(val, res) {
                                    let frag = "";
                                    if (res.audit) {
                                        frag += "<ul>";
                                        for (let audit of res.audit) {
                                            frag += `<li>[${audit.date}] ${audit.user}: "${audit.from_state}" to "${audit.to_state}"</li>`;
                                        }
                                        frag += "</ul>";
                                    }
                                    return frag;
                                }
                            }
                        ],
                        [
                            {
                                valueFunction: function(val, res, component) {
                                    let controlClass = edges.css_classes(component.namespace, "control");
                                    let in_progress = `<a class="button ${controlClass}" href="${doaj.adminAlertsSearchConfig.managePath}${res.id}/in_progress">Set In Progress</a>`;
                                    let resolved = `<a class="button ${controlClass}" href="${doaj.adminAlertsSearchConfig.managePath}${res.id}/closed">Mark Closed</a>`;
                                    let frag = "";
                                    if (res.state === "new") {
                                        frag = in_progress + " " + resolved;
                                    } else if (res.state === "in_progress") {
                                        frag = resolved;
                                    }
                                    return frag;
                                }
                            }
                        ]
                    ]
                })
            }),
            fieldDisplays: {
                "source.exact": "Source",
                "state.exact": "State",
                "created_date": "Alert Date"
            },
            rangeFunctions: {
                "created_date": doaj.valueMaps.displayYearMonthPeriod
            },
            openingQuery: es.newQuery({
                must: [es.newTermFilter({field: "state.exact", value: "new"})],
                sort: [{field: "created_date", order: "desc"}],
                size: 25
            }),
            callbacks: {
                "edges:post-render": function() {
                    let resultsComponent = doaj.adminAlertsSearch.activeEdges[selector].getComponent({id: "results"});
                    let controllSelector = edges.css_class_selector(resultsComponent.renderer.namespace, "control");
                    $(controllSelector).on("click", function(e) {
                        e.preventDefault();
                        let link = e.currentTarget.getAttribute("href");
                        $.ajax({
                            method: "POST",
                            url: link,
                            success: function() {
                                alert("Updated successfully, reload the page to see the changes");
                            },
                            error: function() {
                                alert("There was an unexpected error processing your request.");
                            }
                        })
                    })
                }
            }
        });

        doaj.adminAlertsSearch.activeEdges[selector] = e;
    }
};

jQuery(document).ready(function() {
    doaj.adminAlertsSearch.init();
});
