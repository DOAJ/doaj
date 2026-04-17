doaj.editorGroupJournalsSearch = {
    activeEdges : {},

    init : function(params) {
        if (!params) { params = {} }

        var selector = params.selector || "#group_journals";

        var e = doaj.components.makeSearch({
            selector: selector,
            searchUrl: doaj.build(doaj.editorGroupJournalsSearchConfig.searchPath),
            facets: [
                doaj.facets.inDOAJ(),
                doaj.components.refiningAndFacet({id: "owner", field: "admin.owner.exact", display: "Owner", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "has_associate_editor", field: "index.has_editor.exact", display: "Has Associate Editor?", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "editor_group", field: "admin.editor_group.exact", display: "Editor Group", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "associate_editor", field: "admin.editor.exact", display: "Associate Editor", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "author_pays", field: "index.has_apc.exact", display: "Publication charges?", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "journal_license", field: "index.license.exact", display: "Journal license", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "publisher", field: "bibjson.publisher.name.exact", display: "Publisher", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "classification", field: "index.classification.exact", display: "Classification", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "subject", field: "index.subject.exact", display: "Subject", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "journal_language", field: "index.language.exact", display: "Journal language", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "country_publisher", field: "index.country.exact", display: "Country of publisher", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "journal_title", field: "index.title.exact", display: "Journal title", deactivateThreshold: 1})
            ],
            sortOptions: [
                {'display': 'Date added to DOAJ', 'field': 'created_date'},
                {'display': 'Last updated', 'field': 'last_manual_update'},
                {'display': 'Title', 'field': 'index.unpunctitle.exact'}
            ],
            fieldOptions: [
                {'display': 'Owner', 'field': 'admin.owner'},
                {'display': 'Title', 'field': 'index.title'},
                {'display': 'Alternative Title', 'field': 'bibjson.alternative_title'},
                {'display': 'Subject', 'field': 'index.subject'},
                {'display': 'Classification', 'field': 'index.classification'},
                {'display': 'ISSN', 'field': 'index.issn.exact'},
                {'display': 'Country of publisher', 'field': 'index.country'},
                {'display': 'Journal language', 'field': 'index.language'},
                {'display': 'Publisher', 'field': 'bibjson.publisher.name'}
            ],
            searchPlaceholder: "Search Journals in your Group(s)",
            sizeOptions: [10, 25, 50, 100],
            resultsDisplay: edges.newResultsDisplay({
                id: "results",
                category: "results",
                renderer: edges.bs3.newResultsFieldsByRowRenderer({
                    noResultsText: "<p>There are no journals for your editor group(s) that meet the search criteria</p>" +
                                   "<p>If you have not set any search criteria, this means there are no journals currently allocated to your group</p>",
                    rowDisplay: [
                        [{valueFunction: doaj.fieldRender.titleField}],
                        [{pre: '<span class="alt_title">Alternative title: ', field: "bibjson.alternative_title", post: "</span>"}],
                        [{pre: "<strong>In DOAJ?</strong>: ", valueFunction: doaj.fieldRender.inDoaj}],
                        [{pre: "<strong>Owner</strong>: ", valueFunction: doaj.fieldRender.owner}],
                        [{pre: "<strong>Editor Group</strong>: ", field: "admin.editor_group"}],
                        [{pre: "<strong>Editor</strong>: ", field: "admin.editor"}],
                        [{valueFunction: doaj.fieldRender.issns}],
                        [{pre: "<strong>Date added to DOAJ</strong>: ", valueFunction: doaj.fieldRender.createdDateWithTime}],
                        [{pre: "<strong>Last updated</strong>: ", valueFunction: doaj.fieldRender.lastManualUpdate}],
                        [{valueFunction: doaj.fieldRender.links}],
                        [{pre: "<strong>License</strong>: ", valueFunction: doaj.fieldRender.journalLicense}],
                        [{pre: "<strong>Publisher</strong>: ", field: "bibjson.publisher.name"}],
                        [{pre: "<strong>Publication charges?</strong>: ", valueFunction: doaj.fieldRender.authorPays}],
                        [{pre: "<strong>Classification</strong>: ", field: "index.classification"}],
                        [{pre: "<strong>Keywords</strong>: ", field: "bibjson.keywords"}],
                        [{pre: "<strong>Country</strong>: ", valueFunction: doaj.fieldRender.countryName}],
                        [{pre: "<strong>Language</strong>: ", field: "bibjson.language"}],
                        [{valueFunction: doaj.fieldRender.editJournal({editUrl: doaj.editorGroupJournalsSearchConfig.journalEditUrl})}]
                    ]
                })
            }),
            fieldDisplays: {
                "admin.in_doaj": "In DOAJ?",
                "admin.owner.exact": "Owner",
                "index.has_editor.exact": "Associate Editor?",
                "admin.editor_group.exact": "Editor group",
                "admin.editor.exact": "Associate Editor",
                "index.license.exact": "License",
                "bibjson.publisher.name.exact": "Publisher",
                "index.classification.exact": "Classification",
                "index.subject.exact": "Subject",
                "index.language.exact": "Language",
                "index.country.exact": "Country",
                "index.title.exact": "Title",
                "index.has_apc.exact": "Charges?"
            },
            valueMaps: {
                "admin.in_doaj": {true: "True", false: "False"}
            },
            openingQuery: es.newQuery({
                sort: [{field: "created_date", order: "desc"}]
            })
        });

        doaj.editorGroupJournalsSearch.activeEdges[selector] = e;
    }
}

jQuery(document).ready(function($) {
    doaj.editorGroupJournalsSearch.init();
});
