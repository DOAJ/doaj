jQuery(document).ready(function($) {

    $('.facetview.suggestions').facetview({
        search_url: es_scheme + '//' + es_domain + '/admin_query/suggestion/_search?',

        render_results_metadata: doajPager,
        render_active_terms_filter: doajRenderActiveTermsFilter,
        post_render_callback: doajScrollTop,

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
            {'field': 'index.application_type.exact', 'display': 'Application type'},
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
            {'display':'Date applied','field':'suggestion.suggested_on'},
            {'display':'Last updated','field':'last_manual_update'},   // Note: last updated on UI points to when last updated by a person (via form)
            {'display':'Title','field':'index.unpunctitle.exact'}
        ],

        searchbox_fieldselect: [
            {'display':'Title','field':'index.title'},
            {'display':'Keywords','field':'bibjson.keywords'},
            {'display':'Subject','field':'index.classification'},
            {'display':'ISSN', 'field':'index.issn.exact'},
            {'display':'Country of publisher','field':'index.country'},
            {'display':'Journal Language','field':'index.language'},
            {'display':'Publisher','field':'index.publisher'},

            {'display':'Journal: Alternative Title','field':'bibjson.alternative_title'},
            {'display':'Journal: Platform, Host, Aggregator','field':'bibjson.provider'}
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
            'owner' : fv_owner
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
                    "pre" : "<strong>Application by</strong>: ",
                    "field" : "suggestion.suggester.name"
                },
                {
                    "field" : "suggestion.suggester.email"
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
                    "field" : "edit_suggestion"
                },
                {
                    "field" : "readonly_journal"
                }
            ]
        ]
    });
});
