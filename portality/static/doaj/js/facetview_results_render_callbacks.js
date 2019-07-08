// use a closure to allow attaching the mapping of values directly to
// the function, a bit cleaner


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


