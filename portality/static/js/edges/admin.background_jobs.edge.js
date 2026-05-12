// ~~ BackgroundJobsSearch:Feature ~~
doaj.adminBackgroundJobsSearch = {
    activeEdges : {},

    newBGResultsRenderer : function(params) {
        return edges.instantiate(doaj.adminBackgroundJobsSearch.BGResultsRenderer, params, edges.newRenderer);
    },
    BGResultsRenderer : function(params) {
        this.noResultsText = edges.getParam(params.noResultsText, "No Results");

        this.namespace = "doaj-bg-results";

        this.draw = function(params) {
            var frag = "";
            if (this.component.results !== false && this.component.results.length === 0) {
                this.component.context.html(this.noResultsText);
                return;
            }

            for (var k = 0; k < this.component.results.length; k++) {
                var resultobj = this.component.results[k];
                var firstRow = "";
                if (resultobj.action) {
                    firstRow += "<strong>" + resultobj.action + "</strong>";
                }
                if (resultobj.user) {
                    firstRow += " by <strong>" + resultobj.user + "</strong>";
                }
                if (resultobj.status) {
                    var color = "#000088";
                    if (resultobj.status === "complete") {
                        color = "#008800"
                    } else if (resultobj.status === "error") {
                        color = "#880000";
                    } else if (resultobj.status === "cancelled") {
                        color = "#b47e18";
                    }
                    firstRow += " status: <strong style='color: " + color + "'>" + resultobj.status + "</strong>";
                }

                var dateRow = "";

                // add the date added to doaj
                if (resultobj.created_date) {
                    dateRow += "Job Created: " + doaj.dates.humanYearMonth(resultobj.created_date) + "<br>";
                }
                if (resultobj.last_updated) {
                    dateRow += "Job Last Updated: " + doaj.dates.humanYearMonth(resultobj.last_updated) + "<br>";
                }

                var paramsBlock = "";
                if (resultobj.params) {
                    paramsBlock += "<strong>Parameters:</strong><br>";
                    for (var key in resultobj.params) {
                        var val = resultobj.params[key];
                        if ($.isArray(val)) {
                            val = val.join(', ');
                        }
                        paramsBlock += key + " -- " + edges.escapeHtml(val) + "<br>";
                    }
                }

                var refsBlock = "";
                if (resultobj.reference) {
                    paramsBlock += "<strong>Reference:</strong><br>";
                    for (var key in resultobj.reference) {
                        var val = resultobj.reference[key];
                        if ($.isArray(val) || $.isPlainObject(val)) {
                            val = JSON.stringify(val);
                        }
                        refsBlock += key + " -- " + edges.escapeHtml(val) + "<br>";
                    }
                }

                var auditBlock = "";
                if (resultobj.audit) {
                    auditBlock += "<strong>Audit Messages:</strong><br>";
                    for (var i = 0; i < resultobj.audit.length; i++) {
                        var audit = resultobj.audit[i];
                        auditBlock += audit.timestamp + " -- " + edges.escapeHtml(audit.message) + "<br>";
                    }
                }

                var containerClass = edges.css_classes(this.namespace, "container", this);
                var moreInfoClass = edges.css_classes(this.namespace, "more", this);
                var toggleClass = edges.css_classes(this.namespace, "toggle", this);

                var expandBlock = "<div data-id='" + resultobj.id + "' class='" + moreInfoClass + "' style='display: none'>";
                expandBlock += paramsBlock;
                expandBlock += refsBlock;
                expandBlock += auditBlock;
                expandBlock += "</div>";

                var result = '<div class="edges-bs3-results-fields-by-row-record ' + containerClass + '">';
                result += "<div class='row-fluid'><div class='span12'>";
                result += firstRow + "<br>";
                result += `Outcome Status: ${resultobj.outcome_status}<br />`;
                result += "Job ID: " + resultobj.id + "<br>";
                result += 'On Queue: ' + resultobj.queue_id + '<br>';
                result += dateRow + "<br>";
                result += '<a href="#" data-id="' + resultobj.id + '" class="' + toggleClass + '">More Information</a><br>';
                result += expandBlock;
                result += "</div></div>";
                result += "</div>";

                frag += result;
            }

            this.component.context.html(frag);

            var moreInfoSelector = edges.css_class_selector(this.namespace, "toggle", this);
            edges.on(moreInfoSelector, "click", this, "toggleMoreInformation");
        };

        this.toggleMoreInformation = function(element) {
            var moreSelector = edges.css_class_selector(this.namespace, "more", this);
            var id = $(element).attr("data-id");
            var segment = this.component.context.find(moreSelector).filter("[data-id=" + id + "]");
            segment.slideToggle(300);
        };
    },

    init : function(params) {
        if (!params) { params = {} }

        var selector = params.selector || "#background_jobs";

        var e = doaj.components.makeSearch({
            selector: selector,
            searchUrl: doaj.buildUrl(doaj.adminBackgroundJobsSearchConfig.searchPath),
            facets: [
                doaj.components.refiningAndFacet({id: "action", field: "action.exact", display: "Action", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "user", field: "user.exact", display: "Submitted By", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "status", field: "status.exact", display: "Status", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "queue_id", field: "queue_id.exact", display: "On Queue", deactivateThreshold: 1}),
                doaj.components.refiningAndFacet({id: "outcome_status", field: "outcome_status.exact", display: "Outcome Status", deactivateThreshold: 1})
            ],
            sortOptions: [
                {'display': 'Created Date', 'field': 'created_date'},
                {'display': 'Last Modified Date', 'field': 'last_updated'}
            ],
            fieldOptions: [
                {'display': 'ID', 'field': 'id.exact'},
                {'display': 'Action', 'field': 'action.exact'},
                {'display': 'Submitted By', 'field': 'user.exact'},
                {'display': 'Status', 'field': 'status.exact'},
                {'display': 'Outcome Status', 'field': 'outcome_status.exact'}
            ],
            searchPlaceholder: "Search Background Jobs",
            sizeOptions: [10, 25, 50, 100],
            resultsDisplay: edges.newResultsDisplay({
                id: "results",
                category: "results",
                renderer: doaj.adminBackgroundJobsSearch.newBGResultsRenderer()
            }),
            fieldDisplays: {
                'action.exact': 'Action',
                'user.exact': 'Submitted By',
                'status.exact': 'Status',
                'outcome_status.exact': 'Outcome Status',
                'queue_id.exact': 'On Queue'
            },
            openingQuery: es.newQuery({
                sort: {"field": "created_date", "order": "desc"}
            })
        });

        doaj.adminBackgroundJobsSearch.activeEdges[selector] = e;
    }
}

jQuery(document).ready(function($) {
    doaj.adminBackgroundJobsSearch.init();
});
