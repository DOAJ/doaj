$.extend(true, doaj, {

    editorGroupJournalsSearch : {
        activeEdges : {},

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#group_journals";
            var search_url = current_scheme + "//" + current_domain + doaj.editorGroupJournalsSearchConfig.searchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                doaj.components.searchingNotification(),

                // facets
                doaj.facets.inDOAJ(),
                edges.newRefiningANDTermSelector({
                    id: "owner",
                    category: "facet",
                    field: "admin.owner.exact",
                    display: "Owner",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "has_associate_editor",
                    category: "facet",
                    field: "index.has_editor.exact",
                    display: "Has Associate Editor?",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "editor_group",
                    category: "facet",
                    field: "admin.editor_group.exact",
                    display: "Editor Group",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "associate_editor",
                    category: "facet",
                    field: "admin.editor.exact",
                    display: "Associate Editor",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "author_pays",
                    category: "facet",
                    field: "index.has_apc.exact",
                    display: "Publication charges?",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "journal_license",
                    category: "facet",
                    field: "index.license.exact",
                    display: "Journal license",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "publisher",
                    category: "facet",
                    field: "bibjson.publisher.name.exact",
                    display: "Publisher",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "classification",
                    category: "facet",
                    field: "index.classification.exact",
                    display: "Classification",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "subject",
                    category: "facet",
                    field: "index.subject.exact",
                    display: "Subject",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "journal_language",
                    category: "facet",
                    field: "index.language.exact",
                    display: "Journal language",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "country_publisher",
                    category: "facet",
                    field: "index.country.exact",
                    display: "Country of publisher",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "journal_title",
                    category: "facet",
                    field: "index.title.exact",
                    display: "Journal title",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
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
                    sortOptions: [
                        {'display':'Date added to DOAJ','field':'created_date'},
                        {'display':'Last updated','field':'last_manual_update'},   // Note: last updated on UI points to when last updated by a person (via form)
                        {'display':'Title','field':'index.unpunctitle.exact'}
                    ],
                    fieldOptions: [
                        {'display':'Owner','field':'admin.owner'},
                        {'display':'Title','field':'index.title'},
                        {'display':'Alternative Title','field':'bibjson.alternative_title'},
                        {'display':'Subject','field':'index.subject'},
                        {'display':'Classification','field':'index.classification'},
                        {'display':'ISSN', 'field':'index.issn.exact'},
                        {'display':'Country of publisher','field':'index.country'},
                        {'display':'Journal language','field':'index.language'},
                        {'display':'Publisher','field':'bibjson.publisher.name'}
                    ],
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: -1,
                        searchButton: true,
                        searchPlaceholder: "Search Journals in your Group(s)"
                    })
                }),

                // the pager, with the explicitly set page size options (see the openingQuery for the initial size)
                edges.newPager({
                    id: "top-pager",
                    category: "top-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [10, 25, 50, 100],
                        numberFormat: countFormat,
                        scroll: false
                    })
                }),
                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [10, 25, 50, 100],
                        numberFormat: countFormat,
                        scroll: false
                    })
                }),

                // results display
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer: edges.bs3.newResultsFieldsByRowRenderer({
                        noResultsText: "<p>There are no journals for your editor group(s) that meet the search criteria</p>" +
                                        "<p>If you have not set any search criteria, this means there are no journals currently allocated to your group</p>",
                        rowDisplay : [
                            [
                                {
                                    valueFunction: doaj.fieldRender.titleField
                                }
                            ],
                            [
                                {
                                    "pre": '<span class="alt_title">Alternative title: ',
                                    "field": "bibjson.alternative_title",
                                    "post": "</span>"
                                }
                            ],
                            [
                                {
                                    "pre" : "<strong>In DOAJ?</strong>: ",
                                    valueFunction: doaj.fieldRender.inDoaj
                                }
                            ],
                            [
                                {
                                    "pre" : "<strong>Owner</strong>: ",
                                    valueFunction: doaj.fieldRender.owner
                                }
                            ],
                            [
                                {
                                    "pre" : "<strong>Editor Group</strong>: ",
                                    "field" : "admin.editor_group"
                                }
                            ],
                            [
                                {
                                    "pre" : "<strong>Editor</strong>: ",
                                    "field" : "admin.editor"
                                }
                            ],
                            [
                                {
                                    valueFunction : doaj.fieldRender.issns
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Date added to DOAJ</strong>: ",
                                    valueFunction: doaj.fieldRender.createdDateWithTime
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Last updated</strong>: ",
                                    valueFunction: doaj.fieldRender.lastManualUpdate
                                }
                            ],
                            [
                                {
                                    valueFunction: doaj.fieldRender.links
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>License</strong>: ",
                                    valueFunction: doaj.fieldRender.journalLicense
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Publisher</strong>: ",
                                    "field": "bibjson.publisher.name"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Publication charges?</strong>: ",
                                    valueFunction: doaj.fieldRender.authorPays
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Classification</strong>: ",
                                    "field": "index.classification"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Keywords</strong>: ",
                                    "field": "bibjson.keywords"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Country</strong>: ",
                                    valueFunction: doaj.fieldRender.countryName
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Language</strong>: ",
                                    "field": "bibjson.language"
                                }
                            ],
                            [
                                {
                                    valueFunction: doaj.fieldRender.editJournal({editUrl: doaj.editorGroupJournalsSearchConfig.journalEditUrl})
                                }
                            ]
                        ]
                    })
                }),

                // selected filters display, with all the fields given their display names
                edges.newSelectedFilters({
                    id: "selected-filters",
                    category: "selected-filters",
                    fieldDisplays: {
                        "admin.in_doaj" : "In DOAJ?",
                        "admin.owner.exact" : "Owner",
                        "index.has_editor.exact" : "Associate Editor?",
                        "admin.editor_group.exact" : "Editor group",
                        "admin.editor.exact" : "Associate Editor",
                        "index.license.exact" : "License",
                        "bibjson.publisher.name.exact" : "Publisher",
                        "index.classification.exact" : "Classification",
                        "index.subject.exact" : "Subject",
                        "index.language.exact" : "Language",
                        "index.country.exact" : "Country",
                        "index.title.exact" : "Title",
                        "index.has_apc.exact" : "Charges?"
                    },
                    valueMaps : {
                        "admin.in_doaj" : {
                            true : "True",
                            false : "False"
                        }
                    }
                })
            ];

            var e = edges.newEdge({
                selector: selector,
                template: edges.bs3.newFacetview(),
                search_url: search_url,
                manageUrl: true,
                components: components,
                openingQuery: es.newQuery({
                    sort: [{field: "created_date", order: "desc"}]
                }),
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact an administrator.");
                    }
                }
            });
            doaj.editorGroupJournalsSearch.activeEdges[selector] = e;
        }
    }
});


jQuery(document).ready(function($) {
    doaj.editorGroupJournalsSearch.init();
});
