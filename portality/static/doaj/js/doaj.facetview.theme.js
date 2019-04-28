
/////////////////////////////////////////////////////////////////
// functions for use as plugins to be passed to facetview instances
////////////////////////////////////////////////////////////////

function doajFixedQueryWidgetPostRender(options, context) {
    doajToggleAbstract(options, context);
}

function doajJAPostRender(options, context) {
    // first run the default post render
    doajPostRender(options, context);

    // now add the handlers for the article delete
    $(".delete_article_link").unbind("click");
    $(".delete_article_link").click(function(event) {
        event.preventDefault();

        function success_callback(data) {
            alert("The article was successfully deleted");
            $(".facetview_freetext").trigger("keyup"); // cause a search
        }

        function error_callback() {
            alert("There was an error deleting the article")
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
}

function doajEGPostRender(options, context) {
    // first run the default post render
    doajPostRender(options, context);

    // now add the handlers for the article delete
    $(".delete_editor_group_link").unbind("click")
    $(".delete_editor_group_link").click(function(event) {
        event.preventDefault();

        function success_callback(data) {
            alert("The group was successfully deleted")
            $(".facetview_freetext").trigger("keyup") // cause a search
        }

        function error_callback() {
            alert("There was an error deleting the group")
        }

        var c = confirm("Are you really really sure?  You can't undo this operation!")
        if (c) {
            var href = $(this).attr("href")
            var obj = {"delete" : "true"}
            $.ajax({
                type: "POST",
                url: href,
                data: obj,
                success : success_callback,
                error: error_callback
            })
        }
    });
}



function editorGroupJournalNotFound() {
    return "<tr class='facetview_not_found'>" +
        "<td><p>There are no journals for your editor group(s) that meet the search criteria</p>" +
        "<p>If you have not set any search criteria, this means there are no journals currently allocated to your group</p>" +
        "</tr>";
}

function editorGroupApplicationNotFound() {
    return "<tr class='facetview_not_found'>" +
        "<td><p>There are no applications for your editor group(s) that meet the search criteria</p>" +
        "<p>If you have not set any search criteria, this means there are no applications currently allocated to your group</p>" +
        "</tr>";
}

function associateJournalNotFound() {
    return "<tr class='facetview_not_found'>" +
        "<td><p>There are no journals assigned to you that meet the search criteria</p>" +
        "<p>If you have not set any search criteria, this means there are no journals currently assigned to you</p>" +
        "</tr>";
}

function associateApplicationNotFound() {
    return "<tr class='facetview_not_found'>" +
        "<td><p>There are no applications assigned to you that meet the search criteria</p>" +
        "<p>If you have not set any search criteria, this means there are no applications currently assigned to you</p>" +
        "</tr>";
}

function publisherJournalNotFound() {
    return "<tr class='facetview_not_found'>" +
        "<td><p>This tab normally shows the journals which are indexed in DOAJ and in your account. It doesn't look like that you have any journals in DOAJ currently. " +
        "Please <a href=" + document.location.origin + "/application/new>submit an application</a> for any open access, peer-reviewed journals which you would like to see in DOAJ.</p>" +
        "</tr>";
}

function publisherUpdateRequestNotFound() {
    return "<tr class='facetview_not_found'>" +
        "<td><p>You do not have any active update requests that meet your search criteria</p>" +
        "<p>If you have not set any search criteria, you do not have any update requests at this time.</p>" +
        "</tr>";
}

//////////////////////////////////////////////////////
// value functions for facet displays
/////////////////////////////////////////////////////

var authorPaysMapping = {
    "N" : "No Charges",
    "Y" : "Has Charges",
    "CON" : "Conditional charges",
    "NY" : "No info available"
};
function authorPaysMap(value) {
    if (authorPaysMapping.hasOwnProperty(value)) {
        return authorPaysMapping[value];
    }
    return value;
}

function publisherStatusMap(value) {
    if (applicationStatusMapping.hasOwnProperty(value)) {
        return applicationStatusMapping[value];
    }
    return value;
}

// This must be updated in line with the list in formcontext/choices.py
var applicationStatusMapping = {
    'update_request' : 'Update Request',
    'revisions_required' : 'Revisions Required',
    'pending' : 'Pending',
    'in progress' : 'In Progress',
    'completed' : 'Completed',
    'on hold' : 'On Hold',
    'ready' : 'Ready',
    'rejected' : 'Rejected',
    'accepted' : 'Accepted'
};
function adminStatusMap(value) {
    if (applicationStatusMapping.hasOwnProperty(value)) {
        return applicationStatusMapping[value];
    }
    return value;
}

//////////////////////////////////////////////////////
// date formatting function
/////////////////////////////////////////////////////

function humanDateTime(datestr) {
    var date = new Date(datestr);
    var dom = date.getUTCDate();
    var monthnum = date.getUTCMonth();
    var year = date.getUTCFullYear();
    var hour = date.getUTCHours();
    var minute = date.getUTCMinutes();

    if (String(hour).length === 1) {
        hour = "0" + String(hour);
    }

    if (String(minute).length === 1) {
        minute = "0" + String(minute);
    }

    return String(dom) + " " + monthmap[monthnum] + " " + String(year) + " at " + String(hour) + ":" + String(minute);
}

//////////////////////////////////////////////////////
// fixed query widget generation
/////////////////////////////////////////////////////

var doajenvmap = {
    "http://localhost:5004" : "dev",
    "https://testdoaj.cottagelabs.com" : "test",
    "https://stagingdoaj.cottagelabs.com" : "staging"
};

function doajDetectCurrentEnv(){
    // Return env, if one of recognised locations, default to production.
    return doajenvmap[document.location.origin] || "production";
}

function doajGenFixedQueryWidget(widget_fv_opts){
    // Generates code for the fixed query widget

    var source = elasticSearchQuery({"options" : widget_fv_opts, "include_facets" : widget_fv_opts.include_facets_in_url, "include_fields" : widget_fv_opts.include_fields_in_url});

    // Code to get a version of jQuery
    var jq = '<script type="text/javascript">!window.jQuery && document.write("<scr" + "ipt type=\\"text/javascript\\" src=\\"http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js\\"></scr" + "ipt>"); </script>';

    // Get the env to serve the correct version of the widget file
    var env_suffix = "";
    var doaj_env = doajDetectCurrentEnv();
    if (doaj_env != "production") {
        env_suffix = "_" + doaj_env;
    }

    // Code to configure the widget
    var frag = '<script type="text/javascript">var doaj_url="'+ document.location.origin + '"; var SEARCH_CONFIGURED_OPTIONS=' + JSON.stringify(source) + '</script>';
    frag += '<script src="' + document.location.origin +'/static/widget/fixed_query' + env_suffix + '.js" type="text/javascript"></script><div id="doaj-fixed-query-widget"></div></div>';
    return jq + frag
}
