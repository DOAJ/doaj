$.extend(true, doaj, {

    publicSearch : {
        activeEdges : {},

        dynamicFacets : {
            journal : [
                "country_publisher",
                "apc",
                "peer_review",
                "year_added",
                "language"
            ],
            article : [
                "archiving_policy",
                "journal_title",
                "year_published"
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



                // configure the search controller
                edges.newFullSearchController({
                    id: "search-controller-remember",
                    category: "controller",
                    sortOptions : [
                        {'display':'Date added to DOAJ','field':'created_date'},
                        {'display':'Title','field':'index.unpunctitle.exact'},
                        {'display':'Article: Publication date','field':'index.date'}
                    ],
                    fieldOptions : [
                        {'display':'Title','field':'bibjson.title'},
                        {'display':'Keywords','field':'bibjson.keywords'},
                        {'display':'Subject','field':'index.classification'},
                        {'display':'ISSN', 'field':'index.issn.exact'},
                        {'display':'DOI', 'field' : 'bibjson.identifier.id'},
                        {'display':'Country of publisher','field':'index.country'},
                        {'display':'Journal Language','field':'index.language'},
                        {'display':'Publisher','field':'bibjson.publisher'},

                        {'display':'Article: Abstract','field':'bibjson.abstract'},
                        {'display':'Article: Year','field':'bibjson.year'},
                        {'display':'Article: Journal Title','field':'bibjson.journal.title'},
                        {'display':'Article: Author\'s name','field':'bibjson.author.name'},
                        {'display':'Article: Author\'s ORCID iD','field':'bibjson.author.orcid_id'},

                        {'display':'Journal: Alternative Title','field':'bibjson.alternative_title'}
                    ],
                    defaultOperator : "AND",
                    urlShortener : doaj.bitlyShortener,
                    embedSnippet : doaj.publicSearch.embedSnippet,
                    renderer : doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: 1000,
                        searchButton: true,
                        searchPlaceholder: "Search DOAJ",
                        shareLink: true,
                        shareLinkText : "share | embed"
                    })
                }),


                /*
                edges.newRefiningANDTermSelector({
                    id : "apc",
                    category: "facet",
                    field: "index.has_apc.exact",
                    display: "Article processing charges (APCs)",
                    deactivateThreshold: 1,
                    active: false,
                    renderer : edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true,
                        tooltipText: "What do these figures mean?",
                        tooltip: 'For more information see this <a href="https://doajournals.wordpress.com/2015/05/11/historical-apc-data-from-before-the-april-upgrade/" target="_blank">blog post</a> (opens in new window).'
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id : "journal_title",
                    category: "facet",
                    field: "bibjson.journal.title.exact",
                    display: "Journal title",
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
                    id : "seal",
                    category: "facet",
                    field: "index.has_seal.exact",
                    display: "Journal has DOAJ Seal",
                    deactivateThreshold: 1,
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
                    display: "Year of publication",
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
                        hideInactive: true,
                        shortDisplay: 15
                    })
                }),
                */


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
                    fieldDisplays : {
                        "es_type" : "Showing",
                        "index.classification.exact" : "Subject",
                        "index.has_apc.exact" : "Article processing charges (APCs)",
                        "index.has_seal.exact" : "DOAJ Seal",
                        "index.license.exact" : "Journal license",
                        "bibjson.publisher.exact" : "Publisher",
                        "index.country.exact" : "Country of Publisher",
                        "index.language.exact" : "Fulltext Language",
                        "bibjson.editorial_review.process.exact" : "Peer review",
                        "created_date" : "Date added to DOAJ",
                        "bibjson.journal.title.exact" : "Journal title",
                        "index.date" : "Year of publication"
                    },
                    valueMaps : {
                        "es_type" : {
                            "journal" : "Journals",
                            "article" : "Articles"
                        }
                    },
                    rangeFunctions : {
                        "created_date" : doaj.valueMaps.displayYearPeriod
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
                    }
                }
            });
            doaj.publicSearch.activeEdges[selector] = e;

            /*
            $(selector).on("edges:pre-render", function() {
                var journal_article = e.getComponent({id: "journal_article"});

                var deactivate = [];
                var activate = [];
                if (journal_article.filters.length === 0) {
                    deactivate = [].concat(doaj.publicSearch.dynamicFacets.journal).concat(doaj.publicSearch.dynamicFacets.article);
                } else {
                    var term = journal_article.filters[0].term;
                    if (term === "journal") {
                        deactivate = doaj.publicSearch.dynamicFacets.article;
                        activate = doaj.publicSearch.dynamicFacets.journal;
                    } else if (term === "article") {
                        activate = doaj.publicSearch.dynamicFacets.article;
                        deactivate = doaj.publicSearch.dynamicFacets.journal;
                    }
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
                var journal_article = e.getComponent({id: "journal_article"});
                var musts = e.currentQuery.listMust(es.newTermFilter({field: journal_article.field}));
                var deactivate = [];
                if (musts.length === 0) {
                    deactivate = [].concat(doaj.publicSearch.dynamicFacets.journal).concat(doaj.publicSearch.dynamicFacets.article);
                } else {
                    var term = musts[0].value;
                    if (term === "journal") {
                        deactivate = doaj.publicSearch.dynamicFacets.article;
                    } else if (term === "article") {
                        deactivate = doaj.publicSearch.dynamicFacets.journal;
                    }
                }

                for (var i = 0; i < e.components.length; i++) {
                    var component = e.components[i];
                    if ($.inArray(component.id, deactivate) !== -1) {
                        // remove the filters
                        component.clearFilters({triggerQuery: false});
                    }
                }
            });*/
        }
    }

});

jQuery(document).ready(function($) {
    doaj.publicSearch.init();
});