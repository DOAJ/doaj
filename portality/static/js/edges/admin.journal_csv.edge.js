// ~~ AdminAlerts:Edge ~~
// ~~-> Edges:Technology ~~
$.extend(true, doaj, {

    adminJournalCSVSearch : {
        activeEdges : {},

        deleteCSV: function(params) {
            let id = params.id;
            let success = params.success || function() {};
            let error = params.error || function() {};

            $.ajax({
                type: "POST",
                url: "/admin/journal-csv/delete",
                data: {"id": id},
                success : success,
                error: error
            })
        },

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#journal_csvs";
            var search_url = current_scheme + "//" + current_domain + doaj.adminJournalCSVSearchConfig.searchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            let fileSizeFormat = edges.numFormat({
                thousandsSeparator: ",",
                decimalPlaces: 2
            });

            let deleteClass = edges.css_classes("journal-csvs", "delete");
            let deleteClassSelector = edges.css_class_selector("journal-csvs", "delete");

            var components = [
                doaj.components.searchingNotification(),

                // configure the search controller
                edges.newFullSearchController({
                    id: "search-controller",
                    category: "controller",
                    sortOptions: [
                        {'display':'Export Date','field':'export_date'}
                    ],
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: -1,
                        searchButton: true,
                        searchPlaceholder: "Search All Journal CSV Records"
                    })
                }),

                // the pager, with the explicitly set page size options (see the openingQuery for the initial size)
                edges.newPager({
                    id: "top-pager",
                    category: "top-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [50, 100],
                        numberFormat: countFormat,
                        scroll: false
                    })
                }),
                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [50, 100],
                        numberFormat: countFormat,
                        scroll: false
                    })
                }),

                // results display
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer: edges.bs3.newTabularResultsRenderer({
                        // the fields to display in the results table
                        fieldDisplay: [
                            {
                                field: "id",
                                display: "Free/Premium",
                                valueFunction: function(value, result) {
                                    if (value && value !== "-") {
                                        if (value === doaj.adminJournalCSVSearchConfig.free) {
                                            return "CURRENT FREE"
                                        }
                                        else if (value === doaj.adminJournalCSVSearchConfig.premium) {
                                            return "CURRENT PREMIUM"
                                        }
                                    }
                                    return "";
                                }
                            },
                            {
                                field: "export_date",
                                display: "Export Date"
                            },
                            {
                                field: "filename",
                                display: "Filename/URL",
                                valueFunction: function(value, result) {
                                    if (value && value !== "-") {
                                        if (result.url) {
                                            return `<a href="${result.url}">${value}</a>`;
                                        }
                                        return `${value} [WARNING: NO URL]`;
                                    }
                                    return value;
                                }
                            },
                            {
                                field: "size",
                                display: "File Size",
                                valueFunction: function(value, result) {
                                    if (value && value !== "-") {
                                        return doaj.humanFileSize(value, fileSizeFormat);
                                        // return `${countFormat(value)} b`;
                                    }
                                    return value;
                                }
                            },
                            {
                                field: "created_date",  // arbitrary field, not used
                                display: "Actions",
                                valueFunction: function(value, result) {
                                    return `<a href="#" class="${deleteClass}" data-id="${result.id}">Delete</a>`;
                                }
                            }
                        ]
                    })
                })
            ];

            var e = edges.newEdge({
                selector: selector,
                template: edges.bs3.newFacetview(),
                search_url: search_url,
                manageUrl: true,
                components: components,
                openingQuery: es.newQuery({
                    sort: [{field: "export_date", order: "desc"}],
                    size: 50
                }),
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error. Please reload the page and try again. If the issue persists please contact an administrator.");
                    },
                    "edges:post-render": function() {
                        $(deleteClassSelector).bind("click", function(e) {
                            e.preventDefault();
                            let c = confirm("Are you sure you want to delete this CSV record? This action cannot be undone.");
                            if (!c) {
                                return;
                            }

                            let el = $(e.currentTarget);
                            let id = el.attr("data-id");
                            doaj.adminJournalCSVSearch.deleteCSV({
                                id: id,
                                success: function() {
                                    alert("CSV record deleted successfully.");
                                    doaj.adminJournalCSVSearch.activeEdges[selector].cycle();
                                },
                                error: function() {
                                    alert("There was an error deleting the CSV record. Please try again later.");
                                }
                            });
                        });
                    }
                }
            });
            doaj.adminJournalCSVSearch.activeEdges[selector] = e;
        }
    }
});


jQuery(document).ready(function($) {
    doaj.adminJournalCSVSearch.init();
});
