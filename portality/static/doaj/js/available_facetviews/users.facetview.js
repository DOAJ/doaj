jQuery(document).ready(function($) {

    $('.facetview.users').facetview({
        search_url: es_scheme + '//' + es_domain + '/admin_query/account/_search?',

        render_results_metadata: doajPager,
        render_active_terms_filter: doajRenderActiveTermsFilter,
        post_render_callback: doajScrollTop,

        sharesave_link: false,
        freetext_submit_delay: 1000,
        default_facet_hide_inactive: true,
        default_facet_operator: "AND",
        default_operator : "AND",

        facets: [
            {'field': 'role', 'display': 'Role'}
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

        page_size : 25,
        from : 0,

        results_render_callbacks: {
            "edit_user" : fv_edit_user,
            "user_journals" : fv_user_journals
        },
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
                    "field": "last_updated"
                }
            ],
            [
                {
                    "field": "edit_user"
                },
                {
                    "field" : "user_journals"
                }
            ]
        ]
    });
});
