jQuery(document).ready(function($) {
  $('.facetview.publisher').each(function() {
  $(this).facetview({
    search_url: 'http://' + es_domain + '/publisher_query/journal/_search?',
    search_index: 'elasticsearch',
    sharesave_link: false,
    searchbox_shade: 'none',
    pager_on_top: true,
    pager_slider: true,
    display_images: false,
    pre_search_callback: customise_facetview_presearch,
    post_search_callback: customise_facetview_results,
    post_init_callback: customise_facetview_init,
    freetext_submit_delay:"1000",
    results_render_callbacks: {
        'bibjson.author_pays': fv_author_pays,
        'created_date': fv_created_date,
        'bibjson.abstract': fv_abstract,
        'addthis-social-share-button': fv_addthis,
        'journal_license' : fv_journal_license,
        "title_field" : fv_title_field,
        "doi_link" : fv_doi_link,
        "links" : fv_links,
        "issns" : fv_issns,
        "in_doaj": fv_in_doaj,
    },
    hide_inactive_facets: true,
    facets: [
        {'field': 'admin.in_doaj', 'display': 'In DOAJ?'},
        {'field': 'index.license.exact', 'display': 'Journal License'},
        {'field': 'index.classification.exact', 'display': 'Classification'},
        {'field': 'index.subject.exact', 'display': 'Subject'},
    ],
    search_sortby: [
        {'display':'Date added to DOAJ','field':'created_date'},
        {'display':'Title','field':'index.title.exact'},
    ],
    searchbox_fieldselect: [
        {'display':'Title','field':'index.title'},
        {'display':'Journal: Alternative Title','field':'bibjson.alternative_title'},
        {'display':'Subject','field':'index.subject'},
        {'display':'Classification','field':'index.classification'},
        {'display':'ISSN', 'field':'index.issn.exact'}
    ],
    paging: {
      from: 0,
      size: 10
    },
    default_operator: "AND",
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
                "field": "created_date",
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
                "field": "bibjson.publisher",
            }
        ],
        [
            {
                "pre": "<strong>Provider</strong>: ",
                "field": "bibjson.provider",
            }
        ],
        [
            {
                "pre": "<strong>Publication charges?</strong>: ",
                "field": "bibjson.author_pays",
            }
        ],
        [
            {
                "pre": "<strong>Classification</strong>: ",
                "field": "index.classification",
            }
        ],
        [
            {
                "pre": "<strong>Subject</strong>: ",
                "field": "index.subject",
            }
        ],
        [
            {
                "pre": "<strong>Started publishing Open Access content in</strong>: ",
                "field": "bibjson.oa_start.year",
            }
        ],
        [
            {
                "pre": "<strong>Stopped publishing Open Access content in</strong>: ",
                "field": "bibjson.oa_end.year",
            }
        ],
        [
            {
                "pre": "<strong>Country</strong>: ",
                "field": "bibjson.country",
            }
        ],
        [
            {
                "pre": "<strong>Language</strong>: ",
                "field": "bibjson.language",
            }
        ]
    ],
  });
  });
});
