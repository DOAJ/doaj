$.extend(true, doaj, {

    publicSearch : {
        activeEdges : {},

        embedSnippet : function(renderer) {
            var snip = '<script type="text/javascript">!window.jQuery && document.write("<scr" + "ipt type=\"text/javascript\" src=\"http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js\"></scr" + "ipt>"); </script><script type="text/javascript">var doaj_url="https://doaj.org"; var SEARCH_CONFIGURED_OPTIONS={{QUERY}}</script><script src="https://doaj.org/static/widget/fixed_query.js" type="text/javascript"></script><div id="doaj-fixed-query-widget"></div></div>';
            var query = renderer.component.edge.currentQuery.objectify({
                        include_query_string : true,
                        include_filters : true,
                        include_paging : true,
                        include_sort : true,
                        include_fields : false,
                        include_aggregations : false
                    });
            snip = snip.replace(/{{QUERY}}/g, JSON.stringify(query));
            return snip;
        },

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#public-journal-search";
            var search_url = current_scheme + "//" + current_domain + doaj.publicSearchConfig.publicSearchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                edges.newFullSearchController({
                    id: "search-journal-bar",
                    category: "controller",
                    fieldOptions : [
                        {'display':'Title','field':'bibjson.title'},
                        {'display':'Keywords','field':'bibjson.keywords'},
                        {'display':'Subject','field':'index.classification'},
                        {'display':'ISSN', 'field':'index.issn.exact'},
                        {'display':'Publisher','field':'bibjson.publisher.name'},
                        {'display':'Country of publisher','field':'index.country'},
                        {'display':'Journal Language','field':'index.language'}
                    ],
                    defaultOperator : "AND",
                    renderer : doaj.renderers.newSearchBarRenderer({
                        freetextSubmitDelay: -1,
                        clearButton: false,
                        searchButton: true,
                        searchPlaceholder: "",
                    })
                }),

                edges.newPager({
                    id: "result-count",
                    category: "pager",
                    renderer : edges.bs3.newResultCountRenderer({
                        countFormat: countFormat,
                        suffix: " indexed journals",
                        htmlContainerWrapper: false
                    })
                }),

                edges.newFilterSetter({
                    id : "see_journals",
                    category: "facet",
                    filters : [
                        {
                            id: "with_seal",
                            display: "With a DOAJ Seal&nbsp;&nbsp;<span data-feather=\"check-circle\" aria-hidden=\"true\"></span>",
                            must : [
                                es.newTermFilter({
                                    field: "index.has_seal.exact",
                                    value: "Yes"
                                })
                            ]
                        },
                        {
                            id : "no_charges",
                            display: "Without APCs or other fees",
                            must : [
                                es.newTermFilter({
                                    field: "bibjson.apc.has_apc",
                                    value: false
                                }),
                                es.newTermFilter({
                                    field: "bibjson.other_charges.has_other_charges",
                                    value: false
                                })
                            ]
                        }
                    ],
                    renderer : doaj.renderers.newFacetFilterSetterRenderer({
                        facetTitle : "See journals...",
                        open: true,
                        togglable: false,
                        showCount: false
                    })
                }),

                // FIXME: this is an approximation of the subject selector that we actually want, just to get the
                // ball rolling
                edges.newORTermSelector({
                    id: "subject",
                    category: "facet",
                    field: "index.classification.exact",
                    display: "Subjects",
                    size: 5000,
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
                    id: "language",
                    category: "facet",
                    field: "index.language.exact",
                    display: "Languages",
                    size: 999,
                    syncCounts: false,
                    lifecycle: "update",
                    renderer : doaj.renderers.newORTermSelectorRenderer({
                        showCount: true,
                        hideEmpty: false,
                        open: false,
                        togglable: true
                    })
                }),

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

                edges.newORTermSelector({
                    id: "publisher",
                    category: "facet",
                    field: "bibjson.publisher.name.exact",
                    display: "Publishers",
                    size: 9999,
                    syncCounts: false,
                    lifecycle: "update",
                    renderer : doaj.renderers.newORTermSelectorRenderer({
                        showCount: true,
                        hideEmpty: false,
                        open: false,
                        togglable: true
                    })
                }),

                edges.newORTermSelector({
                    id: "country_publisher",
                    category: "facet",
                    field: "index.country.exact",
                    display: "Publishers' countries",
                    size: 999,
                    syncCounts: false,
                    lifecycle: "update",
                    renderer : doaj.renderers.newORTermSelectorRenderer({
                        showCount: true,
                        hideEmpty: false,
                        open: false,
                        togglable: true
                    })
                }),

                edges.newORTermSelector({
                    id: "peer_review",
                    category: "facet",
                    field: "bibjson.editorial.review_process.exact",
                    display: "Peer review types",
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

                edges.newDateHistogramSelector({
                    id : "year_added",
                    category: "facet",
                    field: "created_date",
                    interval: "year",
                    display: "Date added",
                    displayFormatter : function(val) {
                        return (new Date(parseInt(val))).getUTCFullYear();
                    },
                    sortFunction : function(values) {
                        values.reverse();
                        return values;
                    },
                    renderer : doaj.renderers.newDateHistogramSelectorRenderer({
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: false
                    })
                }),

                edges.newFullSearchController({
                    id: "share_embed",
                    category: "controller",
                    urlShortener : doaj.bitlyShortener,
                    embedSnippet : doaj.publicSearch.embedSnippet,
                    renderer: doaj.renderers.newShareEmbedRenderer({
                        shareLinkText: '<span data-feather="share-2" aria-hidden="true"></span> Share | <span data-feather="code" aria-hidden="true"></span> Embed'
                    })
                }),

                edges.newFullSearchController({
                    id: "sort_by",
                    category: "controller",
                    sortOptions : [
                        {'display':'Added to DOAJ (newest first)','field':'created_date desc'},
                        {'display':'Added to DOAJ (oldest first)','field':'created_date asc'},
                        {'display':'Last updated (most recent first)','field':'last_updated desc'},
                        {'display':'Last updated (less recent first)','field':'last_updated asc'},
                        {'display':'Title (A-Z)','field':'index.unpunctitle.exact asc'},
                        {'display':'Title (Z-A)','field':'index.unpunctitle.exact desc'},
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
                    fieldDisplays : {
                        "index.has_seal.exact" : "With a DOAJ Seal",
                        "bibjson.apc.has_apc" : "Without APC",
                        "bibjson.other_charges.has_other_charges" : "Without other charges",
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
                    renderer : doaj.renderers.newSelectedFiltersRenderer({})
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
                    renderer : doaj.renderers.newPublicSearchResultRenderer()
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
                    title: "Journals"
                }),
                search_url: search_url,
                manageUrl : true,
                openingQuery: es.newQuery({
                    sort: [{"field" : "created_date", "order" : "desc"}],
                    size: 50
                }),
                components : components,
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
            doaj.publicSearch.activeEdges[selector] = e;
        }
    }

});

jQuery(document).ready(function($) {
    doaj.publicSearch.init();
});