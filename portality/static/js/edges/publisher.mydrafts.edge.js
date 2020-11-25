$.extend(true, doaj, {

    publisherApplicationsSearch : {
        activeEdges : {},

        editUpdateRequest : function (value, resultobj, renderer) {
            if (resultobj['suggestion']) {
                if (resultobj.admin && resultobj.admin.application_status) {
                    var status = resultobj.admin.application_status;
                    var result = "";
                    var view = '(<a href="' + doaj.publisherUpdatesSearchConfig.journalReadOnlyUrl + resultobj['id'] + '">view request</a>)';
                    if (status === "update_request" || status === "revisions_required") {
                        var actionUrl = doaj.publisherUpdatesSearchConfig.journalUpdateUrl + resultobj.admin.current_journal;
                        result = '<span><a class="edit_suggestion_link" href="' + actionUrl;
                        result += '"';
                        result += '>Edit this update request</a> | <a href="' + actionUrl + '" class="delete_suggestion_link">Delete this update request</a></span>';
                    } else  if (status !== "rejected" && status !== "accepted") {
                        result = '<span>This update request is currently being reviewed by an Editor ' + view + '.</span>';
                    } else if (status === "rejected") {
                        result = '<span>This update request has been rejected ' + view + '.</span>';
                    } else if (status === "accepted") {
                        result = '<span>This update request has been accepted, and your journal in DOAJ updated ' + view + '.</span>';
                    }
                    return result;
                }
            }
            return false;
        },

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#publisher_applications";
            var search_url = current_scheme + "//" + current_domain + doaj.publisherApplicationsSearchConfig.searchPath;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                // results display
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer : doaj.renderers.newPublisherApplicationRenderer()
                })
            ];
            var e = edges.newEdge({
                selector: selector,
                template: doaj.templates.newPublisherApplications(),
                search_url: search_url,
                manageUrl: true,
                baseQuery: es.newQuery({
                    must: [
                        es.newTermsFilter({
                            field: "admin.application_status.exact",
                            values: ["revisions_requried", "pending", "in progress", "completed", "on hold", "ready", "draft"]
                        })
                    ],
                    sort: [{"field" : "last_updated", "order" : "desc"}],
                    size: 50
                }),
                components: components,
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact us.");
                    },
                    "edges:post-init" : function() {
                        feather.replace();
                    },
                    "edges:post-render" : function() {
                        feather.replace();
                    }
                }
            });
            doaj.publisherApplicationsSearch.activeEdges[selector] = e;
        }
    }
});


jQuery(document).ready(function($) {
    doaj.publisherApplicationsSearch.init();
});
