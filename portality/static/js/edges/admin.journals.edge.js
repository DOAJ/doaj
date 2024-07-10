// ~~ AdminJournalsSearch:Feature ~~
$.extend(true, doaj, {

    adminJournalsSearch : {
        activeEdges : {},

        makeContinuation : function (val, resultobj, renderer) {
            if (!resultobj.suggestion && !resultobj.bibjson.journal) {
                // if it's not a suggestion or an article .. (it's a
                // journal!)
                // we really need to expose _type ...
                var result = '<br/><a class="edit_journal_link button" href="';
                result += doaj.adminJournalsSearchConfig.journalEditUrl;
                result += resultobj['id'];
                result += '/continue?type=replaces" target="_blank"';
                result += ' style="margin-bottom: 0;">Make a preceding continuation</a>';

                result += '<a class="edit_journal_link button" href="';
                result += doaj.adminJournalsSearchConfig.journalEditUrl;
                result += resultobj['id'];
                result += '/continue?type=is_replaced_by" target="_blank"';
                result += ' style="margin-bottom: 0;">Make a succeeding continuation</a>';

                return result;
            }
            return false;
        },

        relatedApplications : function (val, resultobj, renderer) {
            var result = "";
            if (resultobj.admin) {
                if (resultobj.admin.current_application) {
                    var fvurl = doaj.adminJournalsSearchConfig.applicationsUrl + '?source=%7B"query"%3A%7B"query_string"%3A%7B"query"%3A"' + resultobj.admin.current_application + '"%2C"default_operator"%3A"AND"%7D%7D%2C"from"%3A0%2C"size"%3A10%7D';
                    result += "<strong>Current Update Request</strong>: <a href='" + fvurl + "'>" + edges.escapeHtml(resultobj.admin.current_application) + "</a>";
                }
                if (resultobj.admin.related_applications && resultobj.admin.related_applications.length > 0) {
                    if (result != "") {
                        result += "<br>";
                    }
                    result += "<strong>Related Records</strong>: ";
                    for (var i = 0; i < resultobj.admin.related_applications.length; i++) {
                        if (i > 0) {
                            result += ", ";
                        }
                        var ra = resultobj.admin.related_applications[i];
                        var fvurl = doaj.adminJournalsSearchConfig.applicationsUrl + '?source=%7B"query"%3A%7B"query_string"%3A%7B"query"%3A"' + ra.application_id + '"%2C"default_operator"%3A"AND"%7D%7D%2C"from"%3A0%2C"size"%3A10%7D';
                        var linkName = ra.date_accepted;
                        if (!linkName) {
                            linkName = ra.application_id;
                        }
                        result += "<a href='" + fvurl + "'>" + linkName + "</a>";
                    }
                }
            }
            return result;
        },

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#admin_journals";
            var search_url = current_scheme + "//" + current_domain + doaj.adminJournalsSearchConfig.searchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                doaj.components.searchingNotification(),

                // facets
                doaj.facets.inDOAJ(),
                edges.newRefiningANDTermSelector({
                    id: "has_seal",
                    category: "facet",
                    field: "index.has_seal.exact",
                    display: "DOAJ Seal",
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
                    id: "has_editor_group",
                    category: "facet",
                    field: "index.has_editor_group.exact",
                    display: "Has editor group?",
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
                    display: "Editor group",
                    deactivateThreshold: 1,
                    valueFunction: doaj.fieldRender.editorGroupNameCallback,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true,
                        noDisplayEscape: true,
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
                        countFormat: countFormat
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
                    id: "continued",
                    category: "facet",
                    field: "index.continued.exact",
                    display: "Continued",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newDateHistogramSelector({
                    id: "discontinued_date",
                    category: "facet",
                    field : "bibjson.discontinued_date",
                    interval: "year",
                    display: "Discontinued Year",
                    displayFormatter : function(val) {
                        return (new Date(parseInt(val))).getUTCFullYear();
                    },
                    sortFunction : function(values) {
                        values.reverse();
                        return values;
                    },
                    renderer: edges.bs3.newDateHistogramSelectorRenderer({
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
                        {'display':'Last updated','field':'last_manual_update'}, // Note: last updated on UI points to when last updated by a person (via form)
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
                        {'display':'Publisher','field':'bibjson.publisher.name'},
                        {'display':'Notes','field':'admin.notes.note'}
                    ],
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: -1,
                        searchButton: true,
                        searchPlaceholder: "Search All Journals"
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
                        rowDisplay : [
                            [
                                {
                                    valueFunction: doaj.fieldRender.titleField
                                }
                            ],
                            [
                                {
                                   valueFunction: doaj.fieldRender.editJournal({editUrl: doaj.adminJournalsSearchConfig.journalEditUrl})
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
                                    "pre" : "<strong>Editor group</strong>: ",
                                    "field" : "index.editor_group_name",
                                }
                            ],
                            [
                                {
                                    "pre" : "<strong>ISSN(s)</strong>: ",
                                    valueFunction : doaj.fieldRender.issns
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Discontinued Date</strong>: ",
                                    "field": "bibjson.discontinued_date"
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
                                    valueFunction: doaj.adminJournalsSearch.relatedApplications
                                }
                            ],
                            [
                                {
                                    valueFunction: doaj.adminJournalsSearch.makeContinuation
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
                        "index.has_seal.exact" : "Seal?",
                        "admin.owner.exact" : "Owner",
                        "index.has_editor_group.exact" : "Editor group?",
                        "index.has_editor.exact" : "Associate Editor?",
                        "admin.editor_group.exact" : "Editor group",
                        "admin.editor.exact" : "Associate Editor",
                        "index.license.exact" : "License",
                        "bibjson.publisher.name.exact" : "Publisher",
                        "index.classification.exact" : "Classification",
                        "index.subject.exact" : "Subject",
                        "index.language.exact" : "Language",
                        "index.country.exact" : "Country",
                        "index.continued.exact" : "Continued",
                        "bibjson.discontinued_date" : "Discontinued Year",
                        "index.has_apc.exact" : "Charges?"
                    },
                    valueMaps : {
                        "admin.in_doaj" : {
                            true : "Yes",
                            false : "No"
                        }
                    },
                    valueFunctions : {
                        "admin.editor_group.exact" : doaj.fieldRender.editorGroupNameCallback,
                    },
                    rangeFunctions : {
                        "bibjson.discontinued_date" : doaj.valueMaps.displayYearPeriod
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
                        alert("There was an unexpected error. Please reload the page and try again. If the issue persists please contact an administrator.");
                    },
                    "edges:post-render" : function () {
                        doaj.fieldRender.editorGroupNameTrigger(e.result);
                    }
                }
            });
            doaj.adminJournalsSearch.activeEdges[selector] = e;
        }
    }
});


jQuery(document).ready(function($) {
    doaj.adminJournalsSearch.init();
});
