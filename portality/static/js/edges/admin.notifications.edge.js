// ~~ AdminNotifications:Edge -> Notifications:Feature ~~
// ~~-> Edges:Technology ~~
doaj.adminNotificationsSearch = {
    activeEdges : {},

    createdByMap : {
        "application:assed:acceptreject:notify": "Application: AssEd: Accepted/Rejected",
        "application:assed:assigned:notify" : "Application: AssEd: Assigned",
        "application:assed:inprogress:notify" : "Application: AssEd: Referred back",
        "application:editor:acceptreject:notify": "Application: Editor: Accepted/Rejected",
        "application:editor:completed:notify" : "Application: Editor: Completed",
        "application:editor_group:assigned:notify" : "Application: Editor: Group assigned",
        "application:editor:inprogress:notify" : "Application: Editor: Referred back",
        "application:maned:ready:notify" : "Application: ManEd: Editor Sets Ready",
        "application:publisher:accepted:notify" : "Application: Publisher: Accepted",
        "application:publisher:assigned:notify" : "Application: Publisher: Assigned Editor",
        "application:publisher:created:notify" : "Application: Publisher: Received",
        "application:publisher:inprogress:notify" : "Application: Publisher: In progress",
        "application:publisher:rejected:notify" : "Application: Publisher: Rejected",
        "application:publisher:quickreject:notify" : "Application: Publisher: Quick-rejected",
        "application:publisher:revision:notify" : "Application: Publisher: Requires revisions",
        "bg:job_finished:notify" : "Background Job: Admin: Finished",
        "journal:assed:assigned:notify" : "Journal: AssEd: Assigned",
        "journal:editor_group:assigned:notify": "Journal: Editor: Group assigned",
        "update_request:maned:editor_group_assigned:notify": "UR: ManEd: Assigned",
        "update_request:publisher:accepted:notify": "UR: Publisher: Accepted",
        "update_request:publisher:assigned:notify": "UR: Publisher: Assigned Editor",
        "update_request:publisher:rejected:notify": "UR: Publisher: Rejected",
        "update_request:publisher:submitted:notify": "UR: Publisher: Submitted"
    },

    init : function(params) {
        if (!params) { params = {} }

        var selector = params.selector || "#admin_notifications";

        let markdownConverter = new showdown.Converter({
            literalMidWordUnderscores: true
        });

        var e = doaj.components.makeSearch({
            selector: selector,
            searchUrl: doaj.edgeUtil.url.build(doaj.adminNotificationsSearchConfig.searchPath),
            facets: [
                doaj.components.refiningAndFacet({id: "who", field: "who.exact", display: "Notification For", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "created_by", field: "created_by.exact", display: "Notification", size: 20, orderBy: "term", orderDir: "asc", deactivateThreshold: 1, valueMap: doaj.adminNotificationsSearch.createdByMap}),
                doaj.components.refiningAndFacet({id: "classification", field: "classification.exact", display: "Type", deactivateThreshold: 1}),
                doaj.components.monthDateHistogramFacet({id: "created_date", field: "created_date", display: "Notification Month"})
            ],
            sortOptions: [
                {'display': 'Notification Date', 'field': 'created_date'}
            ],
            fieldOptions: [
                {'display': 'Notification For', 'field': 'who'},
                {'display': 'Title', 'field': 'short'},
                {'display': 'Body Text', 'field': 'long'}
            ],
            searchPlaceholder: "Search All Notifications",
            resultsDisplay: edges.newResultsDisplay({
                id: "results",
                category: "results",
                renderer: edges.bs3.newResultsFieldsByRowRenderer({
                    rowDisplay: [
                        [
                            {pre: "For <strong>", field: "who", post: "</strong>"},
                            {pre: " at <strong> ", field: "created_date", post: "</strong>"},
                            {pre: " by <strong> ", field: "created_by", post: "</strong>"},
                            {pre: " (", field: "classification", post: ")<br><br>"}
                        ],
                        [
                            {pre: "<strong>", field: "short", post: "</strong>"}
                        ],
                        [
                            {valueFunction: function(val, res) { return markdownConverter.makeHtml(res.long); }}
                        ],
                        [
                            {pre: '<a href="', field: "action", post: '" target="_blank">See action</a>'}
                        ]
                    ]
                })
            }),
            fieldDisplays: {
                "who.exact": "Who",
                "created_by.exact": "Action",
                "classification.exact": "Type",
                "created_date": "Notification Date"
            },
            valueMaps: {
                "created_by.exact": doaj.adminNotificationsSearch.createdByMap
            },
            rangeFunctions: {
                "created_date": doaj.valueMaps.displayYearMonthPeriod
            }
        });

        doaj.adminNotificationsSearch.activeEdges[selector] = e;
    }
}

jQuery(document).ready(function($) {
    doaj.adminNotificationsSearch.init();
});
