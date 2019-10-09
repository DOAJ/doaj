$.extend(true, doaj, {

    publicToC : {
        activeEdges : {},

        dynamicFacets : {
            volume : [
                "issue"
            ],
            year_published : [
                "month_published"
            ]
        },

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

        displayYearPeriod : function(params) {
            var from = params.from;
            var to = params.to;
            var field = params.field;
            var display = (new Date(parseInt(from))).getUTCFullYear();
            return {to: to, toType: "lt", from: from, fromType: "gte", display: display}
        },

        displayMonthPeriod : function(params) {
            var from = params.from;
            var to = params.to;
            var field = params.field;
            var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            var mi = (new Date(parseInt(from))).getUTCMonth();
            return {to: to, toType: "lt", from: from, fromType: "gte", display: months[mi]}
        },

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#journal_toc_articles";
            var search_url = current_scheme + "//" + current_domain + doaj.publicToCConfig.publicSearchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [

                edges.newRefiningANDTermSelector({
                    id : "volume",
                    category: "facet",
                    field: "bibjson.journal.volume.exact",
                    display: "Volume",
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
                    id : "issue",
                    category: "facet",
                    field: "bibjson.journal.number.exact",
                    display: "Issue",
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
                    id : "year_published",
                    category: "facet",
                    field: "index.date",
                    interval: "year",
                    display: "Year",
                    deactivateThreshold: 1,
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
                        hideInactive: true,
                        shortDisplay: 15
                    })
                }),
                edges.newDateHistogramSelector({
                    id : "month_published",
                    category: "facet",
                    field: "index.date_toc_fv_month",
                    interval: "month",
                    display: "Month",
                    deactivateThreshold: 1,
                    active: false,
                    displayFormatter : function(val) {
                        var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                        var mi = (new Date(parseInt(val))).getUTCMonth();
                        return months[mi]
                    },
                    sortFunction : function(values) {
                        // values.reverse();
                        return values;
                    },
                    renderer : edges.bs3.newDateHistogramSelectorRenderer({
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),

                // configure the search controller
                edges.newFullSearchController({
                    id: "search-controller",
                    category: "controller",
                    sortOptions : [
                        {'display':'Title','field':'index.unpunctitle.exact'},
                        {'display':'Publication date','field':"index.date"}
                    ],
                    fieldOptions : [
                        {'display':'Title','field':'bibjson.title'},
                        {'display':'Abstract','field':'bibjson.abstract'},
                        {'display':'Year','field':'bibjson.year'}
                    ],
                    defaultOperator : "AND",
                    urlShortener : doaj.bitlyShortener,
                    embedSnippet : doaj.publicToC.embedSnippet,
                    renderer : doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: 1000,
                        searchButton: true,
                        searchPlaceholder: "Search this Journal's Articles",
                        shareLink: true,
                        shareLinkText : "share | embed"
                    })
                }),

                // the pager, with the explicitly set page size options (see the openingQuery for the initial size)
                edges.newPager({
                    id: "top-pager",
                    category: "top-pager",
                    renderer : edges.bs3.newPagerRenderer({
                        sizeOptions : [10, 25, 50, 100],
                        numberFormat: countFormat,
                        scrollSelector: "html, body"
                    })
                }),
                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer : edges.bs3.newPagerRenderer({
                        sizeOptions : [10, 25, 50, 100],
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

                // selected filters display, with all the fields given their display names
                edges.newSelectedFilters({
                    id: "selected-filters",
                    category: "selected-filters",
                    ignoreUnknownFilters: true,
                    fieldDisplays : {
                        "bibjson.journal.volume.exact" : "Volume",
                        "bibjson.journal.number.exact" : "Issue",
                        "index.date" : "Year",
                        "index.date_toc_fv_month" : "Month"
                    },
                    rangeFunctions : {
                        "index.date" : doaj.publicToC.displayYearPeriod,
                        "index.date_toc_fv_month" : doaj.publicToC.displayMonthPeriod
                    }
                }),

                // the standard searching notification
                edges.newSearchingNotification({
                    id: "searching-notification",
                    category: "searching-notification"
                })
            ];

            var e = edges.newEdge({
                selector: selector,
                template: edges.bs3.newFacetview(),
                search_url: search_url,
                baseQuery : es.newQuery({
                    must : [
                        es.newTermsFilter({field: "index.issn.exact", values: doaj.publicToCConfig.tocIssns}),
                        es.newTermFilter({field: "_type", value: "article"})
                    ]
                }),
                openingQuery : es.newQuery({
                    size: 100
                }),
                manageUrl : true,
                components : components
            });
            doaj.publicToC.activeEdges[selector] = e;

            $(selector).on("edges:pre-render", function() {
                var volume = e.getComponent({id: "volume"});
                var yearPublished = e.getComponent({id: "year_published"});

                var deactivate = [];
                var activate = [];

                if (volume.filters.length === 0) {
                    deactivate = deactivate.concat(doaj.publicToC.dynamicFacets.volume);
                } else {
                    activate = activate.concat(doaj.publicToC.dynamicFacets.volume);
                }

                if (yearPublished.filters.length === 0) {
                    deactivate = deactivate.concat(doaj.publicToC.dynamicFacets.year_published);
                } else {
                    activate = activate.concat(doaj.publicToC.dynamicFacets.year_published);
                }

                for (var i = 0; i < e.components.length; i++) {
                    var component = e.components[i];
                    if ($.inArray(component.id, deactivate) !== -1) {
                        component.active = false;
                    } else if ($.inArray(component.id, activate) !== -1) {
                        component.active = true;
                    }
                }
            });

            $(selector).on("edges:pre-query", function() {
                var volume = e.getComponent({id: "volume"});
                var yearPublished = e.getComponent({id: "year_published"});

                var volumeMusts = e.currentQuery.listMust(es.newTermFilter({field: volume.field}));
                var yearMusts =  e.currentQuery.listMust(es.newRangeFilter({field: yearPublished.field}));

                var deactivate = [];
                if (volumeMusts.length === 0) {
                    deactivate = deactivate.concat(doaj.publicToC.dynamicFacets.volume);
                }
                if (yearMusts.length === 0) {
                    deactivate = deactivate.concat(doaj.publicToC.dynamicFacets.year_published);
                }

                for (var i = 0; i < e.components.length; i++) {
                    var component = e.components[i];
                    if ($.inArray(component.id, deactivate) !== -1) {
                        // remove the filters
                        component.clearFilters({triggerQuery: false});
                    }
                }
            });
        }
    }

});

jQuery(document).ready(function($) {
    doaj.publicToC.init();
});