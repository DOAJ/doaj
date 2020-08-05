jQuery(document).ready(function($) {

    //////////////////////////////////////////////////////
    // test loading static files

    e4 = edges.newEdge({
        selector: "#statics",
        search_url: "http://localhost:9200/wna/reactor/_search",
        staticFiles : [
            {
                id: "mycsv",
                url: "http://localhost:5029/static/vendor/edges/docs/static.csv",
                datatype: "text"
            }
        ],
        components: []
    });
    e4.loadStaticFiles();

    //////////////////////////////////////////////////////////////
    // this stuff tests the building of a complicated query

    d = false;
    function cb(data) {
        d = data;
    }

    q = es.newQuery({
        filtered: true,
        size : 12,
        from : 1,
        queryString: {queryString: "UCL:University College London", defaultOperator: "AND", defaultField: "monitor.jm:apc.name"},
        sort : {field: "id", order: "asc"},
        fields: ["id"],
        aggs : [
            es.newTermsAggregation({
                name : "richard",
                field: "monitor.jm:apc.name.exact",
                size: 4,
                orderBy: "term",
                orderDir: "asc",
                aggs : [
                    es.newRangeAggregation({
                        name: "jones",
                        field : "monitor.jm:apc.amount_gbp",
                        ranges: [
                            {to: 1000},
                            {from: 1000, to: 2000},
                            {from: 2000}
                        ]
                    })
                ]
            }),
            es.newStatsAggregation({
                name: "david",
                field : "monitor.jm:apc.amount_gbp"
            }),
            es.newDateHistogramAggregation({
                name: "hist",
                field : "created_date",
                format: "yyyy-MM-dd"
            })
        ],
        must : [
            es.newTermFilter({
                field: "monitor.rioxxterms:project.name.exact",
                value: "EPSRC"
            }),
            es.newTermsFilter({
                field: "monitor.ali:license_ref.exact",
                values: ["CC-BY"]
            }),
            es.newRangeFilter({
                field: "monitor.jm:apc.amount_gbp",
                lt: 2300,
                gte: 900
            })
        ]
    });

    o = q.objectify();

    es.doQuery({
        search_url: "http://localhost:9200/allapc/institutional/_search",
        queryobj: q.objectify(),
        datatype: "jsonp",
        success: cb

    });

    ///////////////////////////////////////////////////
    // test parsing of a query

    raw = {
        query: {
            filtered : {
                filter: {
                    bool: {
                        must : [
                            {term: {"monitor.rioxxterms:project.name.exact" : "EPSRC"}},
                            {terms: {"monitor.jm:apc.amount_gbp" : ["CC-BY"]}},
                            {
                                range: {
                                    "monitor.jm:apc.amount_gbp" : {
                                        lt: 2300,
                                        gte: 900
                                    }
                                }
                            }
                        ]
                    }
                },
                query: {
                    query_string: {query: "UCL: University College London", default_field: "monitor.jm:apc.name.exact", default_operator: "AND" }
                }
            }
        },
        size: 12,
        from: 2,
        fields: ["id"],
        sort: [
            {id: {order: "asc"}}
        ],
        aggs : {
            richard: {
                terms: {
                    field: "monitor.jm:apc.name.exact",
                    size: 4,
                    order: {_term : "asc"}
                },
                aggs : {
                    jones: {
                        range: {
                            field: "monitor.jm:apc.amount_gbp",
                            ranges: [
                                {to: 1000},
                                {from: 1000, to: 2000},
                                {from: 2000}
                            ]
                        }
                    }
                }
            },
            david : {
                stats : {
                    field: "monitor.jm:apc.amount_gbp"
                }
            },
            hist: {
                date_histogram: {
                    field: "created_date",
                    format: "yyyy-MM-dd"
                }
            }
        }
    };
    q2 = es.newQuery({raw: raw});

    o2 = q2.objectify();

    //////////////////////////////////////////////////
    // this generates the basic facetview style page

    e2 = edges.newEdge({
        selector: "#facetview",
        template: edges.bs3.newFacetview(),
        search_url: "http://localhost:9200/doaj/article/_search",
        manageUrl : false,  // FIXME: pushState being odd
        baseQuery : es.newQuery({
            must: [es.newTermFilter({field: "index.classification.exact", value: "Medicine"})]
        }),
        openingQuery : es.newQuery({
            size : 12,
            queryString: {queryString: "obese", defaultOperator: "OR", defaultField: "index.unpunctitle"},
            sort : {field: "index.publisher.exact", order: "asc"}
        }),
        components : [
            edges.newRefiningANDTermSelector({
                id: "publisher",
                field: "index.publisher.exact",
                display: "Publisher",
                size: 10,
                category: "facet"
            }),
            edges.newRefiningANDTermSelector({
                id: "subject",
                field: "index.classification.exact",
                display: "Subject",
                size: 10,
                category: "facet"
            }),
            edges.newORTermSelector({
                id: "country",
                field : "index.country.exact",
                display: "Country",
                size: 200,
                category: "facet",
                renderer : edges.bs3.newORTermSelectorRenderer({
                    showCount: true
                })
            }),
            edges.newFullSearchController({
                id: "search-controller",
                category: "controller",
                sortOptions : [
                    {field: "index.asciiunpunctitle.exact", display: "Title"},
                    {field: "index.publisher.exact", display: "Publisher"}
                ],
                fieldOptions : [
                    {field: "index.unpunctitle", display: "Title"},
                    {field: "index.publisher", display: "Publisher"}
                ]
            }),
            edges.newSelectedFilters({
                id: "selected-filters",
                category: "selected-filters",
                fieldDisplays : {
                    "index.publisher.exact" : "Publisher",
                    "index.classification.exact" : "Classification",
                    "index.country.exact" : "Country"
                }
            }),
            edges.newPager({
                id: "top-pager",
                category: "top-pager"
            }),
            edges.newPager({
                id: "bottom-pager",
                category: "bottom-pager"
            }),
            edges.newSearchingNotification({
                id: "searching-notification",
                category: "searching-notification"
            }),
            edges.newResultsDisplay({
                id: "results",
                category: "results",
                renderer : edges.bs3.newResultsDisplayRenderer({
                    fieldDisplayMap: [
                        {field: "id", display: "ID"},
                        {field: "bibjson.title", display: "Title"}
                    ]
                })
            })
        ]
    });

    $("#facetview").on("edges:pre-query", function(event) {
        var obj = e2.urlQueryArg();
        var key = Object.keys(obj);
        var url = "example.html?" + key + "=" + obj[key];
        $("#managed-url").attr("href", url).html(url);
    });

    ///////////////////////////////////////////////////
    // this stuff generates the demo apc report

    function earliestDate() {
        return new Date(0);
    }

    function latestDate() {
        return new Date();
    }

    var base_query = es.newQuery();
    base_query.addAggregation(
        es.newTermsAggregation({
            name : "apc_count",
            field : "monitor.dcterms:publisher.name.exact",
            size : 10,
            aggs : [
                es.newStatsAggregation({
                    name : "publisher_stats",
                    field: "monitor.jm:apc.amount_gbp"
                })
            ]
        })
    );

    e = edges.newEdge({
        selector: "#edges",
        template: edges.bs3.newTabbed(),
        search_url: "http://localhost:9200/allapc/institutional/_search",
        baseQuery : base_query,
        components: [
            edges.newSelectedFilters({
                id: "selected-filters",
                fieldDisplays : {
                    "monitor.jm:apc.name.exact" : "Institution",
                    "monitor.jm:apc.amount_gbp" : "APC"
                },
                rangeMaps : {
                    "monitor.jm:apc.amount_gbp": [
                        {to: 500, display: "< 500"},
                        {from: 500, to: 1000, display: "500 -> 1000"},
                        {from: 1000, to: 2500, display: "1000 -> 2500"},
                        {from: 2500, display: "2500+"}
                    ]
                },
                category: "top"
            }),
            edges.newMultiDateRangeEntry({
                id : "date_range",
                fields : [
                    {field : "monitor.rioxxterms:publication_date", display: "Publication Date"},
                    {field : "monitor.jm:dateApplied", display: "APC Application"},
                    {field : "monitor.jm:apc.date_paid", display: "APC Paid"}
                ],
                earliest : {
                    "monitor.rioxxterms:publication_date" : earliestDate,
                    "monitor.jm:dateApplied" : earliestDate,
                    "monitor.jm:apc.date_paid" : earliestDate
                },
                latest : {
                    "monitor.rioxxterms:publication_date" : latestDate,
                    "monitor.jm:dateApplied" : latestDate,
                    "monitor.jm:apc.date_paid" : latestDate
                },
                category : "lhs"
            }),
            edges.newAutocompleteTermSelector({
                id : "publisher",
                field : "monitor.dcterms:publisher.name.exact",
                display : "Choose publishers to display",
                category: "lhs"
            }),
            edges.newRefiningANDTermSelector({
                id: "institution",
                field: "monitor.jm:apc.name.exact",
                display: "Limit by Institution",
                size: 15,
                category: "lhs"
            }),
            edges.newBasicRangeSelector({
                id : "gbp",
                field: "monitor.jm:apc.amount_gbp",
                display: "APC Amount",
                ranges: [
                    {to: 500, display: "< 500"},
                    {from: 500, to: 1000, display: "500 -> 1000"},
                    {from: 1000, to: 2500, display: "1000 -> 2500"},
                    {from: 2500, display: "2500+"}
                ],
                category: "lhs"
            }),
            edges.newNumericRangeEntry({
                id: "apc",
                field: "monitor.jm:apc.amount_gbp",
                display: "APC Range",
                increment: 1000,
                category: "lhs"
            }),
            edges.newSimpleLineChart({
                id: "line_chart",
                display: "Line Chart",
                dataSeries: [
                    {
                        key: "Series 1",
                        values: [
                            {label: 1980, value: 100},
                            {label: 1981, value: 120},
                            {label: 1982, value: 122},
                            {label: 1983, value: 130}
                        ]
                    },
                    {
                        key: "Series 2",
                        values: [
                            {label: 1980, value: 200},
                            {label: 1981, value: 220},
                            {label: 1982, value: 222},
                            {label: 1983, value: 230}
                        ]
                    }
                ],
                category: "tab",
                renderer : edges.nvd3.newSimpleLineChartRenderer({
                    xTickFormat: '.0f',
                    yTickFormat: ',.0f'
                })
            }),
            edges.newMultibar({
                id: "apc_count",
                display: "APC Count",
                dataFunction: edges.ChartDataFunctions.terms({
                    useAggregations : ["apc_count"],
                    seriesKeys : {
                        "apc_count" : "Number of APCs paid"
                    }
                }),
                category : "tab"
            })/*,
            edges.newHorizontalMultibar({
                id: "total_expenditure",
                display: "Total Expenditure",
                dataFunction : edges.ChartDataFunctions.termsStats({
                    useAggregations : ["apc_count publisher_stats"],  // the path to the stats in the terms, separated by space
                    seriesFor : ["sum"],
                    seriesKeys : {
                        "apc_count publisher_stats sum" : "Total Expenditure"
                    }
                }),
                category : "tab"
            }),
            edges.newHorizontalMultibar({
                id: "min_max_mean",
                display: "Min, Max, Mean",
                dataFunction : edges.ChartDataFunctions.termsStats({
                    useAggregations : ["apc_count publisher_stats"],
                    seriesFor : ["min", "max", "avg"],
                    seriesKeys : {
                        "apc_count publisher_stats min" : "Minimum",
                        "apc_count publisher_stats max" : "Maximum",
                        "apc_count publisher_stats avg" : "Mean"
                    }
                }),
                category : "tab"
            })*/
        ]
    });

    e3 = edges.newEdge({
        selector: "#wna",
        search_url: "http://localhost:9200/wna/reactor/_search",
        baseQuery: es.newQuery({
            must: [es.newTermFilter({field: "id.exact", value: "03df21226fb943a495b793812f65e0c9"})]
        }),
        components: [
            edges.newMapView({
                id: "map-canvas",
                renderer : edges.google.newMapViewRenderer({
                    initialZoom: 15
                })
            })
        ]
    });
});