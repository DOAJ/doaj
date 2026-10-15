// ~~ AdminUserSearch:Feature ~~
doaj.userSearch = {
    activeEdges: {},

    editUserLink : function (val, resultobj, renderer) {
        var result = '<a class="edit_user_link button" href="';
        result += doaj.userSearchConfig.userEditUrl;
        result += resultobj['id'];
        result += '">Edit this user</a>';
        return result;
    },

    userJournalsLink : function (val, resultobj, renderer) {
        var q = {
            "query": {
                "bool": {
                    "must": [{
                        "term": {"admin.owner.exact": resultobj.id}
                    }]
                }
            }
        };
        return '<br/><a class="button" href="/admin/journals?source=' + encodeURIComponent(JSON.stringify(q)) + '">View Journals</a>'
    },

    init : function(params) {
        if (!params) { params = {} }

        var selector = params.selector || "#users";

        var e = doaj.components.makeSearch({
            selector: selector,
            searchUrl: doaj.buildUrl(doaj.userSearchConfig.userSearchPath),
            facets: [
                doaj.components.refiningAndFacet({id: "role", field: "role.exact", display: "Role", deactivateThreshold: 1, open: true}),
                doaj.components.yearDateHistogramFacet({id: "created_date", field: "created_date", display: "Created Date", open: true, togglable: true})
            ],
            sortOptions: [
                {'display': 'Created Date', 'field': 'created_date'},
                {'display': 'Last Modified Date', 'field': 'last_updated'},
                {'display': 'User ID', 'field': 'id.exact'},
                {'display': 'Email address', 'field': 'email.exact'}
            ],
            fieldOptions: [
                {'display': 'User ID', 'field': 'id'},
                {'display': 'Email address', 'field': 'email'}
            ],
            searchPlaceholder: "Search Users",
            resultsDisplay: edges.newResultsDisplay({
                id: "results",
                category: "results",
                renderer: edges.bs3.newResultsFieldsByRowRenderer({
                    rowDisplay: [
                        [{pre: "<h3>", field: "id", post: "</h3>"}],
                        [
                            {pre: '<a href="mailto:', field: "email", post: '">'},
                            {field: "email", post: '</a>'}
                        ],
                        [{pre: "<strong>Role(s)</strong>: <em>", field: "role", post: "</em>"}],
                        [{pre: "<strong>Account Created</strong>: ", field: "created_date"}],
                        [{pre: "<strong>Account Last Modified</strong>: ", field: "last_updated"}],
                        [
                            {valueFunction: doaj.userSearch.userJournalsLink},
                            {valueFunction: doaj.userSearch.editUserLink}
                        ]
                    ]
                })
            }),
            fieldDisplays: {
                "role.exact": "Role",
                "created_date": "Created Date"
            },
            rangeFunctions: {
                "created_date": doaj.valueMaps.displayYearPeriod
            },
            openingQuery: es.newQuery({size: 25})
        });

        doaj.userSearch.activeEdges[selector] = e;
    }
}

jQuery(document).ready(function($) {
    doaj.userSearch.init();
});
