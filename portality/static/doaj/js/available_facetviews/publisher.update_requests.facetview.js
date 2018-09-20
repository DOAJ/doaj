jQuery(document).ready(function ($) {

    function doajUpdateRequestPostRender(options, context) {
        // first run the basic post render
        doajScrollTop(options, context);

        // now add the handlers for the application delete
        $(".delete_suggestion_link").unbind("click").click(function(event) {
            event.preventDefault();

            function success_callback(data) {
                alert("The update request was successfully deleted");
                $(".facetview_freetext").trigger("keyup"); // cause a search
            }

            function error_callback() {
                alert("There was an error deleting the update request")
            }

            var c = confirm("Are you really really sure?  You can't undo this operation!");
            if (c) {
                var href = $(this).attr("href");
                $.ajax({
                    type: "DELETE",
                    url: href,
                    success : success_callback,
                    error: error_callback
                })
            }
        });
    }

    $('.facetview.update_requests').facetview({
        search_url: es_scheme + '//' + es_domain + '/publisher_query/suggestion/_search?',

        render_results_metadata: doajPager,
        render_active_terms_filter: doajRenderActiveTermsFilter,
        render_not_found: publisherUpdateRequestNotFound,
        post_render_callback: doajUpdateRequestPostRender,

        sharesave_link: false,
        freetext_submit_delay: 1000,
        default_facet_hide_inactive: true,
        default_facet_operator: "AND",
        default_operator : "AND",

        facets: [
            {
                'field': 'admin.application_status.exact',
                'display': 'Status',
                value_function: publisherStatusMap,
                open: true
            }
        ],

        search_sortby: [
            {'display': 'Date created', 'field': 'created_date'},
            {'display': 'Last updated', 'field': 'last_manual_update'},
            {'display': 'Title', 'field': 'index.unpunctitle.exact'}
        ],

        searchbox_fieldselect: [
            {'display': 'Title', 'field': 'index.title'},
            {'display': 'Journal: Alternative Title', 'field': 'bibjson.alternative_title'},
            {'display': 'Subject', 'field': 'index.subject'},
            {'display': 'Classification', 'field': 'index.classification'},
            {'display': 'ISSN', 'field': 'index.issn.exact'},
            {'display': 'Country of publisher', 'field': 'index.country'},
            {'display': 'Journal Language', 'field': 'index.language'},
            {'display': 'Publisher', 'field': 'index.publisher'},
            {'display': 'Journal: Provider', 'field': 'bibjson.provider'}
        ],

        page_size : 10,
        from : 0,
        sort : [{"last_manual_update" : {"order" : "desc"}}],

        results_render_callbacks: {
            'bibjson.author_pays': fv_author_pays,
            'created_date': fv_created_date,
            'last_updated': fv_last_updated,
            'journal_license': fv_journal_license,
            "title_field": fv_title_field,
            "doi_link": fv_doi_link,
            "links": fv_links,
            "issns": fv_issns,
            "country_name": fv_country_name,
            'suggested_on': fv_suggested_on,
            "edit_update_request": fv_edit_update_request
        },
        result_display: [
            [
                {
                    "field": "title_field"
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
                    "field": "last_manual_update"
                }
            ],
            [
                {
                    "pre": "<strong>ISSN(s)</strong>: ",
                    "field": "issns"
                }
            ],
            [
                {
                    "pre": "<strong>Application status</strong>: ",
                    "field": "admin.application_status"
                }
            ],
            [
                {
                    "pre": "<strong>Description</strong>: ",
                    "field": "suggestion.description"
                }
            ],
            [
                {
                    "pre": "<strong>Contact</strong>: ",
                    "field": "admin.contact.name"
                },
                {
                    "field": "admin.contact.email"
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
                    "pre": "<strong>Provider</strong>: ",
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
                    "field": "links"
                }
            ],
            [
                {
                    "field": "edit_update_request"
                }
            ]
        ]
    });
});

