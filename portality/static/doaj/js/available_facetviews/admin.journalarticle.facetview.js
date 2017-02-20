jQuery(document).ready(function($) {

    ////////////////////////////////////////////////////////////
    // functions for handling the bulk form

    autocomplete('#editor_group', 'name', 'editor_group', 1, false);

    toggle_optional_field('bulk_action', ['#editor_group'], ['assign_editor_group']);
    toggle_optional_field('bulk_action', ['#note'], ['add_note']);

    function disable_bulk_submit() {
        $('#bulk-submit').attr('disabled', 'disabled').html("Submit");
    }

    function enable_bulk_submit() {
        $('#bulk-submit').removeAttr('disabled').html("Submit");
    }

    function bulk_ui_reset() {
        disable_bulk_submit();
        $("#bulk_action").val("");
        $("#editor_group-container").hide();
        $("#note-container").hide();
        $("#journal_type_note").hide();
        $("#any_type_note").hide();
    }

    function bulk_action_controls(options) {
        var action = $('#bulk_action').val();
        if (action === "") {
            $("#journal_type_note").hide();
            $("#any_type_note").hide();
            disable_bulk_submit();
            return;
        }
        var type = options.active_filters._type;
        if (type && type.length > 0) {
            type = type[0];
        }

        // all the things we need to know to validate and determine whether to allow submit
        var requireJournalType = ["withdraw", "reinstate", "assign_editor_group", "add_note"];
        var requireAnyType = ["delete"];
        var requiresAdditional = ["assign_editor_group", "add_note"];
        var additional = {
            assign_editor_group : "#editor_group",
            add_note : "#note"
        };

        // work out whether we enable submit
        var enable = true;

        if ($.inArray(action, requireJournalType) > -1) {
            if (type !== "journal") {
                $("#journal_type_note").show();
                enable = false;
            } else {
                $("#journal_type_note").hide();
            }
        }

        if ($.inArray(action, requireAnyType) > -1) {
            if (type && type !== "") {
                $("#any_type_note").hide();
            } else {
                $("#any_type_note").show();
                enable = false;
            }
        }

        if ($.inArray(action, requiresAdditional) > -1) {
            var additionalVal = $(additional[action]).val();
            if (additionalVal === "") {
                enable = false;
            }
        }

        if (enable) {
            enable_bulk_submit();
        } else {
            disable_bulk_submit();
        }
    }

    function get_bulk_action() {
        var action = $('#bulk_action').val();
        if (!action) {
            alert('Error: unknown bulk operation.');
            throw 'Error: unknown bulk operation. The bulk action field was empty.'
        }
        return action
    }

    function bulk_action_type(options) {
        if (get_bulk_action() == 'delete') {
            if (! $.isEmptyObject(options.active_filters._type)) {
                if (options.active_filters._type.length != 1) {
                    alert('Error: type facet has multiple options selected.');
                    throw 'Error: type facet has multiple options selected.'
                }
                if (options.active_filters._type[0] === 'journal') { return 'journals'; }
                if (options.active_filters._type[0] === 'article') { return 'articles'; }
            }
        }
        return 'journals';
    }

    function bulk_action_url(options) {
        return '/admin/' + bulk_action_type(options) + '/bulk/' + get_bulk_action()
    }

    function build_affected_msg(data) {
        var mfrg = "";
        if (data.affected) {
            if ("journals" in data.affected && "articles" in data.affected) {
                mfrg += data.affected.journals + " journals and " + data.affected.articles + " articles";
            } else if ("journals" in data.affected) {
                mfrg = data.affected.journals + " journals";
            } else if ("articles" in data.affected) {
                mfrg = data.affected.articles + " articles";
            } else {
                mfrg = "an unknown number of records";
            }
        }
        return mfrg;
    }

    function bulk_action_success_callback(data) {
        var msg = "Your bulk edit request has been submitted and queued for execution.<br>";
        msg += build_affected_msg(data) + " have been queued for edit.<br>";
        msg += 'You can see your request <a href="' + bulk_job_url(data) + '" target="_blank">here</a> in the background jobs interface (opens new window).<br>';
        msg += "You will get an email when your request has been processed; this could take anything from a few minutes to a few hours<br>";
        msg += '<a href="#" id="bulk-action-feedback-dismiss">dismiss</a>';

        $(".bulk-action-feedback").html(msg).show();
        $("#bulk-action-feedback-dismiss").unbind("click").bind("click", function(event) {
            event.preventDefault();
            $(".bulk-action-feedback").html("").hide();
        });

        bulk_ui_reset();
    }

    function bulk_action_error_callback(jqXHR, textStatus, errorThrown) {
        alert('There was an error with your request.');
        console.error(textStatus + ': ' + errorThrown);
        bulk_ui_reset();
    }

    function bulk_action_confirm_closure(options, query) {
        var bulk_action_confirm_callback = function(data) {
            var sure = confirm('This operation will affect ' + build_affected_msg(data) + '.');
            if (sure) {
                var action = get_bulk_action();
                var send = {
                    selection_query: query,
                    dry_run: false
                };
                if (action === "add_note") {
                    send["note"] = $('#note').val();
                } else if (action === "assign_editor_group") {
                    send["editor_group"] = $('#editor_group').val();
                }
                $.ajax({
                    type: 'POST',
                    url: bulk_action_url(options),
                    data: JSON.stringify(send),
                    contentType : 'application/json',
                    success : bulk_action_success_callback,
                    error: bulk_action_error_callback
                });
            } else {
                bulk_ui_reset();
            }
        };

        return bulk_action_confirm_callback
    }
    
    function bulk_job_url(data) {
        var url = "/admin/background_jobs?source=%7B%22query%22%3A%7B%22query_string%22%3A%7B%22query%22%3A%22" + data.job_id + "%22%2C%22default_operator%22%3A%22AND%22%7D%7D%2C%22sort%22%3A%5B%7B%22created_date%22%3A%7B%22order%22%3A%22desc%22%7D%7D%5D%2C%22from%22%3A0%2C%22size%22%3A25%7D";
        return url;
    }

    ////////////////////////////////////////////////////////

    function adminJAPostRender(options, context) {
        doajJAPostRender(options, context);

        $('#bulk_action').change(function () {
            bulk_action_controls(options);
        });

        $("#editor_group").change(function() {
            if ($(this).val() === "") {
                disable_bulk_submit();
            } else {
                enable_bulk_submit();
            }
        });

        $("#note").keyup(function() {
            if ($(this).val() === "") {
                disable_bulk_submit();
            } else {
                enable_bulk_submit();
            }
        });

        $('#bulk-submit').unbind('click').bind('click', function(event) {
            event.preventDefault();

            $('#bulk-submit').attr('disabled', 'disabled').html("<img src='/static/doaj/images/white-transparent-loader.gif'>&nbsp;Submitting...");

            var sure;
            if ($('#bulk_action').val() == 'delete') {
                sure = confirm('Are you sure?  This operation cannot be undone!');
            } else {
                sure = true;
            }

            if (sure) {
                var query = elasticSearchQuery({
                    options: options,
                    include_facets: false,
                    include_fields: false
                });

                $.ajax({
                    type: 'POST',
                    url: bulk_action_url(options),
                    data: JSON.stringify({
                        selection_query: query,
                        editor_group: $('#editor_group').val(),
                        note: $('#note').val(),
                        dry_run: true
                    }),
                    contentType : 'application/json',
                    success : bulk_action_confirm_closure(options, query),
                    error: bulk_action_error_callback
                });
            } else {
                bulk_ui_reset();
            }
        });
    }

    /////////////////////////////////////////////////////////////////

    $('.facetview.admin_journals_and_articles').facetview({
        search_url: es_scheme + '//' + es_domain + '/admin_query/journal,article/_search?',

        render_results_metadata: doajPager,
        render_active_terms_filter: doajRenderActiveTermsFilter,
        post_render_callback: adminJAPostRender,
        post_search_callback: bulk_action_controls,

        sharesave_link: false,
        freetext_submit_delay: 1000,
        default_facet_hide_inactive: true,
        default_facet_operator: "AND",
        default_operator : "AND",

        facets: [
            {'field': '_type', 'display': 'Journals vs. Articles'},
            {'field': 'admin.in_doaj', 'display': 'In DOAJ?'},
            {'field': 'index.classification.exact', 'display': 'Subject'},
            {'field': 'index.language.exact', 'display': 'Journal Language'},
            {'field': 'index.publisher.exact', 'display': 'Publisher'},
            {'field': 'bibjson.provider.exact', 'display': 'Platform, Host, Aggregator'},
            {'field': 'index.classification.exact', 'display': 'Classification'},
            {'field': 'index.subject.exact', 'display': 'Subject'},
            {'field': 'index.language.exact', 'display': 'Journal Language'},
            {'field': 'index.country.exact', 'display': 'Country of publisher'},
            {'field': 'bibjson.author_pays.exact', 'display': 'Publication charges?'},
            {'field': 'index.license.exact', 'display': 'Journal License'},
            // Articles
            {'field': 'bibjson.author.exact', 'display': 'Author (Articles)'},
            {'field': 'bibjson.year.exact', 'display': 'Year of publication (Articles)'},
            {'field': 'bibjson.journal.title.exact', 'display': 'Journal title (Articles)'}
        ],

        search_sortby: [
            {'display':'Date added to DOAJ','field':'created_date'},
            {'display':'Last updated','field':'last_updated'},
            {'display':'Title','field':'index.unpunctitle.exact'},
            {'display':'Article: Publication date','field':['bibjson.year.exact', 'bibjson.month.exact']}
        ],

        searchbox_fieldselect: [
            {'display':'Title','field':'index.title'},
            {'display':'Keywords','field':'bibjson.keywords'},
            {'display':'Subject','field':'index.classification'},
            {'display':'Classification','field':'index.classification'},
            {'display':'ISSN', 'field':'index.issn.exact'},
            {'display':'DOI', 'field' : 'bibjson.identifier.id'},
            {'display':'Country of publisher','field':'index.country'},
            {'display':'Journal Language','field':'index.language'},
            {'display':'Publisher','field':'index.publisher'},

            {'display':'Article: Abstract','field':'bibjson.abstract'},
            {'display':'Article: Author','field':'bibjson.author'},
            {'display':'Article: Year','field':'bibjson.year'},
            {'display':'Article: Journal Title','field':'bibjson.journal.title'},

            {'display':'Journal: Alternative Title','field':'bibjson.alternative_title'},
            {'display':'Journal: Platform, Host, Aggregator','field':'bibjson.provider'}
        ],

        page_size : 10,
        from : 0,

        results_render_callbacks: {
            'bibjson.author_pays': fv_author_pays,
            'created_date': fv_created_date_with_time,
            'last_updated': fv_last_updated,
            'bibjson.abstract': fv_abstract,
            'addthis-social-share-button': fv_addthis,
            'journal_license' : fv_journal_license,
            "title_field" : fv_title_field,
            "doi_link" : fv_doi_link,
            "links" : fv_links,
            "issns" : fv_issns,
            "edit_journal": fv_edit_journal,
            "delete_article" : fv_delete_article,
            "in_doaj": fv_in_doaj,
            "country_name": fv_country_name
        },
        result_display: [
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
                    "field" : "title_field"
                }
                /*
                 {
                 "pre": '<span class="title">',
                 "field": "bibjson.title",
                 "post": "</span>"
                 }
                 */
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
                    "field" : "in_doaj"
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
                    "field": "bibjson.author_pays"
                }
            ],
            /*
             [
             {
             "pre": "<strong>More information on publishing charges</strong>: ",
             "field": "bibjson.author_pays_url",
             }
             ],
             */
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
                    "field" : "issns"
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
                    "field": "created_date"
                }
            ],
            [
                {
                    "pre": "<strong>Last updated</strong>: ",
                    "field": "last_updated"
                }
            ],
            [
                {
                    "pre": "<strong>DOI</strong>: ",
                    "field": "doi_link"
                }
            ],
            [
                {
                    "field" : "links"
                }
                /*
                 {
                 "pre": "<strong>More information - ",
                 "field": "bibjson.link.type",
                 "post": "</strong>: ",
                 },
                 {
                 "field": "bibjson.link.url",
                 },
                 */
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
                    "field": "journal_license"
                }
            ],
            [
                {
                    "pre": "<strong>Country of publisher</strong>: ",
                    "field": "country_name"
                }
            ],
            [
                {
                    "pre": '<strong>Abstract</strong>: ',
                    "field": "bibjson.abstract"
                }
            ],
            [
                {
                    "field": "edit_journal"
                },
                {
                    "field" : "delete_article"
                }
            ]
        ]
    });
});
