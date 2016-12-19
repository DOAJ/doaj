jQuery(document).ready(function($) {

    $('.facetview.background_jobs').facetview({
        search_url: es_scheme + '//' + es_domain + '/admin_query/editor,group/_search?',

        render_results_metadata: doajPager,
        render_active_terms_filter: doajRenderActiveTermsFilter,
        post_render_callback: doajEGPostRender,

        sharesave_link: false,
        freetext_submit_delay: 1000,
        default_facet_hide_inactive: true,
        default_facet_operator: "AND",
        default_operator : "AND",

        facets: [
            {'field': 'name', 'display': 'Name Keywords'}
        ],

        search_sortby: [
            {'display':'Created Date','field':'created_date'},
            {'display':'Last Modified Date','field':'last_updated'},
            {'display':'Editor ID','field':'editor'},
            {'display':'Group Name','field':'name'}
        ],

        searchbox_fieldselect: [
            {'display':'Group Name','field':'name'},
            {'display':'Editor ID','field':'editor'},
            {'display':'Associate Editor ID','field':'associate'}
        ],

        page_size : 25,
        from : 0,

        results_render_callbacks: {
            "linked_associates" : fv_linked_associates,
            "edit_editor_group" : fv_edit_editor_group,
            "delete_editor_group" : fv_delete_editor_group
        },
        result_display: [
            [
                {
                    "pre" : "<strong>",
                    "field" : "name",
                    "post" : "</strong>"
                }
            ],
            [
                {
                    "pre": 'Editor: <a href="/account/',
                    "field": "editor",
                    "post" : '">'
                },
                {
                    "field": "editor",
                    "post" : "</a>"
                }
            ],
            [
                {
                    "field" : "linked_associates"
                }
            ],
            [
                {
                    "field": "edit_editor_group"
                },
                {
                    "field" : "delete_editor_group"
                }
            ]
        ]
    });
});
