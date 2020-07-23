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
                    renderer : doaj.renderers.newFullSearchControllerRenderer({
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
                        suffix: " indexed journals"
                    })
                }),

                edges.newRefiningANDTermSelector({
                    id : "subject",
                    category: "facet",
                    field: "index.classification.exact",
                    display: "Subjects",
                    deactivateThreshold: 1,
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: false,
                        open: true,
                        togglable: false,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),

                edges.newRefiningANDTermSelector({
                    id : "language",
                    category: "facet",
                    field: "index.language.exact",
                    display: "Languages",
                    deactivateThreshold: 1,
                    active: false,
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),

                edges.newRefiningANDTermSelector({
                    id : "journal_licence",
                    category: "facet",
                    field: "index.license.exact",
                    display: "Licenses",
                    deactivateThreshold: 1,
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),

                edges.newRefiningANDTermSelector({
                    id : "publisher",
                    category: "facet",
                    field: "bibjson.publisher.name.exact",
                    display: "Publishers",
                    deactivateThreshold: 1,
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),

                edges.newRefiningANDTermSelector({
                    id : "country_publisher",
                    category: "facet",
                    field: "index.country.exact",
                    display: "Publishers' countries",
                    deactivateThreshold: 1,
                    active: false,
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        hideInactive: true,
                        countFormat: countFormat
                    })
                }),

                edges.newRefiningANDTermSelector({
                    id : "peer_review",
                    category: "facet",
                    field: "bibjson.editorial.review_process.exact",
                    display: "Peer review types",
                    ignoreEmptyString: true,
                    deactivateThreshold: 1,
                    active: false,
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),

                edges.newDateHistogramSelector({
                    id : "year_added",
                    category: "facet",
                    field: "created_date",
                    interval: "year",
                    display: "Date added",
                    active: false,
                    displayFormatter : function(val) {
                        return (new Date(parseInt(val))).getUTCFullYear();
                    },
                    sortFunction : function(values) {
                        values.reverse();
                        return values;
                    },
                    renderer : edges.bs3.newDateHistogramSelectorRenderer({
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
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
                    renderer : edges.bs3.newPagerRenderer({
                        sizeOptions: [50, 100, 200],
                        sizePrefix: "Results per page",
                        sizeSuffix: "",
                        showRecordCount: false,
                        showPageNavigation: false
                    })
                }),

                edges.newPager({
                    id: "top-pager",
                    category: "top-pager",
                    renderer : edges.bs3.newPagerRenderer({
                        showSizeSelector: false,
                        showRecordCount: false,
                        numberFormat: countFormat,
                        scrollSelector: "html, body"
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
                    renderer : edges.bs3.newPagerRenderer({
                        showSizeSelector: false,
                        showRecordCount: false,
                        numberFormat: countFormat,
                        scrollSelector: "html, body"
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