// ~~ AdminAlerts:Edge ~~
// ~~-> Edges:Technology ~~
doaj.adminAutoassignSearch = {
    activeEdges : {},

    init : function(params) {
        if (!params) { params = {} }

        var selector = params.selector || "#autoassign";

        var e = doaj.components.makeSearch({
            selector: selector,
            searchUrl: doaj.edgeUtil.url.build(doaj.adminAutoassignSearchConfig.searchPath),
            facets: [
                doaj.components.refiningAndFacet({id: "target", field: "target.exact", display: "Editor Group", orderBy: "term", orderDir: "asc", size: 50}),
                doaj.components.refiningAndFacet({id: "account", field: "account_id.exact", display: "Publisher", orderBy: "term", orderDir: "asc"}),
                doaj.components.refiningAndFacet({id: "country_name", field: "country_name.exact", display: "Country Name", orderBy: "term", orderDir: "asc"})
            ],
            sortOptions: [
                {'display': 'Import Date', 'field': 'created_date'},
                {'display': 'Publisher', 'field': 'account_id.exact'},
                {'display': 'Country Name', 'field': 'country_name.exact'},
                {'display': 'Editor Group', 'field': 'target.exact'}
            ],
            fieldOptions: [
                {'display': 'Editor Group', 'field': 'target'},
                {'display': 'Publisher', 'field': 'account_id'},
                {'display': 'Country Name', 'field': 'country_name'}
            ],
            searchPlaceholder: "Search All Routers",
            resultsDisplay: edges.newResultsDisplay({
                id: "results",
                category: "results",
                renderer: edges.bs3.newTabularResultsRenderer({
                    fieldDisplay: [
                        {
                            field: "account_id",
                            display: "Publisher",
                            valueFunction: function(value, result) {
                                if (value && value !== "-") {
                                    return `<a href="/account/${value}">${value}</a>`;
                                }
                                return value;
                            }
                        },
                        {field: "country_name", display: "Country Name"},
                        {field: "country_code", display: "Country Code"},
                        {
                            field: "target",
                            display: "Editor Group",
                            valueFunction: function(value, result) {
                                if (value && value !== "-") {
                                    let source = doaj.searchQuerySource({
                                        queryString: value,
                                        defaultField: "name",
                                    });
                                    return `<a href="/admin/editor_groups?source=${source}">${value}</a>`;
                                }
                                return value;
                            }
                        },
                        {field: "created_date", display: "Import Date"}
                    ]
                })
            }),
            fieldDisplays: {
                "target.exact": "Editor Group",
                "country_name.exact": "Country Name",
                "account_id.exact": "Publisher"
            }
        });

        doaj.adminAutoassignSearch.activeEdges[selector] = e;
    }
}


jQuery(document).ready(function($) {
    doaj.adminAutoassignSearch.init();
});
