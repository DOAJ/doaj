jQuery(document).ready(function($) {

    function postSearch() {
        // first to the default post search callback
        customise_facetview_results()

        // now add the handlers for the article delete
        $(".delete_editor_group_link").unbind("click")
        $(".delete_editor_group_link").click(function(event) {
            event.preventDefault();

            function success_callback(data) {
                alert("The group was successfully deleted")
                $(".facetview_freetext").trigger("keyup") // cause a search
            }

            function error_callback() {
                alert("There was an error deleting the group")
            }

            var c = confirm("Are you really really sure?  You can't undo this operation!")
            if (c) {
                var href = $(this).attr("href")
                var obj = {"delete" : "true"}
                $.ajax({
                    type: "POST",
                    url: href,
                    data: obj,
                    success : success_callback,
                    error: error_callback
                })
            }
        });
    }

  $('.facetview.editor_group').each(function() {
  $(this).facetview({
    search_url: es_scheme + '//' + es_domain + '/admin_query/editor,group/_search?',
    search_index: 'elasticsearch',
    sharesave_link: false,
    searchbox_shade: 'none',
    pager_on_top: true,
    pager_slider: true,
    display_images: false,
    pre_search_callback: customise_facetview_presearch,
    post_search_callback: postSearch,
    post_init_callback: customise_facetview_init,
    freetext_submit_delay:"1000",
    results_render_callbacks: {
        "linked_associates" : fv_linked_associates,
        "edit_editor_group" : fv_edit_editor_group,
        "delete_editor_group" : fv_delete_editor_group
    },
    hide_inactive_facets: true,
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
    paging: {
      from: 0,
      size: 25
    },
    default_operator: "AND",
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
                "field": "edit_editor_group",
            },
            {
                "field" : "delete_editor_group"
            }
        ]
    ]
  });
  });
});
