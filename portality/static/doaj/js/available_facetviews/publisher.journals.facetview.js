jQuery(document).ready(function($) {

    $('.facetview.publisher').facetview({
        search_url: es_scheme + '//' + es_domain + '/publisher_query/journal/_search?',

        render_results_metadata: doajPager,
        render_active_terms_filter: doajRenderActiveTermsFilter,
        render_not_found: publisherJournalNotFound,
        post_render_callback: doajScrollTop,

        sharesave_link: false,
        freetext_submit_delay: 1000,
        default_facet_hide_inactive: true,
        default_facet_operator: "AND",
        default_operator : "AND",

        facets: [
            {
                'field': 'admin.in_doaj',
                'display': 'In DOAJ?',
                value_function: function(val) {
                    return val == "T" ? "Yes" : "No"
                }
            },
            {'field': 'index.license.exact', 'display': 'Journal License'},
            {'field': 'index.classification.exact', 'display': 'Classification'},
            {'field': 'index.subject.exact', 'display': 'Subject'}
        ],

        search_sortby: [
            {'display':'Date added to DOAJ','field':'created_date'},
            {'display':'Title','field':'index.unpunctitle.exact'}
        ],

        searchbox_fieldselect: [
            {'display':'Title','field':'index.title'},
            {'display':'Journal: Alternative Title','field':'bibjson.alternative_title'},
            {'display':'Subject','field':'index.subject'},
            {'display':'Classification','field':'index.classification'},
            {'display':'ISSN', 'field':'index.issn.exact'}
        ],

        page_size : 10,
        from : 0,

        results_render_callbacks: {
            'bibjson.author_pays': fv_author_pays,
            'created_date': fv_created_date,
            'bibjson.abstract': fv_abstract,
            'journal_license' : fv_journal_license,
            "title_field" : fv_title_field,
            "doi_link" : fv_doi_link,
            "links" : fv_links,
            "issns" : fv_issns,
            "in_doaj": fv_in_doaj,
            "country_name": fv_country_name,
            "make_update_request" : fv_make_update_request
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
                    "pre" : "<strong>ISSN(s)</strong>: ",
                    "field" : "issns"
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
                    "field" : "make_update_request"
                }
            ]
        ]
    });
});

