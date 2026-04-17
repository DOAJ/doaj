doaj.editorGroupApplicationsSearch = {
    activeEdges : {},

    editorStatusMap: function(value) {
        if (doaj.valueMaps.applicationStatus.hasOwnProperty(value)) {
            return doaj.valueMaps.applicationStatus[value];
        }
        return value;
    },

    init : function(params) {
        if (!params) { params = {} }

        var selector = params.selector || "#group_applications";

        var e = doaj.components.makeSearch({
            selector: selector,
            searchUrl: doaj.build(doaj.editorGroupApplicationsSearchConfig.searchPath),
            facets: [
                doaj.facets.openOrClosed(),
                doaj.components.refiningAndFacet({id: "application_status", field: "admin.application_status.exact", display: "Application Status", deactivateThreshold: 1, valueFunction: doaj.editorGroupApplicationsSearch.editorStatusMap}),
                doaj.components.refiningAndFacet({id: "has_editor", field: "index.has_editor.exact", display: "Has Associate Editor?", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "editor_group", field: "admin.editor_group.exact", display: "Editor Group", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "editor", field: "admin.editor.exact", display: "Editor", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "author_pays", field: "index.has_apc.exact", display: "Publication charges?", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "classification", field: "index.classification.exact", display: "Classification", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "language", field: "index.language.exact", display: "Journal language", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "country_publisher", field: "index.country.exact", display: "Country of publisher", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "subject", field: "index.subject.exact", display: "Subject", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "publisher", field: "bibjson.publisher.name.exact", display: "Publisher", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "journal_license", field: "index.license.exact", display: "Journal license", deactivateThreshold: 1})
            ],
            sortOptions: [
                {'display': 'Date applied', 'field': 'admin.date_applied'},
                {'display': 'Last updated', 'field': 'last_manual_update'},
                {'display': 'Title', 'field': 'index.unpunctitle.exact'}
            ],
            fieldOptions: [
                {'display': 'Title', 'field': 'index.title'},
                {'display': 'Keywords', 'field': 'bibjson.keywords'},
                {'display': 'Classification', 'field': 'index.classification'},
                {'display': 'ISSN', 'field': 'index.issn.exact'},
                {'display': 'Country of publisher', 'field': 'index.country'},
                {'display': 'Journal language', 'field': 'index.language'},
                {'display': 'Publisher', 'field': 'bibjson.publisher.name'},
                {'display': 'Alternative Title', 'field': 'bibjson.alternative_title'}
            ],
            searchPlaceholder: "Search Applications in your Group(s)",
            sizeOptions: [10, 25, 50, 100],
            resultsDisplay: edges.newResultsDisplay({
                id: "results",
                category: "results",
                renderer: edges.bs3.newResultsFieldsByRowRenderer({
                    noResultsText: "<p>There are no applications for your editor group(s) that meet the search criteria</p>" +
                                   "<p>If you have not set any search criteria, this means there are no applications currently allocated to your group</p>",
                    rowDisplay: [
                        [{valueFunction: doaj.fieldRender.titleField}],
                        [{pre: '<span class="alt_title">Alternative title: ', field: "bibjson.alternative_title", post: "</span>"}],
                        [{pre: "<strong>Date applied</strong>: ", valueFunction: doaj.fieldRender.suggestedOn}],
                        [{pre: "<strong>Last updated</strong>: ", valueFunction: doaj.fieldRender.lastManualUpdate}],
                        [{valueFunction: doaj.fieldRender.issns}],
                        [{pre: "<strong>Application status</strong>: ", valueFunction: doaj.fieldRender.applicationStatus}],
                        [{pre: "<strong>Editor Group</strong>: ", field: "admin.editor_group"}],
                        [{pre: "<strong>Editor</strong>: ", field: "admin.editor"}],
                        [{pre: "<strong>Classification</strong>: ", field: "index.classification"}],
                        [{pre: "<strong>Keywords</strong>: ", field: "bibjson.keywords"}],
                        [{pre: "<strong>Publisher</strong>: ", field: "bibjson.publisher.name"}],
                        [{pre: "<strong>Publication charges?</strong>: ", valueFunction: doaj.fieldRender.authorPays}],
                        [{pre: "<strong>Country of publisher</strong>: ", valueFunction: doaj.fieldRender.countryName}],
                        [{pre: "<strong>Journal language</strong>: ", field: "bibjson.language"}],
                        [{pre: "<strong>Journal license</strong>: ", valueFunction: doaj.fieldRender.journalLicense}],
                        [{valueFunction: doaj.fieldRender.links}],
                        [
                            {valueFunction: doaj.fieldRender.readOnlyJournal({readOnlyJournalUrl: doaj.editorGroupApplicationsSearchConfig.readOnlyJournalUrl})},
                            {valueFunction: doaj.fieldRender.editSuggestion({editUrl: doaj.editorGroupApplicationsSearchConfig.applicationEditUrl})}
                        ]
                    ]
                })
            }),
            fieldDisplays: {
                'admin.application_status.exact': 'Application Status',
                'index.application_type.exact': 'Record type',
                'index.has_editor.exact': 'Has Associate Editor?',
                'admin.editor_group.exact': 'Editor Group',
                'admin.editor.exact': 'Editor',
                'index.classification.exact': 'Classification',
                'index.language.exact': 'Journal language',
                'index.country.exact': 'Country of publisher',
                'index.subject.exact': 'Subject',
                'bibjson.publisher.name.exact': 'Publisher',
                'index.license.exact': 'Journal license',
                'index.has_apc.exact': 'Publication charges?'
            },
            openingQuery: es.newQuery({
                sort: {"field": "admin.date_applied", "order": "asc"}
            })
        });

        doaj.editorGroupApplicationsSearch.activeEdges[selector] = e;
    }
}


jQuery(document).ready(function($) {
    doaj.editorGroupApplicationsSearch.init();
});
