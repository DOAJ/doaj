// ~~ AdminUpdateRequestSearch:Feature ~~
doaj.adminApplicationsSearch = {
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

        var selector = params.selector || "#admin_applications";

        var e = doaj.components.makeSearch({
            selector: selector,
            searchUrl: doaj.buildUrl(doaj.adminApplicationsSearchConfig.searchPath),
            facets: [
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
                doaj.facets.journalLicence()
            ],
            sortOptions: [
                {'display': 'Date applied', 'field': 'admin.date_applied'},
                {'display': 'Last updated', 'field': 'last_manual_update'},
                {'display': 'Title', 'field': 'index.unpunctitle.exact'},
                {'display': 'Flag deadline', 'field': 'index.most_urgent_flag_deadline'}
            ],
            fieldOptions: [
                {'display': 'Title', 'field': 'index.title'},
                {'display': 'Keywords', 'field': 'bibjson.keywords'},
                {'display': 'Classification', 'field': 'index.classification'},
                {'display': 'ISSN', 'field': 'index.issn.exact'},
                {'display': 'Country of publisher', 'field': 'index.country'},
                {'display': 'Journal language', 'field': 'index.language'},
                {'display': 'Publisher', 'field': 'bibjson.publisher.name'},
                {'display': 'Journal: Alternative Title', 'field': 'bibjson.alternative_title'},
                {'display': 'Notes', 'field': 'admin.notes.note'}
            ],
            searchPlaceholder: "Search All Applications",
            resultsDisplay: edges.newResultsDisplay({
                id: "results",
                category: "results",
                renderer: edges.bs3.newResultsFieldsByRowRenderer({
                    rowDisplay: [
                        [{valueFunction: doaj.fieldRender.titleField}],
                        [{valueFunction: doaj.fieldRender.editSuggestion({editUrl: doaj.adminApplicationsSearchConfig.applicationEditUrl})}],
                        [{pre: '<span class="alt_title">Alternative title: ', field: "bibjson.alternative_title", post: "</span>"}],
                        [{valueFunction: doaj.fieldRender.deadline}],
                        [{pre: "<strong>Date applied</strong>: ", valueFunction: doaj.fieldRender.suggestedOn}],
                        [{pre: "<strong>Last updated</strong>: ", valueFunction: doaj.fieldRender.lastManualUpdate}],
                        [{pre: "<strong>Owner</strong>: ", valueFunction: doaj.fieldRender.owner}],
                        [{valueFunction: doaj.fieldRender.issns}],
                        [{pre: "<strong>Application status</strong>: ", valueFunction: doaj.fieldRender.applicationStatus}],
                        [{pre: "<strong>Editor Group</strong>: ", field: "admin.editor_group"}],
                        [{pre: "<strong>Classification</strong>: ", field: "index.classification"}],
                        [{pre: "<strong>Keywords</strong>: ", field: "bibjson.keywords"}],
                        [{pre: "<strong>Publisher</strong>: ", field: "bibjson.publisher.name"}],
                        [{pre: "<strong>Publication charges?</strong>: ", valueFunction: doaj.fieldRender.authorPays}],
                        [{pre: "<strong>Country of publisher</strong>: ", valueFunction: doaj.fieldRender.countryName}],
                        [{pre: "<strong>Journal language</strong>: ", field: "bibjson.language"}],
                        [{pre: "<strong>Journal license</strong>: ", valueFunction: doaj.fieldRender.journalLicense}],
                        [{valueFunction: doaj.fieldRender.links}],
                        [{valueFunction: doaj.adminApplicationsSearch.relatedJournal}]
                    ]
                })
            }),
            fieldDisplays: {
                'admin.application_status.exact': 'Status',
                'index.application_type.exact': 'Update Request',
                'index.has_editor_group.exact': 'Editor Group?',
                'index.has_editor.exact': 'Associate Editor?',
                'admin.editor_group.exact': 'Editor Group',
                'admin.editor.exact': 'Editor',
                'index.classification.exact': 'Classification',
                'index.language.exact': 'Language',
                'index.country.exact': 'Country',
                'index.subject.exact': 'Subject',
                'bibjson.publisher.name.exact': 'Publisher',
                'bibjson.provider.exact': 'Platform, Host, Aggregator',
                'index.has_apc.exact': 'Charges?',
                'index.license.exact': 'License',
                'index.is_flagged': "Only Flagged Records",
                'index.flag_assignees.exact': "Flagged to me"
            },
            valueMaps: {
                "index.application_type.exact": {
                    "finished application/update": "Closed",
                    "update request": "Open",
                    "new application": "Open"
                }
            },
            selectedFiltersRenderer: doaj.renderers.newSelectedFiltersRenderer({
                hideValues: [
                    'index.is_flagged',
                    'index.flag_assignees.exact'
                ]
            }),
            openingQuery: es.newQuery({
                sort: {"field": "admin.date_applied", "order": "asc"}
            }),
            callbacks: {
                "edges:pre-render": function() {
                    doaj.multiFormBox.active.validate();
                }
            }
        });

        doaj.adminApplicationsSearch.activeEdges[selector] = e;
        doaj.multiFormBox.active = doaj.bulk.applicationMultiFormBox(e, "update_requests");
    }
}


jQuery(document).ready(function($) {
    doaj.adminApplicationsSearch.init();
});
