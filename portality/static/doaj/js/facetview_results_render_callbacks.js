// use a closure to allow attaching the mapping of values directly to
// the function, a bit cleaner






fv_make_continuation = (function (resultobj) {
    var that = function(resultobj) {
        if (!resultobj.suggestion && !resultobj.bibjson.journal) {
            // if it's not a suggestion or an article .. (it's a
            // journal!)
            // we really need to expose _type ...
            var result = '<a class="edit_journal_link pull-right" href="';
            result += journal_edit_url;
            result += resultobj['id'];
            result += '/continue?type=is_replaced_by" target="_blank"';
            result += '>Make a succeeding continuation</a>';

            result += "<span class='pull-right'>&nbsp;|&nbsp;</span>";

            result += '<a class="edit_journal_link pull-right" href="';
            result += journal_edit_url;
            result += resultobj['id'];
            result += '/continue?type=replaces" target="_blank"';
            result += '>Make a preceding continuation</a>';

            return result;
        }
        return false;
    };
    return that;
})();




fv_user_journals = (function (resultobj) {
    var that = function(resultobj) {
        var q = {
            "query":{
                "filtered":{
                    "filter":{
                        "bool":{
                            "must":[{"term":{"admin.owner.exact":resultobj.id}}]
                        }
                    },
                    "query":{"match_all":{}}
                }
            }
        };
        // var q = {"query" : {"bool" : {"must" : [{"term" : {"admin.owner.exact" : resultobj.id}}]}}};
        return '<a class="pull-right" style="margin-left: 10px; margin-right: 10px" href="/admin/journals?source=' + encodeURIComponent(JSON.stringify(q)) + '">View Journals</a>'
    };
    return that;
})();


fv_edit_update_request = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj['suggestion']) {
            if (resultobj.admin && resultobj.admin.application_status) {
                var status = resultobj.admin.application_status;
                var result = "";
                var view = '(<a href="' + update_request_readonly_url + resultobj['id'] + '">view request</a>)';
                if (status === "update_request" || status == "revisions_required") {
                    var actionUrl = update_request_edit_url + resultobj.admin.current_journal;
                    result = '<span class="pull-right"><a class="edit_suggestion_link" href="' + actionUrl;
                    result += '"';
                    result += '>Edit this update request</a> | <a href="' + actionUrl + '" class="delete_suggestion_link">Delete this update request</a></span>';
                } else  if (status !== "rejected" && status !== "accepted") {
                    result = '<span class="pull-right">This update request is currently being reviewed by an Editor ' + view + '.</span>';
                } else if (status === "rejected") {
                    result = '<span class="pull-right">This update request has been rejected ' + view + '.</span>';
                } else if (status === "accepted") {
                    result = '<span class="pull-right">This update request has been accepted, and your journal in DOAJ updated ' + view + '.</span>';
                }
                return result;
            }
        }
        return false;
    };
    return that;
})();

fv_make_update_request = (function (resultobj) {
    var that = function(resultobj) {
        if (resultobj.admin && resultobj.admin.hasOwnProperty("in_doaj")) {
            if (resultobj.admin.in_doaj === false) {
                return ""
            }
        }
        if (!resultobj.suggestion && !resultobj.bibjson.journal) {
            // if it's not a suggestion or an article .. (it's a
            // journal!)
            // we really need to expose _type ...
            var result = "";
            if (resultobj.admin && resultobj.admin.current_application) {
                var idquery = '%7B%22query%22%3A%7B%22query_string%22%3A%7B%22query%22%3A%22' + resultobj['id'] + '%22%7D%7D%7D';
                result = '<a class="edit_journal_link pull-right" href="' + journal_update_requests_url + "?source=" + idquery + '">View current update request</a>';
            } else {
                result = '<a class="edit_journal_link pull-right" href="';
                result += journal_update_url;
                result += resultobj['id'] + '"';
                result += '>Submit an update</a>';
            }
            return result;
        }
        return false;
    };
    return that;
})();

fv_related_applications = (function (resultobj) {
    var that = function(resultobj) {
        var result = "";
        if (resultobj.admin) {
            if (resultobj.admin.current_application) {
                var fvurl = applications_fv_url + '?source=%7B"query"%3A%7B"query_string"%3A%7B"query"%3A"' + resultobj.admin.current_application + '"%2C"default_operator"%3A"AND"%7D%7D%2C"from"%3A0%2C"size"%3A10%7D';
                result += "<strong>Current Update Request</strong>: <a href='" + fvurl + "'>" + resultobj.admin.current_application + "</a>";
            }
            if (resultobj.admin.related_applications && resultobj.admin.related_applications.length > 0) {
                if (result != "") {
                    result += "<br>";
                }
                result += "<strong>Related Records</strong>: ";
                for (var i = 0; i < resultobj.admin.related_applications.length; i++) {
                    if (i > 0) {
                        result += ", ";
                    }
                    var ra = resultobj.admin.related_applications[i];
                    var fvurl = applications_fv_url + '?source=%7B"query"%3A%7B"query_string"%3A%7B"query"%3A"' + ra.application_id + '"%2C"default_operator"%3A"AND"%7D%7D%2C"from"%3A0%2C"size"%3A10%7D';
                    var linkName = ra.date_accepted;
                    if (!linkName) {
                        linkName = ra.application_id;
                    }
                    result += "<a href='" + fvurl + "'>" + linkName + "</a>";
                }
            }
        }
        return result;
    };
    return that;
})();


