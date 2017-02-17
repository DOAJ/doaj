jQuery(document).ready(function($) {

    function adminButtons(options, context) {
        // Disable the bulk action submit button if there is an empty query in the facetview
        if ($.isEmptyObject(options.active_filters) && options.q == '') {
            $('#bulk-submit').attr('disabled', 'disabled');
        } else {
            $('#bulk-submit').removeAttr('disabled');
        }
    }

    function adminJAPostRender(options, context) {
        doajJAPostRender(options, context);

        var query = elasticSearchQuery({
            options: options,
            include_facets: false,
            include_fields: false
        });

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

        function bulk_action_type() {
            // TODO if the action is "delete", we want to take the value of the _type facet
            // and return "articles" or "journals" as appropriate.
            // We also need to make disable the bulk job submit button unless an option
            // is selected in the _type facet.
            // if (get_bulk_action() == 'delete') {
            //     return 'journals,articles';
            // }
            return 'journals'
        }

        function bulk_action_url() {
            return '/admin/' + bulk_action_type() + '/bulk/' + get_bulk_action()
        }

        function build_affected_msg(data) {
            var mfrg = undefined;
            if (data.affected_journals && data.affected_articles) {
                mfrg = data.affected_journals + " journals and " + data.affected_articles + " articles"
            }
            else if (data.affected_journals) {
                mfrg = data.affected_journals + " journals"
            }
            else if (data.affected_articles) {
                mfrg = data.affected_articles + " articles"
            }
            else {
                mfrg = "an unknown number of records"
            }
            return mfrg
        }

        function bulk_action_success_callback(data) {
            alert('Submitted - ' + build_affected_msg(data) + ' have been queued for edit.');
            $('#bulk-submit').removeAttr('disabled').html('Submit');
        }

        function bulk_action_error_callback(jqXHR, textStatus, errorThrown) {
            alert('There was an error with your request.');
            console.error(textStatus + ': ' + errorThrown);
            $('#bulk-submit').removeAttr('disabled').html('Submit');
        }

        function bulk_action_confirm_callback(data) {
            var sure = confirm('This operation will affect ' + build_affected_msg(data) + '.');
            if (sure) {
                $.ajax({
                    type: 'POST',
                    url: bulk_action_url(),
                    data: JSON.stringify({
                        selection_query: query,
                        editor_group: $('#editor_group').val(),
                        note: $('#note').val(),
                        dry_run: false
                    }),
                    contentType : 'application/json',
                    success : bulk_action_success_callback,
                    error: bulk_action_error_callback
                });
            } else {
                $('#bulk-submit').removeAttr('disabled').html('Submit');
            }
        }

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
                $.ajax({
                    type: 'POST',
                    url: bulk_action_url(),
                    data: JSON.stringify({
                        selection_query: query,
                        editor_group: $('#editor_group').val(),
                        note: $('#note').val(),
                        dry_run: true
                    }),
                    contentType : 'application/json',
                    success : bulk_action_confirm_callback,
                    error: bulk_action_error_callback
                });
            } else {
                $('#bulk-submit').removeAttr('disabled').html('Submit');
            }
        });
    }

    $('.facetview.admin_journals_and_articles').facetview({
        search_url: es_scheme + '//' + es_domain + '/admin_query/journal,article/_search?',

        render_results_metadata: doajPager,
        render_active_terms_filter: doajRenderActiveTermsFilter,
        post_render_callback: adminJAPostRender,
        post_search_callback: adminButtons,

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
