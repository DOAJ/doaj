$.extend(true, doaj, {

    adminApplicationsSearch : {
        activeEdges : {},

        relatedJournal : function (val, resultobj, renderer) {
            var result = "";
            if (resultobj.admin) {
                var journals_url = doaj.adminApplicationsSearchConfig.journalsUrl;
                if (resultobj.admin.current_journal) {
                    var fvurl = journals_url + '?source=%7B"query"%3A%7B"query_string"%3A%7B"query"%3A"' + edges.escapeHtml(resultobj.admin.current_journal) + '"%2C"default_operator"%3A"AND"%7D%7D%2C"from"%3A0%2C"size"%3A10%7D';
                    result += "<strong>Update Request For</strong>: <a href='" + fvurl + "'>" + edges.escapeHtml(resultobj.admin.current_journal) + '</a>';
                }
                if (resultobj.admin.related_journal) {
                     var fvurl = journals_url + '?source=%7B"query"%3A%7B"query_string"%3A%7B"query"%3A"' + resultobj.admin.related_journal + '"%2C"default_operator"%3A"AND"%7D%7D%2C"from"%3A0%2C"size"%3A10%7D';
                    if (result != "") {
                        result += "<br>";
                    }
                    let label = "Produced Journal";
                    if (resultobj.admin.application_status === "rejected") {
                        label = "Originally For Journal";
                    }
                    result += "<strong>" + label + "</strong>: <a href='" + fvurl + "'>" + edges.escapeHtml(resultobj.admin.related_journal) + '</a>';
                }
            }
            return result;
        },

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#admin_applications";
            var search_url = current_scheme + "//" + current_domain + doaj.adminApplicationsSearchConfig.searchPath;

            var components = [
                doaj.components.searchingNotification(),

                // facets
                doaj.facets.openOrClosed(),
                doaj.facets.applicationStatus(),
                doaj.facets.hasEditorGroup(),
                doaj.facets.hasEditor(),
                doaj.facets.editorGroup(),
                doaj.facets.editor(),
                doaj.facets.hasAPC(),
                doaj.facets.classification(),
                doaj.facets.language(),
                doaj.facets.countryPublisher(),
                doaj.facets.subject(),
                doaj.facets.publisher(),
                doaj.facets.journalLicence(),

                // configure the search controller
                edges.newFullSearchController({
                    id: "search-controller",
                    category: "controller",
                    sortOptions: [
                        {'display':'Date applied','field':'admin.date_applied'},
                        {'display':'Last updated','field':'last_manual_update'},   // Note: last updated on UI points to when last updated by a person (via form)
                        {'display':'Title','field':'index.unpunctitle.exact'}
                    ],
                    fieldOptions: [
                        {'display':'Title','field':'index.title'},
                        {'display':'Keywords','field':'bibjson.keywords'},
                        {'display':'Classification','field':'index.classification'},
                        {'display':'ISSN', 'field':'index.issn.exact'},
                        {'display':'Country of publisher','field':'index.country'},
                        {'display':'Journal language','field':'index.language'},
                        {'display':'Publisher','field':'bibjson.publisher.name'},
                        {'display':'Journal: Alternative Title','field':'bibjson.alternative_title'}
                    ],
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: -1,
                        searchButton: true,
                        searchPlaceholder: "Search All Applications"
                    })
                }),

                // the pager, with the explicitly set page size options (see the openingQuery for the initial size)
                doaj.components.pager("top-pager", "top-pager"),
                doaj.components.pager("bottom-pager", "bottom-pager"),

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
                                    valueFunction: doaj.fieldRender.editSuggestion({
                                        editUrl : doaj.adminApplicationsSearchConfig.applicationEditUrl
                                    })
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
                                    "pre": "<strong>Country of publisher</strong>: ",
                                    valueFunction: doaj.fieldRender.countryName
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Journal language</strong>: ",
                                    "field": "bibjson.language"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Journal license</strong>: ",
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
                        'index.application_type.exact' : 'Update Request',
                        'index.has_editor_group.exact' : 'Has Editor Group?',
                        'index.has_editor.exact' : 'Has Associate Editor?',
                        'admin.editor_group.exact' : 'Editor Group',
                        'admin.editor.exact' : 'Editor',
                        'index.classification.exact' : 'Classification',
                        'index.language.exact' : 'Journal language',
                        'index.country.exact' : 'Country of publisher',
                        'index.subject.exact' : 'Subject',
                        'bibjson.publisher.name.exact' : 'Publisher',
                        'bibjson.provider.exact' : 'Platform, Host, Aggregator',
                        "index.has_apc.exact" : "Publication charges?",
                        'index.license.exact' : 'Journal license'
                    },
                    valueMaps : {
                        "index.application_type.exact" : {
                            "finished application/update": "Closed",
                            "update request": "Open",
                            "new application": "Open"
                        }
                    }
                })
            ];

            var e = edges.newEdge({
                selector: selector,
                template: edges.bs3.newFacetview(),
                search_url: search_url,
                manageUrl: true,
                openingQuery : es.newQuery({
                    sort: {"field" : "admin.date_applied", "order" : "asc"}
                }),
                components: components,
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact an administrator.");
                    }
                }
            });
            doaj.adminApplicationsSearch.activeEdges[selector] = e;

            doaj.multiFormBox.active = doaj.bulk.applicationMultiFormBox(e);
            $(selector).on("edges:pre-render", function() {
                doaj.multiFormBox.active.validate();
            });
        }
    }
});


jQuery(document).ready(function($) {
    doaj.adminApplicationsSearch.init();
});
