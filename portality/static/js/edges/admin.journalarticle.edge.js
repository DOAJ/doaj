// ~~ AdminJournalsArticlesSearch:Feature ~~
doaj.adminJournalArticleSearch = {
    activeEdges : {},

    journalSelected : function(selector) {
        return function() {
            var type = doaj.adminJournalArticleSearch.activeEdges[selector].currentQuery.listMust(es.newTermFilter({field: "es_type.exact"}));
            if (type && type.length > 0) {
                type = type[0];
            }
            if (!type || type.value !== "journal") {
                return {valid: false, error_id: "journal_type_error"}
            }
            return {valid: true};
        }
    },

    anySelected : function(selector) {
        return function() {
            var type = doaj.adminJournalArticleSearch.activeEdges[selector].currentQuery.listMust(es.newTermFilter({field: "es_type.exact"}));
            if (!type || type.length === 0) {
                return {valid: false, error_id: "any_type_error"}
            }
            return {valid: true};
        }
    },

    typeSelected : function(selector) {
        return function() {
            var type = doaj.adminJournalArticleSearch.activeEdges[selector].currentQuery.listMust(es.newTermFilter({field: "es_type.exact"}));
            if (type && type.length > 0) {
                return type[0].value;
            }
            return null;
        }
    },

    lastUpdated : function(val, resultobj, renderer) {
        return doaj.dates.humanYearMonth(resultobj['last_updated']);
    },

    deleteArticle : function(val, resultobj, renderer) {
        if (!resultobj.suggestion && resultobj.bibjson.journal) {
            var result = '<br/>'
            result += '<a class="delete_article_link button" href="';
            result += "/admin/delete/article/";
            result += resultobj['id'];
            result += '" target="_blank"';
            result += ' style="margin-bottom: 0;">Delete this article</a>';
            return result;
        }
        return false;
    },

    editArticle : function(val, resultobj, renderer) {
        if (!resultobj.suggestion && resultobj.bibjson.journal) {
            var result = '<p><a class="edit_article_link button" href="';
            result += doaj.adminJournalArticleSearchConfig.articleEditUrl;
            result += resultobj['id'];
            result += '" target="_blank"';
            result += ' style="margin-bottom: .75em;">Edit this article</a></p>';
            return result;
        }
        return false;
    },

    editJournal : function(val, resultobj, renderer) {
        if (!resultobj.suggestion && !resultobj.bibjson.journal) {
            var result = '<p><a class="edit_journal_link button" href="';
            result += doaj.adminJournalArticleSearchConfig.journalEditUrl;
            result += resultobj['id'];
            result += '" target="_blank"';
            result += 'style="margin-bottom: .75em;">Edit this journal</a></p>';
            return result;
        }
        return false;
    },

    init : function(params) {
        if (!params) { params = {} }

        var selector = params.selector || "#admin_journals_and_articles";

        var journalSelected = doaj.adminJournalArticleSearch.journalSelected(selector);
        var anySelected = doaj.adminJournalArticleSearch.anySelected(selector);
        var typeSelected = doaj.adminJournalArticleSearch.typeSelected(selector);

        var e = doaj.components.makeSearch({
            selector: selector,
            searchUrl: doaj.buildUrl(doaj.adminJournalArticleSearchConfig.searchPath),
            facets: [
                doaj.components.refiningAndFacet({id: "journals_articles", field: "es_type.exact", display: "Journals vs Articles", valueMap: {"journal": "Journals", "article": "Articles"}}),
                doaj.facets.inDOAJ(),
                doaj.components.refiningAndFacet({id: "author_pays", field: "index.has_apc.exact", display: "Publication charges?", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "journal_language", field: "index.language.exact", display: "Journal language", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "publisher", field: "bibjson.publisher.name.exact", display: "Publisher", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "classification", field: "index.classification.exact", display: "Classification", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "subject", field: "index.subject.exact", display: "Subject", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "country_publisher", field: "index.country.exact", display: "Country of publisher", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "journal_license", field: "index.license.exact", display: "Journal license", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "publication_year", field: "bibjson.year.exact", display: "Year of publication (Articles)", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "journal_title", field: "bibjson.journal.title.exact", display: "Journal title (Articles)", deactivateThreshold: 1})
            ],
            sortOptions: [
                {'display': 'Date added to DOAJ', 'field': 'created_date'},
                {'display': 'Last updated', 'field': 'last_updated'},
                {'display': 'Title', 'field': 'index.unpunctitle.exact'},
                {'display': 'Article: Publication date', 'field': 'index.date'}
            ],
            fieldOptions: [
                {'display': 'Title', 'field': 'index.title'},
                {'display': 'Keywords', 'field': 'bibjson.keywords'},
                {'display': 'Subject', 'field': 'index.classification'},
                {'display': 'Classification', 'field': 'index.classification'},
                {'display': 'ISSN', 'field': 'index.issn.exact'},
                {'display': 'DOI', 'field': 'bibjson.identifier.id'},
                {'display': 'Country of publisher', 'field': 'index.country'},
                {'display': 'Journal language', 'field': 'index.language'},
                {'display': 'Journal: Publisher', 'field': 'bibjson.publisher.name'},
                {'display': 'Article: Abstract', 'field': 'bibjson.abstract'},
                {'display': 'Article: Author\'s name', 'field': 'bibjson.author.name'},
                {'display': 'Article: Author\'s ORCID iD', 'field': 'bibjson.author.orcid_id'},
                {'display': 'Article: Year', 'field': 'bibjson.year'},
                {'display': 'Article: Journal title', 'field': 'bibjson.journal.title'},
                {'display': 'Journal: Alternative Title', 'field': 'bibjson.alternative_title'}
            ],
            searchPlaceholder: "Search all journals and articles",
            sizeOptions: [10, 25, 50, 100],
            resultsDisplay: edges.newResultsDisplay({
                id: "results",
                category: "results",
                renderer: edges.bs3.newResultsFieldsByRowRenderer({
                    rowDisplay: [
                        [{pre: "<strong>ID</strong>: ", field: "id"}],
                        [{valueFunction: doaj.fieldRender.titleField}],
                        [{valueFunction: doaj.adminJournalArticleSearch.editArticle}],
                        [{valueFunction: doaj.adminJournalArticleSearch.editJournal}],
                        [{pre: '<span class="alt_title">Alternative title: ', field: "bibjson.alternative_title", post: "</span>"}],
                        [{pre: "<strong>In DOAJ?</strong>: ", valueFunction: doaj.fieldRender.inDoaj}],
                        [{pre: "<strong>Classification</strong>: ", field: "index.classification"}],
                        [{pre: "<strong>Publisher</strong>: ", field: "bibjson.publisher.name"}],
                        [{pre: "<strong>Publication charges?</strong>: ", valueFunction: doaj.fieldRender.authorPays}],
                        [{pre: "<strong>Journal language</strong>: ", field: "bibjson.language"}],
                        [{pre: "<strong>Authors</strong>: ", field: "bibjson.author.name"}],
                        [{pre: "<strong>Publisher</strong>: ", field: "bibjson.journal.publisher"}],
                        [
                            {pre: '<strong>Date of publication</strong>: ', field: "bibjson.year"},
                            {pre: ' <span class="date-month">', field: "bibjson.month", post: "</span>"}
                        ],
                        [
                            {pre: "<strong>Published in</strong>: ", field: "bibjson.journal.title", notrailingspace: true},
                            {pre: ", Vol ", field: "bibjson.journal.volume", notrailingspace: true},
                            {pre: ", Iss ", field: "bibjson.journal.number", notrailingspace: true},
                            {pre: ", Pp ", field: "bibjson.start_page", notrailingspace: true},
                            {pre: "-", field: "bibjson.end_page"},
                            {pre: "(", field: "bibjson.year", post: ")"}
                        ],
                        [{valueFunction: doaj.fieldRender.issns}],
                        [{pre: "<strong>Keywords</strong>: ", field: "bibjson.keywords"}],
                        [{pre: "<strong>Discontinued Date</strong>: ", field: "bibjson.discontinued_date"}],
                        [{pre: "<strong>Date added to DOAJ</strong>: ", valueFunction: doaj.fieldRender.createdDateWithTime}],
                        [{pre: "<strong>Last updated</strong>: ", valueFunction: doaj.adminJournalArticleSearch.lastUpdated}],
                        [{pre: "<strong>DOI</strong>: ", valueFunction: doaj.fieldRender.doiLink}],
                        [{valueFunction: doaj.fieldRender.links}],
                        [{pre: "<strong>Journal language(s)</strong>: ", field: "bibjson.journal.language"}],
                        [{pre: "<strong>Journal license</strong>: ", valueFunction: doaj.fieldRender.journalLicense}],
                        [{pre: "<strong>Country of publisher</strong>: ", valueFunction: doaj.fieldRender.countryName}],
                        [{pre: '<strong>Abstract</strong>: ', valueFunction: doaj.fieldRender.abstract}],
                        [{valueFunction: doaj.adminJournalArticleSearch.deleteArticle}]
                    ]
                })
            }),
            fieldDisplays: {
                "es_type.exact": "Showing",
                "admin.in_doaj": "In DOAJ?",
                "index.language.exact": "Language",
                "bibjson.publisher.name.exact": "Publisher",
                "index.classification.exact": "Classification",
                "index.subject.exact": "Subject",
                "index.country.exact": "Country",
                "index.license.exact": "License",
                "bibjson.year.exact": "Year of publication",
                "bibjson.journal.title.exact": "Title",
                "index.has_apc.exact": "Charges?"
            },
            valueMaps: {
                "es_type.exact": {"journal": "Journals", "article": "Articles"},
                "admin.in_doaj": {true: "Yes", false: "No"}
            },
            callbacks: {
                "edges:pre-render": function() {
                    doaj.multiFormBox.active.validate();
                },
                "edges:post-render": function() {
                    $(".abstract_action").off("click").on("click", function(event) {
                        event.preventDefault();
                        var el = $(this);
                        var at = $(".abstract_text").filter('[rel="' + el.attr("rel") + '"]');
                        at.slideToggle(300);
                    });

                    $(".delete_article_link").off("click").on("click", function(event) {
                        event.preventDefault();

                        function success_callback(data) {
                            alert("The article was successfully deleted");
                            doaj.adminJournalArticleSearch.activeEdges[selector].cycle();
                        }

                        function error_callback() {
                            alert("There was an error deleting the article")
                        }

                        var c = confirm("Are you really really sure?  You can't undo this operation!");
                        if (c) {
                            var href = $(this).attr("href");
                            var obj = {"delete": "true"};
                            $.ajax({
                                type: "POST",
                                url: href,
                                data: obj,
                                success: success_callback,
                                error: error_callback
                            })
                        }
                    });
                }
            }
        });

        doaj.adminJournalArticleSearch.activeEdges[selector] = e;

        doaj.multiFormBox.active = doaj.multiFormBox.newMultiFormBox({
            edge: e,
            selector: "#admin-bulk-box",
            bindings: {
                editor_group: function(context) {
                    autocomplete($('#editor_group', context), 'name', 'editor_group', 1, false);
                },
                edit_metadata: function(context) {
                    autocomplete($('#publisher_name', context), 'bibjson.publisher.name');
                    $('#publisher_country', context).select2();
                    autocomplete($('#owner', context), 'id', 'account');
                }
            },
            validators: {
                withdraw: journalSelected,
                reinstate: journalSelected,
                delete: anySelected,
                note: function(context) {
                    var valid = journalSelected();
                    if (!valid.valid) { return valid; }
                    var val = context.find("#note").val();
                    if (val === "") { return {valid: false}; }
                    return {valid: true};
                },
                editor_group: function(context) {
                    var valid = journalSelected();
                    if (!valid.valid) { return valid; }
                    var val = context.find("#editor_group").val();
                    if (val === "") { return {valid: false}; }
                    return {valid: true};
                },
                edit_metadata: function(context) {
                    var valid = journalSelected();
                    if (!valid.valid) { return valid; }
                    var found = false;
                    var fields = ["#publisher_name", "#publisher_country", "#owner"];
                    for (var i = 0; i < fields.length; i++) {
                        if (context.find(fields[i]).val() !== "") { found = true; }
                    }
                    if (!found) { return {valid: false}; }
                    return {valid: true};
                }
            },
            submit: {
                delete: {sure: 'Are you sure?  This operation cannot be undone!'},
                note: {
                    data: function(context) {
                        return {note: $('#note', context).val()};
                    }
                },
                editor_group: {
                    data: function(context) {
                        return {editor_group: $('#editor_group', context).val()};
                    }
                },
                edit_metadata: {
                    data: function(context) {
                        return {
                            metadata: {
                                publisher_name: $('#publisher_name', context).select2("val"),
                                publisher_country: $('#publisher_country', context).select2("val"),
                                owner: $('#owner', context).select2("val")
                            }
                        };
                    }
                }
            },
            urls: {
                withdraw: "/admin/journals/bulk/withdraw",
                reinstate: "/admin/journals/bulk/reinstate",
                delete: function() {
                    var type = typeSelected();
                    if (type === "journal") { return "/admin/journals/bulk/delete"; }
                    else if (type === "article") { return "/admin/articles/bulk/delete"; }
                    return null;
                },
                note: "/admin/journals/bulk/add_note",
                editor_group: "/admin/journals/bulk/assign_editor_group",
                edit_metadata: "/admin/journals/bulk/edit_metadata"
            }
        });
    }
}


jQuery(document).ready(function($) {
    doaj.adminJournalArticleSearch.init();
});
