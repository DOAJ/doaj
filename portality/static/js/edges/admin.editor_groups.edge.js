// ~~ EditorGroupsSearch:Feature ~~
$.extend(true, doaj, {

    adminEditorGroupSearch: {
        activeEdges: {},

        linkedAssociates : function (val, resultobj, renderer) {
            if (resultobj.associates) {
                var frag = "Associate Editors: ";
                for (var i = 0; i < resultobj.associates.length; i++) {
                    if (i > 0) {
                        frag += ", "
                    }
                    var ass = resultobj.associates[i];
                    frag += '<a href="/account/' + ass + '">' + edges.escapeHtml(ass) + '</a>'
                }
                return frag
            }
            return false
        },

        editEditorGroup : function (val, resultobj, renderer) {
            var result = '<a class="edit_editor_group_link button" href="';
            result += doaj.adminEditorGroupSearchConfig.editorGroupEditUrl;
            result += resultobj['id'];
            result += '">Edit this group</a>';
            return result;
        },

        deleteEditorGroup : function (val, resultobj, renderer) {
            var result = '<br/><a class="delete_editor_group_link button" href="';
            result += doaj.adminEditorGroupSearchConfig.editorGroupEditUrl;
            result += resultobj['id'];
            result += '" target="_blank"';
            result += '>Delete this group</a>';
            return result;
        },

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#editor_groups";
            var search_url = current_scheme + "//" + current_domain + doaj.adminEditorGroupSearchConfig.searchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                doaj.components.searchingNotification(),

                // facets
                edges.newRefiningANDTermSelector({
                    id: "maned",
                    category: "facet",
                    field: "maned.exact",
                    display: "Managing Editor",
                    deactivateThreshold: 1,
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: true,
                        togglable: false,
                        countFormat: countFormat,
                        hideInactive: true
                    })
                }),

                // configure the search controller
                edges.newFullSearchController({
                    id: "search-controller",
                    category: "controller",
                    sortOptions: [
                        {'display':'Created Date','field':'created_date'},
                        {'display':'Last Modified Date','field':'last_updated'},
                        {'display':'Managing Editor ID','field':'maned.exact'},
                        {'display':'Editor ID','field':'editor.exact'},
                        {'display':'Group Name','field':'name.exact'}
                    ],
                    fieldOptions: [
                        {'display':'Group Name','field':'name'},
                        {'display':'Managing Editor ID','field':'maned'},
                        {'display':'Editor ID','field':'editor'},
                        {'display':'Associate Editor ID','field':'associate'}
                    ],
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: -1,
                        searchButton: true,
                        searchPlaceholder: "Search Editor Groups"
                    })
                }),

                // the pager, with the explicitly set page size options (see the openingQuery for the initial size)
                edges.newPager({
                    id: "top-pager",
                    category: "top-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [25, 50, 100],
                        numberFormat: countFormat,
                        scroll: false
                    })
                }),
                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [25, 50, 100],
                        numberFormat: countFormat,
                        scroll: false
                    })
                }),

                // results display
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer: edges.bs3.newResultsFieldsByRowRenderer({
                        rowDisplay : [
                            [
                                {
                                    "pre" : "<h3>",
                                    "field" : "name",
                                    "post" : "</h3>"
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
                                    "valueFunction" : doaj.adminEditorGroupSearch.linkedAssociates
                                }
                            ],
                            [
                                {
                                    "pre": 'Managing Editor: <a href="/account/',
                                    "field": "maned",
                                    "post" : '">'
                                },
                                {
                                    "field": "maned",
                                    "post" : "</a>"
                                }
                            ],
                            [
                                {
                                    "valueFunction" : doaj.adminEditorGroupSearch.deleteEditorGroup
                                },
                                {
                                    "valueFunction": doaj.adminEditorGroupSearch.editEditorGroup
                                }
                            ]
                        ]
                    })
                }),

                // selected filters display, with all the fields given their display names
                edges.newSelectedFilters({
                    id: "selected-filters",
                    category: "selected-filters",
                    fieldDisplays: {
                        "name.exact": "Name",
                        "maned.exact": "Managing Editor"
                    }
                })
            ];

            var e = edges.newEdge({
                selector: selector,
                template: edges.bs3.newFacetview(),
                search_url: search_url,
                openingQuery : es.newQuery({size: 25}),
                manageUrl: true,
                components: components,
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact an administrator.");
                    }
                }
            });
            doaj.adminEditorGroupSearch.activeEdges[selector] = e;

            // bind the delete button
            $(selector).on("edges:post-render", function() {
                // now add the handlers for the article delete
                $(".delete_editor_group_link").unbind("click").click(function(event) {
                    event.preventDefault();

                    function success_callback(data) {
                        alert("The group was successfully deleted");
                        doaj.adminEditorGroupSearch.activeEdges[selector].cycle();
                    }

                    function error_callback() {
                        alert("There was an error deleting the group");
                    }

                    var c = confirm("Are you really really sure?  You can't undo this operation!");
                    if (c) {
                        var href = $(this).attr("href");
                        var obj = {"delete" : "true"};
                        $.ajax({
                            type: "POST",
                            url: href,
                            data: obj,
                            success : success_callback,
                            error: error_callback
                        })
                    }
                });
            });
        }
    }
});

jQuery(document).ready(function($) {
    doaj.adminEditorGroupSearch.init();
});
