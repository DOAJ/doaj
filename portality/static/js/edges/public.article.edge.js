$.extend(true, doaj, {

    publicSearch : {
        activeEdges : {},

        embedSnippet : function(renderer) {
            var snip = `<script type="text/javascript">
  var SEARCH_CONFIGURED_OPTIONS={{QUERY}}
</script>
<script src="https://doaj.org/static/widget/fixed_query.js" type="text/javascript"></script>
<div id="doaj-fixed-query-widget"></div>`;

            var query = renderer.component.edge.cloneQuery();
            query.addMust(es.newTermFilter({field: "_type", value: "article"}))
            query = query.objectify({
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

            var selector = params.selector || "#public-article-search";
            var search_url = current_scheme + "//" + current_domain + doaj.publicSearchConfig.publicSearchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                doaj.components.searchingNotification(),

                edges.newFullSearchController({
                    id: "search-input-bar",
                    category: "controller",
                    fieldOptions : [
                        {'display':'Title','field':'bibjson.title'},
                        {'display':'Abstract','field':'bibjson.abstract'},
                        {'display':'Keywords','field':'bibjson.keywords'},
                        {'display':'Subject','field':'index.classification'},
                        {'display':'Author','field':'bibjson.author.name'},
                        {'display':'ORCID','field':'bibjson.author.orcid_id'},
                        {'display':'DOI', 'field' : 'bibjson.identifier.id'},
                        {'display':'Language','field':'index.language'}
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
                        suffix: " indexed articles",
                        htmlContainerWrapper: false
                    })
                }),

                // Subject Browser
                ///////////////////////////////////
                doaj.components.subjectBrowser({
                    tree: doaj.publicSearchConfig.lccTree
                }),

                edges.newORTermSelector({
                    id: "journals",
                    category: "facet",
                    field: "bibjson.journal.title.exact",
                    display: "Journals",
                    size: 100,
                    syncCounts: false,
                    lifecycle: "update",
                    updateType: "fresh",
                    orderBy: "count",
                    orderDir: "desc",
                    renderer : doaj.renderers.newORTermSelectorRenderer({
                        showCount: true,
                        hideEmpty: true,
                        open: false,
                        togglable: true
                    })
                }),

                edges.newDateHistogramSelector({
                    id : "year_published",
                    category: "facet",
                    field: "index.date",
                    interval: "year",
                    display: "Year of publication",
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
                        hideInactive: false,
                        hideEmpty: true
                    })
                }),

                edges.newORTermSelector({
                    id: "seal",
                    category: "facet",
                    field: "index.has_seal.exact",
                    display: "Journal has the Seal",
                    syncCounts: false,
                    lifecycle: "update",
                    orderBy: "count",
                    orderDir: "desc",
                    renderer : doaj.renderers.newORTermSelectorRenderer({
                        showCount: true,
                        hideEmpty: false,
                        open: false,
                        togglable: true
                    })
                }),

                edges.newFullSearchController({
                    id: "share_embed",
                    category: "controller",
                    urlShortener : doaj.bitlyShortener,
                    embedSnippet : doaj.publicSearch.embedSnippet,
                    renderer: doaj.renderers.newShareEmbedRenderer({
                        shareLinkText: '<span data-feather="share-2" aria-hidden="true"></span> Share or embed'
                    })
                }),

                edges.newFullSearchController({
                    id: "sort_by",
                    category: "controller",
                    sortOptions : [
                        {'display':'Added to DOAJ (newest first)','field':'created_date', "dir" : "desc"},
                        {'display':'Added to DOAJ (oldest first)','field':'created_date', "dir" : "asc"},
                        {'display':'Publication date (most recent first)','field':'index.date', "dir" : "desc"},
                        {'display':'Publication date (less recent first)','field':'index.date', "dir" : "asc"},
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

                // selected filters display, with all the fields given their display names
                edges.newSelectedFilters({
                    id: "selected-filters",
                    category: "selected-filters",
                    fieldDisplays : {
                        "index.schema_codes_tree.exact" : "Subject",
                        "bibjson.journal.title.exact" : "Journal",
                        "index.date" : "Year of publication",
                        "index.has_seal.exact" : "Journal has the Seal"
                    },
                    rangeFunctions : {
                        "index.date" : doaj.valueMaps.displayYearPeriod
                    },
                    valueFunctions : {
                        "index.schema_codes_tree.exact" : doaj.valueMaps.schemaCodeToNameClosure(doaj.publicSearchConfig.lccTree)
                    },
                    renderer : doaj.renderers.newSelectedFiltersRenderer({})
                }),

                edges.newPager({
                    id: "top-pager",
                    category: "top-pager",
                    renderer : doaj.renderers.newPagerRenderer({
                        numberFormat: countFormat
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
                        numberFormat: countFormat
                    })
                })
            ];

            var e = edges.newEdge({
                selector: selector,
                template: doaj.templates.newPublicSearch({
                    title: "Articles"
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
