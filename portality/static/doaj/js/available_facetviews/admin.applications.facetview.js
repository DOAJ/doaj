jQuery(document).ready(function($) {

    ////////////////////////////////////////////////////////////
    // functions for handling the bulk form


    /*
    toggle_optional_field('bulk_action', ['#editor_group'], ['assign_editor_group']);
    toggle_optional_field('bulk_action', ['#application_status'], ['change_status']);
    toggle_optional_field('bulk_action', ['#note'], ['add_note']);
    */
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
        $("#application_status-container").hide();
    }

    function bulk_action_controls(options) {
        var action = $('#bulk_action').val();
        if (action === "") {
            disable_bulk_submit();
            return;
        }

        var requiresAdditional = ["assign_editor_group", "add_note", "change_status"];
        var additional = {
            assign_editor_group : "#editor_group",
            add_note : "#note",
            change_status: "#application_status"
        };

        // work out whether we enable submit
        var enable = true;

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

    function bulk_action_url(options) {
        return '/admin/applications/bulk/' + get_bulk_action()
    }

    function build_affected_msg(data) {
        var mfrg = "";
        if (data.affected) {
            if ("applications" in data.affected) {
                mfrg += data.affected.applications + " applications";
            } else {
                mfrg = "an unknown number of records";
            }
        }
        return mfrg;
    }

    function bulk_action_success_callback(data) {
        var msg = "Your bulk edit request has been submitted and queued for execution.<br>";
        msg += build_affected_msg(data) + " have been queued for edit.<br>";
        msg += 'You can see your request <a href="' + bulk_job_url(data) + '" target="_blank">here</a> in the background jobs interface (opens new tab).<br>';
        msg += "You will get an email when your request has been processed; this could take anything from a few minutes to a few hours.<br>";
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
                } else if (action === "change_status") {
                    send["application_status"] = $("#application_status").val();
                }
                $.ajax({
                    type: 'POST',
                    url: bulk_action_url(options),
                    data: serialiseQueryObject(send),
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

        $("#application_status").change(function() {
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
                    data: serialiseQueryObject({
                        selection_query: query,
                        editor_group: $('#editor_group').val(),
                        note: $('#note').val(),
                        application_status: $("#application_status").val(),
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

        /*
        ////////////////////////////////////////////////////////////
        // functions for handling the bulk form

        function get_bulk_action() {
            action = $('#bulk_action').val();
            if (! action) {
                alert('Error: unknown bulk operation.');
                throw 'Error: unknown bulk operation. The bulk action field was empty.'
            }
            return action
        }

        function bulk_action_url() {
            return '/admin/applications/bulk/' + get_bulk_action()
        }

        function application_success_callback(data) {
            alert('Submitted - ' + data.affected_applications + ' applications have been queued for edit.');
            $('#bulk-submit').removeAttr('disabled').html('Submit');
        }

        function application_error_callback(jqXHR, textStatus, errorThrown) {
            alert('There was an error with your request.');
            console.error(textStatus + ': ' + errorThrown);
            $('#bulk-submit').removeAttr('disabled').html('Submit');
        }

        function application_confirm_callback(data) {
            var sure = confirm('This operation will affect ' + data.affected_applications + ' applications.');
            if (sure) {
                $.ajax({
                    type: 'POST',
                    url: bulk_action_url(),
                    data: JSON.stringify({
                        selection_query: query,
                        editor_group: $('#editor_group').val(),
                        application_status: $('#application_status').val(),
                        note: $('#note').val(),
                        dry_run: false
                    }),
                    contentType : 'application/json',
                    success : application_success_callback,
                    error: application_error_callback
                });
            } else {
                $('#bulk-submit').removeAttr('disabled').html('Submit');
            }
        }

        $('#bulk-submit').unbind('click').bind('click', function(event) {
            event.preventDefault();

            $('#bulk-submit').attr('disabled', 'disabled').html("<img src='/static/doaj/images/white-transparent-loader.gif'>&nbsp;Submitting...");

            $.ajax({
                type: 'POST',
                url: bulk_action_url(),
                data: JSON.stringify({
                    selection_query: query,
                    editor_group: $('#editor_group').val(),
                    application_status: $('#application_status').val(),
                    note: $('#note').val(),
                    dry_run: true
                }),
                contentType : 'application/json',
                success : application_confirm_callback,
                error: application_error_callback
            });
        });
        */
    }

    $('.facetview.suggestions').facetview({
        search_url: es_scheme + '//' + es_domain + '/admin_query/suggestion/_search?',

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
            {   'field': 'admin.application_status.exact',
                'display': 'Application Status',
                'value_function': adminStatusMap
            },
            {'field': 'index.application_type.exact', 'display': 'Record type'},
            {'field': 'index.has_editor_group.exact', 'display': 'Has Editor Group?'},
            {'field': 'index.has_editor.exact', 'display': 'Has Associate Editor?'},
            {'field': 'admin.editor_group.exact', 'display': 'Editor Group'},
            {'field': 'admin.editor.exact', 'display': 'Editor'},
            {'field': 'index.classification.exact', 'display': 'Subject'},
            {'field': 'index.language.exact', 'display': 'Journal Language'},
            {'field': 'index.country.exact', 'display': 'Country of publisher'},
            {'field': 'index.subject.exact', 'display': 'Subject'},
            {'field': 'index.publisher.exact', 'display': 'Publisher'},
            {'field': 'bibjson.provider.exact', 'display': 'Platform, Host, Aggregator'},
            {
                'field': 'bibjson.author_pays.exact',
                'display': 'Publication charges?',
                value_function: authorPaysMap
            },
            {'field': 'index.license.exact', 'display': 'Journal License'},
            {'field': 'bibjson.oa_start.exact', 'display': 'Started publishing OA content (year)'},
            {'field': 'bibjson.oa_end.exact', 'display': 'Stopped publishing OA content (year)'}
        ],

        search_sortby: [

        ],

        sort : [

        ],

        searchbox_fieldselect: [

        ],

        page_size : 10,
        from : 0,

        results_render_callbacks: {
            'bibjson.author_pays': fv_author_pays,
            'admin.application_status': fv_application_status,
            'created_date': fv_created_date,
            'bibjson.abstract': fv_abstract,
            'journal_license' : fv_journal_license,
            "title_field" : fv_title_field,
            "doi_link" : fv_doi_link,
            "links" : fv_links,
            "issns" : fv_issns,
            "edit_suggestion" : fv_edit_suggestion,
            "country_name": fv_country_name,
            'last_manual_update': fv_last_manual_update,
            'suggested_on': fv_suggested_on,
            'readonly_journal': fv_readonly_journal,
            'owner' : fv_owner,
            "related_journal" : fv_related_journal
        },
        result_display: [
            [
                {
                    "field" : "title_field"
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
                    "field": "suggested_on"
                }
            ],
            [
                {
                    "pre": "<strong>Last updated</strong>: ",
                    "field": "last_manual_update"   // Note: last updated on UI points to when last updated by a person (via form)
                }
            ],
            [
                {
                    "pre" : "<strong>Owner</strong>: ",
                    "field" : "owner"
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
                    "pre" : "<strong>Application status</strong>: ",
                    "field" : "admin.application_status"
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
                    "field": "suggestion.suggester.name"
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
                    "field": "bibjson.author_pays"
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
                    "field": "country_name"
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
                    "field": "journal_license"
                }
            ],
            [
                {
                    "field" : "links"
                }
            ],
            [
                {
                    "field" : "related_journal"
                }
            ],
            [
                {
                    "field" : "edit_suggestion"
                },
                {
                    "field" : "readonly_journal"
                }
            ]
        ]
    });
});
