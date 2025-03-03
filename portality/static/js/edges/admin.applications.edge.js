// ~~ AdminApplicationsSearch:Feature ~~
$.extend(true, doaj, {

    adminApplicationsSearch : {
        activeEdges : {},

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
                doaj.components.searchingNotification(),
                // filters
                edges.newFilterSetter({
                    id : "see_applications",
                    category: "facet",
                    filters : [
                        doaj.filters.noCharges()
                    ],
                    renderer : doaj.renderers.newFacetFilterSetterRenderer({
                        facetTitle : "",
                        open: true,
                        togglable: false,
                        showCount: false
                    })
                }),
                // facets
                doaj.facets.openOrClosed(),
                doaj.facets.applicationStatus(),
                doaj.facets.hasEditorGroup(),
                doaj.facets.hasEditor(),
                doaj.facets.editorGroup(),
                doaj.facets.editor(),
                doaj.facets.classification(),
                doaj.facets.language(),
                doaj.facets.countryPublisher(),
                doaj.facets.subject(),
                doaj.facets.publisher(),
                doaj.facets.journalLicence(),

                doaj.components.newFacetDivider({
                    id: "reporting_tools_divider",
                    category: "facet",
                    display: "Reporting Tools"
                }),
                doaj.components.newSimultaneousDateRangeEntry({
                    id: "date_limiter",
                    display: "Limit by Date Range",
                    fields: [
                        {"field": "admin.date_applied", "display": "Date Applied"},
                        {"field": "last_manual_update", "display": "Last Updated"}
                    ],
                    autoLookupRange: true,
                    category: "facet",
                    renderer: doaj.renderers.newBSMultiDateRangeFacet()
                }),

                doaj.components.newDateHistogramSelector({
                    id: "date_applied_histogram",
                    category: "facet",
                    field: "admin.date_applied",
                    display: "Date Applied Histogram",
                    interval: "year",
                    displayFormatter : function(val) {
                        let date = new Date(parseInt(val));
                        let interval = doaj.adminApplicationsSearch.activeEdges[selector].getComponent({id: "date_applied_histogram"}).interval;
                        if (interval === "year") {
                            return date.toLocaleString('default', { year: 'numeric', timeZone: "UTC" });
                        } else if (interval === "month") {
                            return date.toLocaleString('default', { month: 'long', year: 'numeric', timeZone: "UTC" });
                        }
                    },
                    sortFunction : function(values) {
                        values.reverse();
                        return values;
                    },
                    renderer: doaj.renderers.newFlexibleDateHistogramSelectorRenderer({
                        showSelected: false,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),

                doaj.components.newDateHistogramSelector({
                    id: "last_updated_histogram",
                    category: "facet",
                    field: "last_manual_update",
                    display: "Last Update Histogram",
                    interval: "year",
                    displayFormatter : function(val) {
                        let date = new Date(parseInt(val));
                        let interval = doaj.adminApplicationsSearch.activeEdges[selector].getComponent({id: "last_updated_histogram"}).interval;
                        if (interval === "year") {
                            return date.toLocaleString('default', { year: 'numeric', timeZone: "UTC" });
                        } else if (interval === "month") {
                            return date.toLocaleString('default', { month: 'long', year: 'numeric', timeZone: "UTC" });
                        }
                    },
                    sortFunction : function(values) {
                        values.reverse();
                        return values;
                    },
                    renderer: doaj.renderers.newFlexibleDateHistogramSelectorRenderer({
                        showSelected: false,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                doaj.components.newReportExporter({
                    id: "report-exporter",
                    category: "facet",
                    model: "application",
                    facetExports: [
                        {component_id: "application_type", exporter: doaj.valueMaps.refiningANDTermSelectorExporter},
                        {component_id: "application_status", exporter: doaj.valueMaps.refiningANDTermSelectorExporter},
                        {component_id: "has_editor_group", exporter: doaj.valueMaps.refiningANDTermSelectorExporter},
                        {component_id: "has_editor", exporter: doaj.valueMaps.refiningANDTermSelectorExporter},
                        {component_id: "editor_group", exporter: doaj.valueMaps.refiningANDTermSelectorExporter},
                        {component_id: "editor", exporter: doaj.valueMaps.refiningANDTermSelectorExporter},
                        {component_id: "classification", exporter: doaj.valueMaps.refiningANDTermSelectorExporter},
                        {component_id: "language", exporter: doaj.valueMaps.refiningANDTermSelectorExporter},
                        {component_id: "country_publisher", exporter: doaj.valueMaps.refiningANDTermSelectorExporter},
                        {component_id: "subject", exporter: doaj.valueMaps.refiningANDTermSelectorExporter},
                        {component_id: "publisher", exporter: doaj.valueMaps.refiningANDTermSelectorExporter},
                        {component_id: "journal_license", exporter: doaj.valueMaps.refiningANDTermSelectorExporter},
                        {component_id: "date_applied_histogram", exporter: doaj.valueMaps.dateHistogramSelectorExporter},
                        {component_id: "last_updated_histogram", exporter: doaj.valueMaps.dateHistogramSelectorExporter}
                    ]
                }),

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
                        {'display':'Journal: alternative title','field':'bibjson.alternative_title'},
                        {'display':'Notes','field':'admin.notes.note'},
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
                                    "pre": '<strong>Alternative title: </strong>',
                                    "field": "bibjson.alternative_title"
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
                                    "pre" : "<strong>Editor group</strong>: ",
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
                            ]
                        ]
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
                            display : "Without article processing charges (APCs)"
                        }
                    ],
                    fieldDisplays: {
                        'admin.application_status.exact': 'Status',
                        'index.application_type.exact' : 'Application',
                        'index.has_editor_group.exact' : 'Editor group',
                        'index.has_editor.exact' : 'Associate Editor',
                        'admin.editor_group.exact' : 'Editor group',
                        'admin.editor.exact' : 'Editor',
                        'index.classification.exact' : 'Classification',
                        'index.language.exact' : 'Language',
                        'index.country.exact' : 'Country',
                        'index.subject.exact' : 'Subject',
                        'bibjson.publisher.name.exact' : 'Publisher',
                        'bibjson.provider.exact' : 'Platform, Host, Aggregator',
                        "index.has_apc.exact" : "Charges?",
                        'index.license.exact' : 'License',
                        "admin.date_applied": "Date Applied",
                        "last_manual_update": "Last Updated"
                    },
                    valueMaps : {
                        "index.application_type.exact" : {
                            "finished application/update": "Closed",
                            "update request": "Open",
                            "new application": "Open"
                        }
                    },
                    rangeFunctions : {
                        "admin.date_applied" : doaj.valueMaps.displayYearMonthPeriod,
                        "last_manual_update": doaj.valueMaps.displayYearMonthPeriod
                    },
                    renderer : doaj.renderers.newSelectedFiltersRenderer({
                        omit : [
                            "bibjson.apc.has_apc",
                            "bibjson.other_charges.has_other_charges"
                        ]
                    })
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

            doaj.multiFormBox.active = doaj.bulk.applicationMultiFormBox(e, "applications");
            $(selector).on("edges:pre-render", function() {
                doaj.multiFormBox.active.validate();
            });
        }
    }
});


jQuery(document).ready(function($) {
    doaj.adminApplicationsSearch.init();
});
