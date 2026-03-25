doaj.adminReportsSearch = {
    activeEdges : {},

    init : function(params) {
        if (!params) { params = {} }

        var selector = params.selector || "#reports";

        var e = doaj.components.makeSearch({
            selector: selector,
            searchUrl: doaj.edgeUtil.url.build(doaj.adminReportsSearchConfig.searchPath),
            facets: [
                doaj.components.refiningAndFacet({id: "requester", field: "requester.exact", display: "Produced By", deactivateThreshold: 1}),
                edges.newDateHistogramSelector({
                    id: "generated_date",
                    category: "facet",
                    field: "generated_date",
                    interval: "month",
                    display: "Generated Date",
                    displayFormatter: function(val) {
                        let date = new Date(parseInt(val));
                        return date.toLocaleString('default', {month: 'long', year: 'numeric', timeZone: "UTC"});
                    },
                    sortFunction: function(values) {
                        values.reverse();
                        return values;
                    },
                    renderer: edges.bs3.newDateHistogramSelectorRenderer({
                        countFormat: doaj.valueMaps.countFormat,
                        hideInactive: true
                    })
                })
            ],
            sortOptions: [
                {'display': 'Generated Date', 'field': 'generated_date'},
                {'display': 'Report Name', 'field': 'name.exact'}
            ],
            fieldOptions: [
                {'display': 'Requested by', 'field': 'requester'},
                {'display': 'Report Name', 'field': 'name'},
                {'display': 'Filename', 'field': 'filename'}
            ],
            searchPlaceholder: "Search All Reports",
            resultsDisplay: edges.newResultsDisplay({
                id: "results",
                category: "results",
                renderer: edges.bs3.newResultsFieldsByRowRenderer({
                    rowDisplay: [
                        [
                            {pre: "<strong>", field: "name", post: "</strong>"},
                            {
                                pre: " <strong>(",
                                field: "generated_date",
                                post: ")</strong>",
                                valueFunction: function(val, resultobj, renderer) {
                                    return doaj.humanDateTime(val);
                                }
                            }
                        ],
                        [
                            {pre: "A <strong>", field: "model", post: "</strong> report "},
                            {pre: "requested by <strong>", field: "requester", post: "</strong>"},
                            {
                                pre: " on <strong> ",
                                field: "request_date",
                                post: "</strong>",
                                valueFunction: function(val, resultobj, renderer) {
                                    return doaj.humanDateTime(val);
                                }
                            },
                            {
                                pre: " and generated on <strong> ",
                                field: "generated_date",
                                post: "</strong>",
                                valueFunction: function(val, resultobj, renderer) {
                                    return doaj.humanDateTime(val);
                                }
                            }
                        ],
                        [
                            {
                                field: "constraints",
                                valueFunction: function(val, res, component) {
                                    let modelMap = {
                                        "journal": "/admin",
                                        "application": "/admin/applications"
                                    };
                                    let route = modelMap[res.model];
                                    if (route === undefined) {
                                        route = "/admin";
                                    }
                                    return `<a href="${route}?source=${val}">Search again</a> `;
                                }
                            },
                            {
                                field: "id",
                                valueFunction: function(val, res, component) {
                                    return `<a href="/admin/report/${val}">Download report</a>`;
                                }
                            }
                        ]
                    ]
                })
            }),
            fieldDisplays: {
                "requester.exact": "Requested By",
                "generated_date": "Generated Date"
            },
            rangeFunctions: {
                "generated_date": doaj.valueMaps.displayYearMonthPeriod
            },
            openingQuery: es.newQuery({
                sort: [{field: "generated_date", order: "desc"}],
                size: 25
            })
        });

        doaj.adminReportsSearch.activeEdges[selector] = e;
    }
}

jQuery(document).ready(function($) {
    doaj.adminReportsSearch.init();
});
