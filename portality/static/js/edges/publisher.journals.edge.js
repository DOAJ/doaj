$.extend(true, doaj, {

    publisherJournalsSearch : {
        activeEdges : {},

        makeUpdateRequest : function (resultobj) {
            if (resultobj.admin && resultobj.admin.hasOwnProperty("in_doaj")) {
                if (resultobj.admin.in_doaj === false) {
                    return false;
                }
            }

            var result = {label : "", link : ""};
            if (resultobj.admin && resultobj.admin.current_application) {
                var idquery = '%7B%22query%22%3A%7B%22query_string%22%3A%7B%22query%22%3A%22' + resultobj['id'] + '%22%7D%7D%7D';
                result.link = doaj.publisherJournalsSearchConfig.journalUpdateRequestsUrl + "?source=" + idquery;
                result.label = 'View Update';
            } else {
                result.link = doaj.publisherJournalsSearchConfig.journalUpdateUrl + resultobj['id'];
                result.label = 'Update';
            }
            return result;
        },

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#publisher_journals";
            var search_url = current_scheme + "//" + current_domain + doaj.publisherJournalsSearchConfig.searchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                edges.newPager({
                    id: "result-count",
                    category: "pager",
                    renderer : edges.bs3.newResultCountRenderer({
                        countFormat: countFormat,
                        suffix: " indexed journals",
                        htmlContainerWrapper: false
                    })
                }),

                // edges.newFilterSetter({
                //     id : "see_journals",
                //     category: "facet",
                //     filters : [
                //         {
                //             id: "with_seal",
                //             display: "With a DOAJ Seal&nbsp;&nbsp;<span data-feather=\"check-circle\" aria-hidden=\"true\"></span>",
                //             must : [
                //                 es.newTermFilter({
                //                     field: "index.has_seal.exact",
                //                     value: "Yes"
                //                 })
                //             ]
                //         },
                //         {
                //             id : "no_charges",
                //             display: "Without APCs or other fees",
                //             must : [
                //                 es.newTermFilter({
                //                     field: "bibjson.apc.has_apc",
                //                     value: false
                //                 }),
                //                 es.newTermFilter({
                //                     field: "bibjson.other_charges.has_other_charges",
                //                     value: false
                //                 })
                //             ]
                //         }
                //     ],
                //     renderer : doaj.renderers.newFacetFilterSetterRenderer({
                //         facetTitle : "See journals...",
                //         open: true,
                //         togglable: false,
                //         showCount: false
                //     })
                // }),

                edges.newORTermSelector({
                    id: "journal_licence",
                    category: "facet",
                    field: "index.license.exact",
                    display: "Licenses",
                    size: 99,
                    syncCounts: false,
                    lifecycle: "update",
                    renderer : doaj.renderers.newORTermSelectorRenderer({
                        showCount: true,
                        hideEmpty: false,
                        open: false,
                        togglable: true
                    })
                }),

                // FIXME: this is an approximation of the subject selector that we actually want, just to get the
                // ball rolling
                edges.newORTermSelector({
                    id: "subject",
                    category: "facet",
                    field: "index.classification.exact",
                    display: "Subjects",
                    size: 40,
                    syncCounts: false,
                    lifecycle: "static",
                    renderer : doaj.renderers.newORTermSelectorRenderer({
                        showCount: false,
                        hideEmpty: false,
                        open: true,
                        togglable: false
                    })
                }),

                edges.newORTermSelector({
                    id: "keywords",
                    category: "facet",
                    field: "bibjson.keywords.exact",
                    display: "Keywords",
                    size: 99,
                    syncCounts: false,
                    lifecycle: "update",
                    renderer : doaj.renderers.newORTermSelectorRenderer({
                        showCount: true,
                        hideEmpty: false,
                        open: false,
                        togglable: true
                    })
                }),

                // edges.newORTermSelector({
                //     id: "language",
                //     category: "facet",
                //     field: "index.language.exact",
                //     display: "Languages",
                //     size: 40,
                //     syncCounts: false,
                //     lifecycle: "update",
                //     orderBy: "count",
                //     orderDir: "desc",
                //     renderer : doaj.renderers.newORTermSelectorRenderer({
                //         showCount: true,
                //         hideEmpty: false,
                //         open: false,
                //         togglable: true
                //     })
                // }),



                // edges.newORTermSelector({
                //     id: "publisher",
                //     category: "facet",
                //     field: "bibjson.publisher.name.exact",
                //     display: "Publishers",
                //     size: 40,
                //     syncCounts: false,
                //     lifecycle: "update",
                //     orderBy: "count",
                //     orderDir: "desc",
                //     renderer : doaj.renderers.newORTermSelectorRenderer({
                //         showCount: true,
                //         hideEmpty: false,
                //         open: false,
                //         togglable: true
                //     })
                // }),

                // edges.newORTermSelector({
                //     id: "country_publisher",
                //     category: "facet",
                //     field: "index.country.exact",
                //     display: "Publishers' countries",
                //     size: 40,
                //     syncCounts: false,
                //     lifecycle: "update",
                //     orderBy: "count",
                //     orderDir: "desc",
                //     renderer : doaj.renderers.newORTermSelectorRenderer({
                //         showCount: true,
                //         hideEmpty: false,
                //         open: false,
                //         togglable: true
                //     })
                // }),

                // edges.newORTermSelector({
                //     id: "peer_review",
                //     category: "facet",
                //     field: "bibjson.editorial.review_process.exact",
                //     display: "Peer review types",
                //     size: 99,
                //     syncCounts: false,
                //     lifecycle: "update",
                //     renderer : doaj.renderers.newORTermSelectorRenderer({
                //         showCount: true,
                //         hideEmpty: false,
                //         open: false,
                //         togglable: true
                //     })
                // }),

                // edges.newDateHistogramSelector({
                //     id : "year_added",
                //     category: "facet",
                //     field: "created_date",
                //     interval: "year",
                //     display: "Date added",
                //     displayFormatter : function(val) {
                //         return (new Date(parseInt(val))).getUTCFullYear();
                //     },
                //     sortFunction : function(values) {
                //         values.reverse();
                //         return values;
                //     },
                //     renderer : doaj.renderers.newDateHistogramSelectorRenderer({
                //         open: false,
                //         togglable: true,
                //         countFormat: countFormat,
                //         hideInactive: false
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

                edges.newPager({
                    id: "rpp",
                    category: "pager",
                    renderer : doaj.renderers.newPageSizeRenderer({
                        sizeOptions: [50, 100, 200],
                        sizeLabel: "Results per page"
                    })
                }),

                // selected filters display, with all the fields given their display names
                edges.newSelectedFilters({
                    id: "selected-filters",
                    category: "selected-filters",
                    compoundDisplays : [
                        {
                            filters : [
                                es.newTermFilter({
                                    field: "bibjson.apc.has_apc",
                                    value: false
                                }),
                                es.newTermFilter({
                                    field: "bibjson.other_charges.has_other_charges",
                                    value: false
                                })
                            ],
                            display : "Without APCs or other fees"
                        }
                    ],
                    fieldDisplays : {
                        "index.has_seal.exact" : "With a DOAJ Seal",
                        "index.classification.exact" : "Subjects",
                        "index.license.exact" : "Licenses",
                        "bibjson.publisher.name.exact" : "Publishers",
                        "index.country.exact" : "Publishers' countries",
                        "index.language.exact" : "Languages",
                        "bibjson.editorial.review_process.exact" : "Peer review",
                        "created_date" : "Date added"
                    },
                    rangeFunctions : {
                        "created_date" : doaj.valueMaps.displayYearPeriod
                    },
                    renderer : doaj.renderers.newSelectedFiltersRenderer({
                        hideValues : [
                            "index.has_seal.exact"
                        ],
                        omit : [
                            "bibjson.apc.has_apc",
                            "bibjson.other_charges.has_other_charges"
                        ]
                    })
                }),

                edges.newPager({
                    id: "top-pager",
                    category: "top-pager",
                    renderer : doaj.renderers.newPagerRenderer({
                        numberFormat: countFormat,
                        scrollSelector: "#top-pager"
                    })
                }),

                // results display
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer : doaj.renderers.newPublicSearchResultRenderer({
                        actions: [
                            doaj.publisherJournalsSearch.makeUpdateRequest
                        ]
                    })
                }),

                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer : doaj.renderers.newPagerRenderer({
                        numberFormat: countFormat,
                        scrollSelector: "#top-pager"    // FIXME: these selectors don't work, why not?
                    })
                })
            ];

            var e = edges.newEdge({
                selector: selector,
                template: doaj.templates.newPublicSearch({
                    titleBar: false,
                    title: "Journals"
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
            doaj.publisherJournalsSearch.activeEdges[selector] = e;
        }
    }
});


jQuery(document).ready(function($) {
    doaj.publisherJournalsSearch.init();
});
