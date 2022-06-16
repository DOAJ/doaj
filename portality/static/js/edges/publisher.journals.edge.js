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

        shareSealLogo: function(resultobj) {
            // Add Display Seal as an action
            if (!edges.objVal("admin.seal", resultobj, false)) {
                return false;
            }
            let result = {
                label: "Download the Seal",
                link: "#",
                data: {
                    toggle: "modal",
                    target: "#modal-embed-seal-" + resultobj.id
                }
            }

            var issn = resultobj.bibjson.pissn;
            if (!issn) {
                issn = resultobj.bibjson.eissn;
            }
            if (issn) {
                issn = edges.escapeHtml(issn);
            }

            result.modal = '<section class="modal in" id="modal-embed-seal-' + resultobj.id + '" tabindex="-1" role="dialog" style="display: none;"> \
                    <div class="modal__dialog" role="document">\
                        <h2 class="modal__title">Download the Seal</h2>\
                        <p>Copy and paste this HTML to display the DOAJ Seal on your website:</p> \
                        <p><code>&lt;a href="https://doaj.org/toc/' + issn + '" target="_blank" style="display: block; width: 150px; height: auto;"&gt;&lt;img src="https://doaj.org/static/doaj/images/logo/seal.png"/&gt;&lt;/a&gt;</code></p>\
                        <button class="button" data-dismiss="modal" class="modal__close no-margins">Close</button>\
                    </div>\
                </section>';

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
                // edges.newSearchingNotification({
                //     id: "searching-notification",
                //     finishedEvent: "edges:post-render",
                //     renderer : doaj.renderers.newSearchingNotificationRenderer({
                //         scrollOnSearch: true
                //     })
                // }),

                doaj.components.searchingNotification(),

                edges.newPager({
                    id: "result-count",
                    category: "pager",
                    renderer : edges.bs3.newResultCountRenderer({
                        countFormat: countFormat,
                        suffix: " indexed journals",
                        htmlContainerWrapper: false
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
                    updateType: "fresh",
                    renderer : doaj.renderers.newORTermSelectorRenderer({
                        showCount: true,
                        hideEmpty: false,
                        open: false,
                        togglable: true
                    })
                }),

                // Subject Browser
                ///////////////////////////////////
                doaj.components.subjectBrowser({
                    tree: doaj.publisherJournalsSearchConfig.lccTree,
                    hideEmpty: true
                }),

                edges.newORTermSelector({
                    id: "keywords",
                    category: "facet",
                    field: "bibjson.keywords.exact",
                    display: "Keywords",
                    size: 99,
                    syncCounts: false,
                    lifecycle: "update",
                    updateType: "fresh",
                    renderer : doaj.renderers.newORTermSelectorRenderer({
                        showCount: true,
                        hideEmpty: false,
                        open: false,
                        togglable: true
                    })
                }),

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
                            display : "Without publication fees"
                        }
                    ],
                    fieldDisplays : {
                        "index.has_seal.exact" : "With a DOAJ Seal",
                        "index.schema_codes_tree.exact" : "Subject",
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
                    valueFunctions : {
                        "index.schema_codes_tree.exact" : doaj.valueMaps.schemaCodeToNameClosure(doaj.publisherJournalsSearchConfig.lccTree)
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
                        numberFormat: countFormat
                    })
                }),

                // results display
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer : doaj.renderers.newPublicSearchResultRenderer({
                        actions: [
                            doaj.publisherJournalsSearch.makeUpdateRequest,
                            doaj.publisherJournalsSearch.shareSealLogo
                        ]
                    })
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
