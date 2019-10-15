$.extend(true, doaj, {

    adminApplicationsSearch : {
        activeEdges : {},

        editSuggestion : function (val, resultobj, renderer) {
            if (resultobj['suggestion']) {
                // determine the link name
                var linkName = "Review application";
                if (resultobj.admin.application_status === 'accepted' || resultobj.admin.application_status === 'rejected') {
                    linkName = "View finished application";
                    if (resultobj.admin.related_journal) {
                        linkName = "View finished update";
                    }
                } else if (resultobj.admin.current_journal) {
                    linkName = "Review update";
                }

                var result = '<a class="edit_suggestion_link" href="';
                result += doaj.adminApplicationsSearchConfig.applicationEditUrl;
                result += resultobj['id'];
                result += '" target="_blank"';
                result += '>' + linkName + '</a>';
                return result;
            }
            return false;
        },

        readOnlyJournal : function (val, resultobj, renderer) {
            if (resultobj.admin && resultobj.admin.current_journal) {
                var result = '<a style="margin-left: 10px; margin-right: 10px" class="readonly_journal_link" href="';
                result += doaj.adminApplicationsSearchConfig.readOnlyJournalUrl;
                result += resultobj.admin.current_journal;
                result += '" target="_blank"';
                result += '>View journal being updated</a>';
                return result;
            }
            return false;
        },

        relatedJournal : function (val, resultobj, renderer) {
            var result = "";
            if (resultobj.admin) {
                var journals_url = doaj.adminApplicationsSearchConfig.journalsUrl;
                if (resultobj.admin.current_journal) {
                    var fvurl = journals_url + '?source=%7B"query"%3A%7B"query_string"%3A%7B"query"%3A"' + resultobj.admin.current_journal + '"%2C"default_operator"%3A"AND"%7D%7D%2C"from"%3A0%2C"size"%3A10%7D';
                    result += "<strong>Update Request For</strong>: <a href='" + fvurl + "'>" + resultobj.admin.current_journal + '</a>';
                }
                if (resultobj.admin.related_journal) {
                     var fvurl = journals_url + '?source=%7B"query"%3A%7B"query_string"%3A%7B"query"%3A"' + resultobj.admin.related_journal + '"%2C"default_operator"%3A"AND"%7D%7D%2C"from"%3A0%2C"size"%3A10%7D';
                    if (result != "") {
                        result += "<br>";
                    }
                    result += "<strong>Produced Journal</strong>: <a href='" + fvurl + "'>" + resultobj.admin.related_journal + '</a>';
                }
            }
            return result;
        },

        adminStatusMap: function(value) {
            if (doaj.valueMaps.applicationStatus.hasOwnProperty(value)) {
                return doaj.valueMaps.applicationStatus[value];
            }
            return value;
        },

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#admin_applications";
            var search_url = current_scheme + "//" + current_domain + doaj.adminApplicationsSearchConfig.searchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                // facets
                edges.newRefiningANDTermSelector({
                    id: "application_status",
                    category: "facet",
                    field: "admin.application_status.exact",
                    display: "Application Status",
                    deactivateThreshold : 1,
                    valueFunction : doaj.adminApplicationsSearch.adminStatusMap,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "application_type",
                    category: "facet",
                    field: "index.application_type.exact",
                    display: "Record type",
                    deactivateThreshold : 1,
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
                    display: "Has Editor Group?",
                    deactivateThreshold : 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "has_editor",
                    category: "facet",
                    field: "index.has_editor.exact",
                    display: "Has Associate Editor?",
                    deactivateThreshold : 1,
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
                    deactivateThreshold : 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "editor",
                    category: "facet",
                    field: "admin.editor.exact",
                    display: "Editor",
                    deactivateThreshold : 1,
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
                    deactivateThreshold : 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "language",
                    category: "facet",
                    field: "index.language.exact",
                    display: "Journal Language",
                    deactivateThreshold : 1,
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
                    deactivateThreshold : 1,
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
                    deactivateThreshold : 1,
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
                    field: "index.publisher.exact",
                    display: "Publisher",
                    deactivateThreshold : 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "provider",
                    category: "facet",
                    field: "bibjson.provider.exact",
                    display: "Platform, Host, Aggregator",
                    deactivateThreshold : 1,
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
                    display: "Journal License",
                    deactivateThreshold : 1,
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
                        {'display':'Date applied','field':'suggestion.suggested_on'},
                        {'display':'Last updated','field':'last_manual_update'},   // Note: last updated on UI points to when last updated by a person (via form)
                        {'display':'Title','field':'index.unpunctitle.exact'}
                    ],
                    fieldOptions: [
                        {'display':'Title','field':'index.title'},
                        {'display':'Keywords','field':'bibjson.keywords'},
                        {'display':'Classification','field':'index.classification'},
                        {'display':'ISSN', 'field':'index.issn.exact'},
                        {'display':'Country of publisher','field':'index.country'},
                        {'display':'Journal Language','field':'index.language'},
                        {'display':'Publisher','field':'index.publisher'},

                        {'display':'Journal: Alternative Title','field':'bibjson.alternative_title'},
                        {'display':'Journal: Platform, Host, Aggregator','field':'bibjson.provider'}
                    ],
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: 1000,
                        searchButton: true,
                        searchPlaceholder: "Search All Applications"
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
                                    "pre": "<strong>Date applied</strong>: ",
                                    valueFunction: doaj.fieldRender.suggestedOn
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
                                    "pre" : "<strong>Owner</strong>: ",
                                    valueFunction: doaj.fieldRender.owner
                                }
                            ],
                            [
                                {
                                    "pre" : "<strong>ISSN(s)</strong>: ",
                                    valueFunction: doaj.fieldRender.issns
                                }
                            ],
                            [
                                {
                                    "pre" : "<strong>Application status</strong>: ",
                                    valueFunction: doaj.fieldRender.applicationStatus
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
                                    "pre" : "<strong>Description</strong>: ",
                                    "field" : "suggestion.description"
                                }
                            ],
                            [
                                {
                                    "pre" : "<strong>Contact</strong>: ",
                                    "field" : "admin.contact.name"
                                },
                                {
                                    "field" : "admin.contact.email"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Application by</strong>: ",
                                    "field": "suggestion.suggester.name",
                                    "post" : " "
                                },
                                {
                                    "pre" : "<strong>Applicant email</strong>: ",
                                    "field": "suggestion.suggester.email"
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
                                    "pre": "<strong>Country of publisher</strong>: ",
                                    valueFunction: doaj.fieldRender.countryName
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Journal Language</strong>: ",
                                    "field": "bibjson.language"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Journal License</strong>: ",
                                    valueFunction: doaj.fieldRender.journalLicense
                                }
                            ],
                            [
                                {
                                    valueFunction: doaj.fieldRender.links
                                }
                            ],
                            [
                                {
                                    valueFunction: doaj.adminApplicationsSearch.relatedJournal
                                }
                            ],
                            [
                                {
                                    valueFunction: doaj.fieldRender.readOnlyJournal({
                                        readOnlyJournalURL : doaj.adminApplicationsSearchConfig.readOnlyJournalUrl
                                    })
                                },
                                {
                                    valueFunction: doaj.fieldRender.editSuggestion({
                                        editUrl : doaj.adminApplicationsSearchConfig.applicationEditUrl
                                    })
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
                        'admin.application_status.exact': 'Application Status',
                        'index.application_type.exact' : 'Record type',
                        'index.has_editor_group.exact' : 'Has Editor Group?',
                        'index.has_editor.exact' : 'Has Associate Editor?',
                        'admin.editor_group.exact' : 'Editor Group',
                        'admin.editor.exact' : 'Editor',
                        'index.classification.exact' : 'Classification',
                        'index.language.exact' : 'Journal Language',
                        'index.country.exact' : 'Country of publisher',
                        'index.subject.exact' : 'Subject',
                        'index.publisher.exact' : 'Publisher',
                        'bibjson.provider.exact' : 'Platform, Host, Aggregator',
                        'bibjson.author_pays.exact' : 'Publication charges?',
                        'index.license.exact' : 'Journal License'
                    },
                    valueMaps : {
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
                openingQuery : es.newQuery({
                    sort: {"field" : "suggestion.suggested_on", "order" : "asc"}
                }),
                components: components,
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact an administrator.");
                    }
                }
            });
            doaj.adminApplicationsSearch.activeEdges[selector] = e;

            var mfb = doaj.multiFormBox.newMultiFormBox({
                edge : e,
                selector: "#admin-bulk-box",
                bindings : {
                    editor_group : function(context) {
                        autocomplete($('#editor_group', context), 'name', 'editor_group', 1, false);
                    }
                },
                validators : {
                    application_status : function(context) {
                        var val = context.find("#application_status").val();
                        if (val === "") {
                            return {valid: false};
                        }
                        return {valid: true};
                    },
                    editor_group : function(context) {
                        var val = context.find("#editor_group").val();
                        if (val === "") {
                            return {valid: false};
                        }
                        return {valid: true};
                    },
                    note : function(context) {
                        var val = context.find("#note").val();
                        if (val === "") {
                            return {valid: false};
                        }
                        return {valid: true};
                    }
                },
                submit : {
                    note : {
                        data: function(context) {
                            return {
                                note: $('#note', context).val()
                            };
                        }
                    },
                    editor_group : {
                        data : function(context) {
                            return {
                                editor_group: $('#editor_group', context).val()
                            };
                        }
                    },
                    application_status : {
                        data : function(context) {
                            return {
                                application_status: $('#application_status', context).val()
                            };
                        }
                    }
                },
                urls : {
                    note : "/admin/applications/bulk/add_note",
                    editor_group : "/admin/applications/bulk/assign_editor_group",
                    application_status : "/admin/applications/bulk/change_status"
                }
            });
            doaj.multiFormBox.active = mfb;

            $(selector).on("edges:pre-render", function() {
                doaj.multiFormBox.active.validate();
            });
        }
    }
});


jQuery(document).ready(function($) {
    doaj.adminApplicationsSearch.init();
});
