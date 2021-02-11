$.extend(true, doaj, {

    adminJournalArticleSearch : {
        activeEdges : {},

        journalSelected : function(selector) {
            return function() {
                var type = doaj.adminJournalArticleSearch.activeEdges[selector].currentQuery.listMust(es.newTermFilter({field: "es_type"}));
                // var type = doaj.currentFVOptions.active_filters._type;
                if (type && type.length > 0) {
                    type = type[0];
                }
                if (!type || type.value !== "journal") {
                    return {
                        valid: false,
                        error_id: "journal_type_error"
                    }
                }
                return {valid : true};
            }
        },

        anySelected : function(selector) {
            return function() {
                var type = doaj.adminJournalArticleSearch.activeEdges[selector].currentQuery.listMust(es.newTermFilter({field: "es_type"}));
                if (!type || type.length === 0) {
                    return {
                        valid: false,
                        error_id: "any_type_error"
                    }
                }
                return {valid: true};
            }
        },

        typeSelected : function(selector) {
            return function() {
                var type = doaj.adminJournalArticleSearch.activeEdges[selector].currentQuery.listMust(es.newTermFilter({field: "es_type"}));
                if (type && type.length > 0) {
                    return type[0].value;
                }
                return null;
            }
        },

        lastUpdated : function (val, resultobj, renderer) {
            return doaj.iso_datetime2date_and_time(resultobj['last_updated']);
        },

        deleteArticle : function (val, resultobj, renderer) {
            if (!resultobj.suggestion && resultobj.bibjson.journal) {
                // if it's not a suggestion or a journal .. (it's an article!)
                // we really need to expose _type ...
                var result = '<br/>'
                result += '<a class="delete_article_link button" href="';
                result += "/admin/delete/article/";
                result += resultobj['id'];
                result += '" target="_blank"';
                result += '>Delete this article</a>';
                return result;
            }
            return false;
        },

        editArticle : function (val, resultobj, renderer) {
            if (!resultobj.suggestion && resultobj.bibjson.journal) {
                var result = '<a class="edit_article_link button" href="';
                result += doaj.adminJournalArticleSearchConfig.articleEditUrl;
                result += resultobj['id'];
                result += '" target="_blank"';
                result += '>Edit this article</a>';
                return result;
            }
            return false;
        },

        editJournal : function (val, resultobj, renderer) {
            if (!resultobj.suggestion && !resultobj.bibjson.journal) {
                // if it's not a suggestion or an article .. (it's a
                // journal!)
                // we really need to expose _type ...
                var result = '<a class="edit_journal_link button" href="';
                result += doaj.adminJournalArticleSearchConfig.journalEditUrl;
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

            var selector = params.selector || "#admin_journals_and_articles";
            var search_url = current_scheme + "//" + current_domain + doaj.adminJournalArticleSearchConfig.searchPath;

            var journalSelected = doaj.adminJournalArticleSearch.journalSelected(selector);
            var anySelected = doaj.adminJournalArticleSearch.anySelected(selector);
            var typeSelected = doaj.adminJournalArticleSearch.typeSelected(selector);

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                // facets
                edges.newRefiningANDTermSelector({
                    id: "journals_articles",
                    category: "facet",
                    field: "es_type",
                    display: "Journals vs Articles",
                    valueMap : {
                        "journal" : "Journals",
                        "article" : "Articles"
                    },
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "in_doaj",
                    category: "facet",
                    field: "admin.in_doaj",
                    display: "In DOAJ?",
                    deactivateThreshold: 1,
                    valueMap : {
                        "T" : "True",
                        "F" : "False"
                    },
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
                    id: "journal_language",
                    category: "facet",
                    field: "index.language.exact",
                    display: "Journal Language",
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
                    id: "journal_license",
                    category: "facet",
                    field: "index.license.exact",
                    display: "Journal License",
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
                    id: "publication_year",
                    category: "facet",
                    field: "bibjson.year.exact",
                    display: "Year of publication (Articles)",
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
                    field: "bibjson.journal.title.exact",
                    display: "Journal title (Articles)",
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
                        {'display':'Last updated','field':'last_updated'},
                        {'display':'Title','field':'index.unpunctitle.exact'},
                        {'display':'Article: Publication date','field':"index.date"}
                    ],
                    fieldOptions: [
                        {'display':'Title','field':'index.title'},
                        {'display':'Keywords','field':'bibjson.keywords'},
                        {'display':'Subject','field':'index.classification'},
                        {'display':'Classification','field':'index.classification'},
                        {'display':'ISSN', 'field':'index.issn.exact'},
                        {'display':'DOI', 'field' : 'bibjson.identifier.id'},
                        {'display':'Country of publisher','field':'index.country'},
                        {'display':'Journal Language','field':'index.language'},
                        {'display':'Publisher','field':'bibjson.publisher.name'},

                        {'display':'Article: Abstract','field':'bibjson.abstract'},
                        {'display':'Article: Author\'s name','field':'bibjson.author.name'},
                        {'display':'Article: Author\'s ORCID iD','field':'bibjson.author.orcid_id'},
                        {'display':'Article: Year','field':'bibjson.year'},
                        {'display':'Article: Journal Title','field':'bibjson.journal.title'},

                        {'display':'Journal: Alternative Title','field':'bibjson.alternative_title'}
                    ],
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: -1,
                        searchButton: true,
                        searchPlaceholder: "Search All Journals and Articles"
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
                                    "pre" : "<strong>ID</strong>: <em>",
                                    "field" : "id",
                                    "post": "</em>"
                                }
                            ],
                            // Journals
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
                                    "valueFunction" : doaj.fieldRender.inDoaj
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
                                    "pre": "<strong>Publisher</strong>: ",
                                    "field": "bibjson.publisher.name"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Publication charges?</strong>: ",
                                    "valueFunction": doaj.fieldRender.authorPays
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Journal Language</strong>: ",
                                    "field": "bibjson.language"
                                }
                            ],
                            // Articles
                            [
                                {
                                    "pre": "<strong>Authors</strong>: ",
                                    "field": "bibjson.author.name"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Publisher</strong>: ",
                                    "field": "bibjson.journal.publisher"
                                }
                            ],
                            [
                                {
                                    "pre":'<strong>Date of publication</strong>: ',
                                    "field": "bibjson.year"
                                },
                                {
                                    "pre":' <span class="date-month">',
                                    "field": "bibjson.month",
                                    "post": "</span>"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Published in</strong>: ",
                                    "field": "bibjson.journal.title",
                                    "notrailingspace": true
                                },
                                {
                                    "pre": ", Vol ",
                                    "field": "bibjson.journal.volume",
                                    "notrailingspace": true
                                },
                                {
                                    "pre": ", Iss ",
                                    "field": "bibjson.journal.number",
                                    "notrailingspace": true
                                },
                                {
                                    "pre": ", Pp ",
                                    "field": "bibjson.start_page",
                                    "notrailingspace": true
                                },
                                {
                                    "pre": "-",
                                    "field": "bibjson.end_page"
                                },
                                {
                                    "pre" : "(",
                                    "field": "bibjson.year",
                                    "post" : ")"
                                }
                            ],
                            [
                                {
                                    "pre" : "<strong>ISSN(s)</strong>: ",
                                    "valueFunction" : doaj.fieldRender.issns
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
                                    "pre": "<strong>Discontinued Date</strong>: ",
                                    "field": "bibjson.discontinued_date"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Date added to DOAJ</strong>: ",
                                    "valueFunction": doaj.fieldRender.createdDateWithTime
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Last updated</strong>: ",
                                    "valueFunction": doaj.adminJournalArticleSearch.lastUpdated
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>DOI</strong>: ",
                                    "valueFunction": doaj.fieldRender.doiLink
                                }
                            ],
                            [
                                {
                                    "valueFunction" : doaj.fieldRender.links
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Journal Language(s)</strong>: ",
                                    "field": "bibjson.journal.language"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Journal License</strong>: ",
                                    "valueFunction": doaj.fieldRender.journalLicense
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Country of publisher</strong>: ",
                                    "valueFunction": doaj.fieldRender.countryName
                                }
                            ],
                            [
                                {
                                    "pre": '<strong>Abstract</strong>: ',
                                    "valueFunction": doaj.fieldRender.abstract
                                }
                            ],
                            [
                                {
                                    "valueFunction": doaj.adminJournalArticleSearch.editJournal
                                },
                                {
                                    "valueFunction": doaj.adminJournalArticleSearch.deleteArticle
                                },
                                {
                                    "valueFunction": doaj.adminJournalArticleSearch.editArticle
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
                        "es_type": "Showing",
                        "admin.in_doaj" : "In DOAJ?",
                        "index.language.exact" : "Journal Language",
                        "bibjson.publisher.name.exact" : "Publisher",
                        "index.classification.exact" : "Classification",
                        "index.subject.exact" : "Subject",
                        "index.country.exact" : "Country of publisher",
                        "index.license.exact" : "Journal License",
                        "bibjson.year.exact" : "Year of publication",
                        "bibjson.journal.title.exact" : "Journal title",
                        "index.has_apc.exact" : "Publication charges?"
                    },
                    valueMaps : {
                        "es_type" : {
                            "journal" : "Journals",
                            "article" : "Articles"
                        },
                        "admin.in_doaj" : {
                            "T" : "True",
                            "F" : "False"
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
                components: components,
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact an administrator.");
                    }
                }
            });
            doaj.adminJournalArticleSearch.activeEdges[selector] = e;

            var mfb = doaj.multiFormBox.newMultiFormBox({
                edge : e,
                selector: "#admin-bulk-box",
                bindings : {
                    editor_group : function(context) {
                        autocomplete($('#editor_group', context), 'name', 'editor_group', 1, false);
                    },
                    edit_metadata : function(context) {
                        autocomplete($('#publisher_name', context), 'bibjson.publisher.name');
                        $('#publisher_country', context).select2();
                        autocomplete($('#owner', context), 'id', 'account');
                    }
                },
                validators : {
                    withdraw : journalSelected,
                    reinstate: journalSelected,
                    delete: anySelected,
                    note : function(context) {
                        var valid = journalSelected();
                        if (!valid.valid) {
                            return valid;
                        }
                        var val = context.find("#note").val();
                        if (val === "") {
                            return {valid: false};
                        }
                        return {valid: true};
                    },
                    editor_group : function(context) {
                        var valid = journalSelected();
                        if (!valid.valid) {
                            return valid;
                        }
                        var val = context.find("#editor_group").val();
                        if (val === "") {
                            return {valid: false};
                        }
                        return {valid: true};
                    },
                    edit_metadata : function(context) {
                        // first check that the journal has been selected
                        var valid = journalSelected();
                        if (!valid.valid) {
                            return valid;
                        }

                        // now check that at least one field has been completed
                        var found = false;
                        var fields = ["#publisher_name", "#publisher_country", "#owner", "#doaj_seal"];
                        for (var i = 0; i < fields.length; i++) {
                            var val = context.find(fields[i]).val();
                            if (val !== "") {
                                found = true;
                            }
                        }
                        if (!found) {
                            return {valid: false};
                        }

                        return {valid: true};
                    }
                },
                submit : {
                    delete : {
                        sure : 'Are you sure?  This operation cannot be undone!'
                    },
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
                    edit_metadata : {
                        data : function(context) {
                            var seal = $('#change_doaj_seal', context).val();
                            if (seal === "True") {
                                seal = true;
                            } else if (seal === "False") {
                                seal = false;
                            }
                            var data = {
                                metadata : {
                                    publisher_name: $('#publisher_name', context).select2("val"),
                                    publisher_country: $('#publisher_country', context).select2("val"),
                                    owner: $('#owner', context).select2("val"),
                                    change_doaj_seal: seal
                                }
                            };
                            return data;
                        }
                    }
                },
                urls : {
                    withdraw: "/admin/journals/bulk/withdraw",
                    reinstate: "/admin/journals/bulk/reinstate",
                    delete : function() {
                        var type = typeSelected();
                        if (type === "journal") {
                            return "/admin/journals/bulk/delete"
                        } else if (type === "article") {
                            return "/admin/articles/bulk/delete"
                        }
                        return null;
                    },
                    note : "/admin/journals/bulk/add_note",
                    editor_group : "/admin/journals/bulk/assign_editor_group",
                    edit_metadata : "/admin/journals/bulk/edit_metadata"
                }
            });
            doaj.multiFormBox.active = mfb;

            $(selector).on("edges:pre-render", function() {
                doaj.multiFormBox.active.validate();
            });

            // now bind the abstract expander
            $(selector).on("edges:post-render", function() {
                $(".abstract_action").off("click").on("click", function(event) {
                    event.preventDefault();
                    var el = $(this);
                    var at = $(".abstract_text").filter('[rel="' + el.attr("rel") + '"]');
                    at.slideToggle(300);
                });

                // now add the handlers for the article delete
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
                        var obj = {"delete" : "true"};
                        $.ajax({
                            type: "POST",
                            url: href,
                            data: obj,
                            success : success_callback,
                            error: error_callback
                        })
                    }
                });
            });
        }
    }
});


jQuery(document).ready(function($) {
    doaj.adminJournalArticleSearch.init();
});
