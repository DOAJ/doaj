// ~~ SystemObjectsSearch:Feature ~~
// ~~-> Edges:Technology ~~
//
// Admin-only search interfaces for system objects.
// Uses doaj.components.makeSearch() from doaj.fieldrender.edges.js - each search
// is defined with a few lines of config.

doaj.systemObjectSearch = {

    activeEdges: {},

    //-----------------------------
    // Generic JSON results renderer
    //-----------------------------
    // Displays each result as pretty-printed JSON.
    // Used as the default results display for system objects where no custom rendering is needed.

    newJSONResultsRenderer: function(params) {
        return edges.instantiate(doaj.systemObjectSearch.JSONResultsRenderer, params, edges.newRenderer);
    },

    JSONResultsRenderer: function(params) {
        this.namespace = "doaj-json-results";
        this.noResultsText = edges.getParam(params.noResultsText, "No results found.");

        this.draw = function() {
            if (this.component.results === false || this.component.results.length === 0) {
                this.component.context.html("<p>" + this.noResultsText + "</p>");
                return;
            }
            var frag = "";
            for (var i = 0; i < this.component.results.length; i++) {
                var res = this.component.results[i];
                frag += '<div class="edges-bs3-results-fields-by-row-record" style="margin-bottom: 1em; border-bottom: 1px solid #ddd; padding-bottom: 1em;">';
                frag += '<pre style="white-space: pre-wrap; word-wrap: break-word; background: #f5f5f5; padding: 10px; font-size: 12px;">';
                frag += edges.escapeHtml(JSON.stringify(res, null, 2));
                frag += '</pre>';
                frag += '</div>';
            }
            this.component.context.html(frag);
        };
    },

    // Builds a resultsDisplay component using the JSON renderer
    jsonResultsDisplay: function() {
        return edges.newResultsDisplay({
            id: "results",
            category: "results",
            renderer: doaj.systemObjectSearch.newJSONResultsRenderer()
        });
    },

    //-----------------------------
    // Per-object init functions
    //-----------------------------

    initProvenance: function() {
        var e = doaj.components.makeSearch({
            selector: "#provenance_search",
            searchUrl: doaj.edgeUtil.url.build("/admin_query/provenance/_search"),
            facets: [
                doaj.components.refiningAndFacet({id: "user", field: "user.exact", display: "User"}),
                doaj.components.refiningAndFacet({id: "type", field: "type.exact", display: "Object Type"}),
                doaj.components.refiningAndFacet({id: "subtype", field: "subtype.exact", display: "Subtype"}),
                doaj.components.refiningAndFacet({id: "action", field: "action.exact", display: "Action"}),
                doaj.components.monthDateHistogramFacet({id: "created_date", field: "created_date", display: "Date"})
            ],
            sortOptions: [
                {"display": "Date Created", "field": "created_date"},
                {"display": "User", "field": "user.exact"}
            ],
            fieldOptions: [
                {"display": "User", "field": "user"},
                {"display": "Resource ID", "field": "resource_id"},
                {"display": "Action", "field": "action"},
                {"display": "Object Type", "field": "type"}
            ],
            searchPlaceholder: "Search Provenance Records",
            resultsDisplay: doaj.systemObjectSearch.jsonResultsDisplay(),
            fieldDisplays: {
                "user.exact": "User",
                "type.exact": "Object Type",
                "subtype.exact": "Subtype",
                "action.exact": "Action",
                "created_date": "Date"
            },
            rangeFunctions: {
                "created_date": doaj.valueMaps.displayYearMonthPeriod
            }
        });
        doaj.systemObjectSearch.activeEdges["#provenance_search"] = e;
    },

    initFileUploads: function() {
        var e = doaj.components.makeSearch({
            selector: "#file_uploads_search",
            searchUrl: doaj.edgeUtil.url.build("/admin_query/upload/_search"),
            facets: [
                doaj.components.refiningAndFacet({id: "status", field: "status.exact", display: "Status"}),
                doaj.components.refiningAndFacet({id: "owner", field: "owner.exact", display: "Owner"}),
                doaj.components.refiningAndFacet({id: "schema", field: "schema.exact", display: "Schema"}),
                doaj.components.monthDateHistogramFacet({id: "created_date", field: "created_date", display: "Date"})
            ],
            sortOptions: [
                {"display": "Date Created", "field": "created_date"},
                {"display": "Owner", "field": "owner.exact"}
            ],
            fieldOptions: [
                {"display": "Owner", "field": "owner"},
                {"display": "Filename", "field": "filename"},
                {"display": "Status", "field": "status.exact"}
            ],
            searchPlaceholder: "Search File Uploads",
            resultsDisplay: doaj.systemObjectSearch.jsonResultsDisplay(),
            fieldDisplays: {
                "status.exact": "Status",
                "owner.exact": "Owner",
                "schema.exact": "Schema",
                "created_date": "Date"
            },
            rangeFunctions: {
                "created_date": doaj.valueMaps.displayYearMonthPeriod
            }
        });
        doaj.systemObjectSearch.activeEdges["#file_uploads_search"] = e;
    },

    initBulkUploads: function() {
        var e = doaj.components.makeSearch({
            selector: "#bulk_uploads_search",
            searchUrl: doaj.edgeUtil.url.build("/admin_query/bulk_articles/_search"),
            facets: [
                doaj.components.refiningAndFacet({id: "status", field: "status.exact", display: "Status"}),
                doaj.components.refiningAndFacet({id: "owner", field: "owner.exact", display: "Owner"}),
                doaj.components.monthDateHistogramFacet({id: "created_date", field: "created_date", display: "Date"})
            ],
            sortOptions: [
                {"display": "Date Created", "field": "created_date"},
                {"display": "Owner", "field": "owner.exact"}
            ],
            fieldOptions: [
                {"display": "Owner", "field": "owner"},
                {"display": "Status", "field": "status.exact"}
            ],
            searchPlaceholder: "Search Bulk Uploads",
            resultsDisplay: doaj.systemObjectSearch.jsonResultsDisplay(),
            fieldDisplays: {
                "status.exact": "Status",
                "owner.exact": "Owner",
                "created_date": "Date"
            },
            rangeFunctions: {
                "created_date": doaj.valueMaps.displayYearMonthPeriod
            }
        });
        doaj.systemObjectSearch.activeEdges["#bulk_uploads_search"] = e;
    },

    initCache: function() {
        var e = doaj.components.makeSearch({
            selector: "#cache_search",
            searchUrl: doaj.edgeUtil.url.build("/admin_query/cache/_search"),
            sortOptions: [
                {"display": "Date Created", "field": "created_date"},
                {"display": "Last Updated", "field": "last_updated"}
            ],
            searchPlaceholder: "Search Cache",
            resultsDisplay: doaj.systemObjectSearch.jsonResultsDisplay(),
            openingQuery: es.newQuery({size: 25})
        });
        doaj.systemObjectSearch.activeEdges["#cache_search"] = e;
    },

    initLocks: function() {
        var e = doaj.components.makeSearch({
            selector: "#locks_search",
            searchUrl: doaj.edgeUtil.url.build("/admin_query/lock/_search"),
            facets: [
                doaj.components.refiningAndFacet({id: "type", field: "type.exact", display: "Type"}),
                doaj.components.refiningAndFacet({id: "username", field: "username.exact", display: "Username"}),
                doaj.components.monthDateHistogramFacet({id: "created_date", field: "created_date", display: "Date"})
            ],
            sortOptions: [
                {"display": "Date Created", "field": "created_date"},
                {"display": "Expires", "field": "expires"},
                {"display": "Username", "field": "username.exact"}
            ],
            fieldOptions: [
                {"display": "Username", "field": "username"},
                {"display": "About (resource ID)", "field": "about"}
            ],
            searchPlaceholder: "Search Locks",
            resultsDisplay: doaj.systemObjectSearch.jsonResultsDisplay(),
            fieldDisplays: {
                "type.exact": "Type",
                "username.exact": "Username",
                "created_date": "Date"
            },
            rangeFunctions: {
                "created_date": doaj.valueMaps.displayYearMonthPeriod
            }
        });
        doaj.systemObjectSearch.activeEdges["#locks_search"] = e;
    },

    initPreservation: function() {
        var e = doaj.components.makeSearch({
            selector: "#preservation_search",
            searchUrl: doaj.edgeUtil.url.build("/admin_query/preserve/_search"),
            facets: [
                doaj.components.refiningAndFacet({id: "status", field: "status.exact", display: "Status"}),
                doaj.components.refiningAndFacet({id: "owner", field: "owner.exact", display: "Owner"}),
                doaj.components.monthDateHistogramFacet({id: "created_date", field: "created_date", display: "Date"})
            ],
            sortOptions: [
                {"display": "Date Created", "field": "created_date"},
                {"display": "Owner", "field": "owner.exact"}
            ],
            fieldOptions: [
                {"display": "Owner", "field": "owner"},
                {"display": "Filename", "field": "filename"},
                {"display": "Status", "field": "status.exact"}
            ],
            searchPlaceholder: "Search Preservation Files",
            resultsDisplay: doaj.systemObjectSearch.jsonResultsDisplay(),
            fieldDisplays: {
                "status.exact": "Status",
                "owner.exact": "Owner",
                "created_date": "Date"
            },
            rangeFunctions: {
                "created_date": doaj.valueMaps.displayYearMonthPeriod
            }
        });
        doaj.systemObjectSearch.activeEdges["#preservation_search"] = e;
    },

    initArticleTombstones: function() {
        var e = doaj.components.makeSearch({
            selector: "#article_tombstones_search",
            searchUrl: doaj.edgeUtil.url.build("/admin_query/article_tombstone/_search"),
            facets: [
                doaj.components.monthDateHistogramFacet({id: "created_date", field: "created_date", display: "Date Deleted"})
            ],
            sortOptions: [
                {"display": "Date Deleted", "field": "created_date"},
                {"display": "Last Updated", "field": "last_updated"}
            ],
            fieldOptions: [
                {"display": "DOI", "field": "bibjson.identifier.id"},
                {"display": "Title", "field": "bibjson.title"},
                {"display": "Author", "field": "bibjson.author.name"}
            ],
            searchPlaceholder: "Search Article Tombstones",
            resultsDisplay: doaj.systemObjectSearch.jsonResultsDisplay(),
            fieldDisplays: {
                "created_date": "Date Deleted"
            },
            rangeFunctions: {
                "created_date": doaj.valueMaps.displayYearMonthPeriod
            }
        });
        doaj.systemObjectSearch.activeEdges["#article_tombstones_search"] = e;
    },

    initDraftApplications: function() {
        var e = doaj.components.makeSearch({
            selector: "#draft_applications_search",
            searchUrl: doaj.edgeUtil.url.build("/admin_query/draft_application/_search"),
            facets: [
                doaj.components.refiningAndFacet({id: "owner", field: "admin.owner.exact", display: "Owner"}),
                doaj.components.monthDateHistogramFacet({id: "created_date", field: "created_date", display: "Date"})
            ],
            sortOptions: [
                {"display": "Date Created", "field": "created_date"},
                {"display": "Last Updated", "field": "last_updated"}
            ],
            fieldOptions: [
                {"display": "Title", "field": "bibjson.title"},
                {"display": "ISSN", "field": "bibjson.identifier.id"},
                {"display": "Owner", "field": "admin.owner"}
            ],
            searchPlaceholder: "Search Draft Applications",
            resultsDisplay: doaj.systemObjectSearch.jsonResultsDisplay(),
            fieldDisplays: {
                "admin.owner.exact": "Owner",
                "created_date": "Date"
            },
            rangeFunctions: {
                "created_date": doaj.valueMaps.displayYearMonthPeriod
            }
        });
        doaj.systemObjectSearch.activeEdges["#draft_applications_search"] = e;
    },

    initHarvesterState: function() {
        var e = doaj.components.makeSearch({
            selector: "#harvester_state_search",
            searchUrl: doaj.edgeUtil.url.build("/admin_query/harvester_state/_search"),
            facets: [
                doaj.components.refiningAndFacet({id: "status", field: "status.exact", display: "Status"}),
                doaj.components.refiningAndFacet({id: "account", field: "account.exact", display: "Account"})
            ],
            sortOptions: [
                {"display": "Last Updated", "field": "last_updated"},
                {"display": "Date Created", "field": "created_date"},
                {"display": "Account", "field": "account.exact"}
            ],
            fieldOptions: [
                {"display": "Account", "field": "account"},
                {"display": "ISSN", "field": "issn"},
                {"display": "Status", "field": "status.exact"}
            ],
            searchPlaceholder: "Search Harvester State",
            resultsDisplay: doaj.systemObjectSearch.jsonResultsDisplay(),
            fieldDisplays: {
                "status.exact": "Status",
                "account.exact": "Account"
            },
            openingQuery: es.newQuery({
                sort: [{field: "last_updated", order: "desc"}],
                size: 25
            })
        });
        doaj.systemObjectSearch.activeEdges["#harvester_state_search"] = e;
    },

    initAutochecks: function() {
        var e = doaj.components.makeSearch({
            selector: "#autochecks_search",
            searchUrl: doaj.edgeUtil.url.build("/admin_query/autocheck/_search"),
            facets: [
                doaj.components.refiningAndFacet({id: "checked_by", field: "checks.checked_by.exact", display: "Checked By"}),
                doaj.components.monthDateHistogramFacet({id: "created_date", field: "created_date", display: "Date"})
            ],
            sortOptions: [
                {"display": "Date Created", "field": "created_date"},
                {"display": "Last Updated", "field": "last_updated"}
            ],
            fieldOptions: [
                {"display": "Application ID", "field": "application"},
                {"display": "Journal ID", "field": "journal"}
            ],
            searchPlaceholder: "Search Autochecks",
            resultsDisplay: doaj.systemObjectSearch.jsonResultsDisplay(),
            fieldDisplays: {
                "checks.checked_by.exact": "Checked By",
                "created_date": "Date"
            },
            rangeFunctions: {
                "created_date": doaj.valueMaps.displayYearMonthPeriod
            }
        });
        doaj.systemObjectSearch.activeEdges["#autochecks_search"] = e;
    }
};
