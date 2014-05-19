jQuery(document).ready(function($) {
  $('.facetview.journals').each(function() {
  $(this).facetview({
    search_url: es_scheme + '//' + es_domain + '/admin_query/journal/_search?',
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
        'last_updated': fv_last_updated,
        'bibjson.abstract': fv_abstract,
        'addthis-social-share-button': fv_addthis,
        'journal_license' : fv_journal_license,
        "title_field" : fv_title_field,
        "doi_link" : fv_doi_link,
        "links" : fv_links,
        "issns" : fv_issns,
        "edit_journal": fv_edit_journal,
        "in_doaj": fv_in_doaj,
        "country_name": fv_country_name,
        "owner" : fv_owner
    },
    hide_inactive_facets: true,
    facets: [
        {'field': 'admin.in_doaj', 'display': 'In DOAJ?'},
        {'field': 'admin.owner', 'display': 'Owner'},
        {'field': 'bibjson.author_pays.exact', 'display': 'Publication charges?'},
        {'field': 'index.license.exact', 'display': 'Journal License'},
        {'field': 'index.publisher.exact', 'display': 'Publisher'},
        {'field': 'bibjson.provider.exact', 'display': 'Provider'},
        {'field': 'index.classification.exact', 'display': 'Classification'},
        {'field': 'index.subject.exact', 'display': 'Subject'},
        {'field': 'index.language.exact', 'display': 'Journal Language'},
        {'field': 'index.country.exact', 'display': 'Journal Country'},
        {'field': 'index.title.exact', 'display': 'Journal Title'},
    ],
    search_sortby: [
        {'display':'Date added to DOAJ','field':'created_date'},
        {'display':'Last updated','field':'last_updated'},
        {'display':'Title','field':'index.title.exact'},
    ],
    searchbox_fieldselect: [
        {'display':'Owner','field':'admin.owner'},
        {'display':'Title','field':'index.title'},
        {'display':'Journal: Alternative Title','field':'bibjson.alternative_title'},
        {'display':'Subject','field':'index.subject'},
        {'display':'Classification','field':'index.classification'},
        {'display':'ISSN', 'field':'index.issn.exact'},
        {'display':'Journal Country','field':'index.country'},
        {'display':'Journal Language','field':'index.language'},
        {'display':'Publisher','field':'index.publisher'},
        {'display':'Journal: Provider','field':'bibjson.provider'},
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
                "pre": "<strong>Date added to DOAJ</strong>: ",
                "field": "created_date",
            }
        ],
        [
            {
                "pre": "<strong>Last updated</strong>: ",
                "field": "last_updated",
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
                "field": "country_name",
            }
        ],
        [
            {
                "pre": "<strong>Language</strong>: ",
                "field": "bibjson.language",
            }
        ],
        [
            {
                "field": "edit_journal",
            }
        ]
    ],
  });
  });
});
