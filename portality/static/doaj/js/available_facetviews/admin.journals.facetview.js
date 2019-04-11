jQuery(document).ready(function($) {

    $('.facetview.journals').facetview({
        search_url: es_scheme + '//' + es_domain + '/admin_query/journal/_search?',

        render_results_metadata: doajPager,
        render_active_terms_filter: doajRenderActiveTermsFilter,
        post_render_callback: doajScrollTop,

        sharesave_link: false,
        freetext_submit_delay: 1000,
        default_facet_hide_inactive: true,
        default_facet_operator: "AND",
        default_operator : "AND",

        facets: [
            {'field': 'admin.in_doaj', 'display': 'In DOAJ?'},
            {'field': 'index.has_seal.exact', 'display': "DOAJ Seal"},
            {'field': 'admin.owner.exact', 'display': 'Owner'},
            {'field': 'index.has_editor_group.exact', 'display': 'Has Editor Group?'},
            {'field': 'index.has_editor.exact', 'display': 'Has Associate Editor?'},
            {'field': 'admin.editor_group.exact', 'display': 'Editor Group'},
            {'field': 'admin.editor.exact', 'display': 'Editor'},
            {
                'field': 'bibjson.author_pays.exact',
                'display': 'Publication charges?',
                value_function: authorPaysMap
            },
            {'field': 'index.license.exact', 'display': 'Journal License'},
            {'field': 'index.publisher.exact', 'display': 'Publisher'},
            {'field': 'bibjson.provider.exact', 'display': 'Platform, Host, Aggregator'},
            {'field': 'index.classification.exact', 'display': 'Classification'},
            {'field': 'index.subject.exact', 'display': 'Subject'},
            {'field': 'index.language.exact', 'display': 'Journal Language'},
            {'field': 'index.country.exact', 'display': 'Country of publisher'},
            {'field': 'index.continued.exact', 'display': 'Continued'},
            {
                type: "date_histogram",
                field: "bibjson.discontinued_date",
                interval: "year",
                display: "Discontinued Year",
                value_function : function(val) {
                    return (new Date(parseInt(val))).getUTCFullYear();
                },
                size: false,
                sort: "desc"
            }
        ],

        search_sortby: [
            {'display':'Date added to DOAJ','field':'created_date'},
            {'display':'Last updated','field':'last_manual_update'}, // Note: last updated on UI points to when last updated by a person (via form)
            {'display':'Title','field':'index.unpunctitle.exact'}
        ],

        searchbox_fieldselect: [
            {'display':'Owner','field':'admin.owner'},
            {'display':'Title','field':'index.title'},
            {'display':'Journal: Alternative Title','field':'bibjson.alternative_title'},
            {'display':'Subject','field':'index.subject'},
            {'display':'Classification','field':'index.classification'},
            {'display':'ISSN', 'field':'index.issn.exact'},
            {'display':'Country of publisher','field':'index.country'},
            {'display':'Journal Language','field':'index.language'},
            {'display':'Publisher','field':'index.publisher'},
            {'display':'Journal: Platform, Host, Aggregator','field':'bibjson.provider'}
        ],

        page_size : 10,
        from : 0,

        results_render_callbacks: {
            'bibjson.author_pays': fv_author_pays,
            'created_date': fv_created_date,
            'last_manual_update': fv_last_manual_update,
            'bibjson.abstract': fv_abstract,
            'journal_license' : fv_journal_license,
            "title_field" : fv_title_field,
            "doi_link" : fv_doi_link,
            "links" : fv_links,
            "issns" : fv_issns,
            "edit_journal": fv_edit_journal,
            "make_continuation" : fv_make_continuation,
            "in_doaj": fv_in_doaj,
            "country_name": fv_country_name,
            "owner" : fv_owner,
            "related_applications" : fv_related_applications
        },
        result_display: [
            // Journals
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
                    "pre" : "<strong>In DOAJ?</strong>: ",
                    "field" : "in_doaj"
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
                    "pre" : "<strong>Editor Group</strong>: ",
                    "field" : "admin.editor_group"
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
                    "field": "last_manual_update"  // Note: last updated on UI points to when last updated by a person (via form)
                }
            ],
            [
                {
                    "field" : "links"
                }
            ],
            [
                {
                    "pre": "<strong>License</strong>: ",
                    "field": "journal_license"
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
                    "pre": "<strong>Country</strong>: ",
                    "field": "country_name"
                }
            ],
            [
                {
                    "pre": "<strong>Language</strong>: ",
                    "field": "bibjson.language"
                }
            ],
            [
                {
                    "field" : "related_applications"
                }
            ],
            [
                {
                    "field" : "make_continuation"
                }
            ],
            [
                {
                    "field": "edit_journal"
                }
            ]
        ]
    });
});
