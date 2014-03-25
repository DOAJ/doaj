jQuery(document).ready(function($) {
  $('.facetview.users').each(function() {
  $(this).facetview({
    search_url: es_scheme + '//' + es_domain + '/admin_query/account/_search?',
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
        "user_actions" : fv_user_actions
    },
    hide_inactive_facets: true,
    facets: [
        {'field': 'role', 'display': 'Role'},
    ],
    search_sortby: [
        {'display':'Created Date','field':'created_date'},
        {'display':'Last Modified Date','field':'last_updated'},
        {'display':'User ID','field':'id'},
        {'display':'Email Address','field':'email'}
    ],
    searchbox_fieldselect: [
        {'display':'User ID','field':'id'},
        {'display':'Email Address','field':'email'}
    ],
    paging: {
      from: 0,
      size: 25
    },
    default_operator: "AND",
    result_display: [
        [
            {
                "pre" : "<strong>",
                "field" : "id",
                "post" : "</strong>"
            }
        ],
        [
            {
                "pre": '<a href="mailto:',
                "field": "email",
                "post": '">'
            },
            {
                "field": "email",
                "post": '</a>'
            }
        ],
        [
            {
                "pre" : "<strong>Role(s)</strong>: <em>",
                "field" : "role",
                "post" : "</em>"
            }
        ],
        [
            {
                "pre" : "<strong>Account Created</strong>: ",
                "field" : "created_date"
            }
        ],
        [
            {
                "pre": "<strong>Account Last Modified</strong>: ",
                "field": "last_updated",
            }
        ],
        [
            {
                "pre": "<strong>Journals Managed</strong>: ",
                "field": "journal"
            }
        ],
        [
            {
                "field": "user_actions"
            }
        ]
    ],
  });
  });
});
