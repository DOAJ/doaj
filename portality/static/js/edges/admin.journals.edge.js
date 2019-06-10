$.extend(true, doaj, {

    adminJournalsSearch : {
        activeEdges : {},

        makeContinuation : function (val, resultobj, renderer) {
            if (!resultobj.suggestion && !resultobj.bibjson.journal) {
                // if it's not a suggestion or an article .. (it's a
                // journal!)
                // we really need to expose _type ...
                var result = '<a class="edit_journal_link" href="';
                result += doaj.adminJournalsSearchConfig.journalEditUrl;
                result += resultobj['id'];
                result += '/continue?type=replaces" target="_blank"';
                result += '>Make a preceding continuation</a>';

                result += "<span>&nbsp;|&nbsp;</span>";

                result += '<a class="edit_journal_link" href="';
                result += doaj.adminJournalsSearchConfig.journalEditUrl;
                result += resultobj['id'];
                result += '/continue?type=is_replaced_by" target="_blank"';
                result += '>Make a succeeding continuation</a>';

                return result;
            }
            return false;
        },

        relatedApplications : function (val, resultobj, renderer) {
            var result = "";
            if (resultobj.admin) {
                if (resultobj.admin.current_application) {
                    var fvurl = doaj.adminJournalsSearchConfig.applicationsUrl + '?source=%7B"query"%3A%7B"query_string"%3A%7B"query"%3A"' + resultobj.admin.current_application + '"%2C"default_operator"%3A"AND"%7D%7D%2C"from"%3A0%2C"size"%3A10%7D';
                    result += "<strong>Current Update Request</strong>: <a href='" + fvurl + "'>" + resultobj.admin.current_application + "</a>";
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

        editJournal : function (val, resultobj, renderer) {
            if (!resultobj.suggestion && !resultobj.bibjson.journal) {
                // if it's not a suggestion or an article .. (it's a
                // journal!)
                // we really need to expose _type ...
                var result = '<a class="edit_journal_link" href="';
                result += doaj.adminJournalsSearchConfig.journalEditUrl;
                result += resultobj['id'];
                result += '" target="_blank"';
                result += '>Edit this journal</a>';
                return result;
            }
            return false;
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
                // facets
                edges.newRefiningANDTermSelector({
                    id: "in_doaj",
                    category: "facet",
                    field: "admin.in_doaj",
                    display: "In DOAJ?",
                    valueMap : {
                        "T" : "True",
                        "F" : "False"
                    },
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "has_seal",
                    category: "facet",
                    field: "index.has_seal.exact",
                    display: "DOAJ Seal",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "owner",
                    category: "facet",
                    field: "admin.owner.exact",
                    display: "Owner",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "has_editor_group",
                    category: "facet",
                    field: "index.has_editor_group.exact",
                    display: "Has Editor Group?",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "has_associate_editor",
                    category: "facet",
                    field: "index.has_editor.exact",
                    display: "Has Associate Group?",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "editor_group",
                    category: "facet",
                    field: "admin.editor_group.exact",
                    display: "Editor Group",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "associate_editor",
                    category: "facet",
                    field: "admin.editor.exact",
                    display: "Associate Editor",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "author_pays",
                    category: "facet",
                    field: "bibjson.author_pays.exact",
                    display: "Publication charges?",
                    valueMap : {
                        "N" : "No",
                        "Y" : "Yes",
                        "NY" : "No Information",
                        "CON" : "Conditional"
                    },
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "journal_license",
                    category: "facet",
                    field: "index.license.exact",
                    display: "Journal License",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "publisher",
                    category: "facet",
                    field: "index.publisher.exact",
                    display: "Publisher",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "platform_host_aggregator",
                    category: "facet",
                    field: "bibjson.provider.exact",
                    display: "Platform, Host, Aggregator",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "classification",
                    category: "facet",
                    field: "index.classification.exact",
                    display: "Classification",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "subject",
                    category: "facet",
                    field: "index.subject.exact",
                    display: "Subject",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "journal_language",
                    category: "facet",
                    field: "index.language.exact",
                    display: "Journal Language",
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
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "continued",
                    category: "facet",
                    field: "index.continued.exact",
                    display: "Continued",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
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
                        countFormat: countFormat
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
                        {'display':'Journal Language','field':'index.language'},
                        {'display':'Publisher','field':'index.publisher'},
                        {'display':'Platform, Host, Aggregator','field':'bibjson.provider'}
                    ],
                    defaultOperator: "AND",
                    renderer: edges.bs3.newFullSearchControllerRenderer({
                        freetextSubmitDelay: 1000,
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
                        scrollSelector: "html, body"
                    })
                }),
                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [10, 25, 50, 100],
                        numberFormat: countFormat,
                        scrollSelector: "html, body"
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
                                    "field": "bibjson.publisher"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Platform, Host, Aggregator</strong>: ",
                                    "field": "bibjson.provider"
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
                                    "pre": "<strong>Started publishing Open Access content in</strong>: ",
                                    "field": "bibjson.oa_start.year"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Stopped publishing Open Access content in</strong>: ",
                                    "field": "bibjson.oa_end.year"
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
                            ],
                            [
                                {
                                    valueFunction: doaj.adminJournalsSearch.editJournal
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
                        "index.has_seal.exact" : "DOAJ Seal",
                        "admin.owner.exact" : "Owner",
                        "index.has_editor_group.exact" : "Has Editor Group?",
                        "index.has_editor.exact" : "Has Associate Editor?",
                        "admin.editor_group.exact" : "Editor Group",
                        "admin.editor.exact" : "Associate Editor",
                        "bibjson.author_pays.exact" : "Publication charges?",
                        "index.license.exact" : "Journal License",
                        "index.publisher.exact" : "Publisher",
                        "bibjson.provider.exact" : "Platform, Host, Aggregator",
                        "index.classification.exact" : "Classification",
                        "index.subject.exact" : "Subject",
                        "index.language.exact" : "Journal Language",
                        "index.country.exact" : "Country of publisher",
                        "index.continued.exact" : "Continued"
                    },
                    valueMaps : {
                        "admin.in_doaj" : {
                            "T" : "True",
                            "F" : "False"
                        },
                        "bibjson.author_pays.exact" : {
                            "N" : "No",
                            "Y" : "Yes",
                            "NY" : "No Information",
                            "CON" : "Conditional"
                        }
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
                manageUrl: true,
                components: components
            });
            doaj.adminJournalsSearch.activeEdges[selector] = e;
        }
    }
});


jQuery(document).ready(function($) {
    doaj.adminJournalsSearch.init();
});
