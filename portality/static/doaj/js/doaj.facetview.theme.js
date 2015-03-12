var licenceMap = {
    "CC BY" : ["/static/doaj/images/cc/by.png", "http://creativecommons.org/licenses/by/3.0/"],
    "CC BY-NC" : ["/static/doaj/images/cc/by-nc.png", "http://creativecommons.org/licenses/by-nc/3.0/"],
    "CC BY-NC-ND" : ["/static/doaj/images/cc/by-nc-nd.png", "http://creativecommons.org/licenses/by-nc-nd/3.0/"],
    "CC BY-NC-SA" : ["/static/doaj/images/cc/by-nc-sa.png", "http://creativecommons.org/licenses/by-nc-sa/3.0/"],
    "CC BY-ND" : ["/static/doaj/images/cc/by-nd.png", "http://creativecommons.org/licenses/by-nd/3.0/"],
    "CC BY-SA" : ["/static/doaj/images/cc/by-sa.png", "http://creativecommons.org/licenses/by-sa/3.0/"]
};


/*
Function which translates the month - we'll use this in the display of results

var months_english = {
    '1': 'January',
    '2': 'February',
    '3': 'March',
    '4': 'April',
    '5': 'May',
    '6': 'June',
    '7': 'July',
    '8': 'August',
    '9': 'September',
    '10': 'October',
    '11': 'November',
    '12': 'December'
};

function expand_month() {
    this.innerHTML = months_english[this.innerHTML.replace(/^0+/,"")];
}
 */

/////////////////////////////////////////////////////////////////
// functions which override the bootstrap2 theme
////////////////////////////////////////////////////////////////

function searchingNotification(options) {
    return '<div class="progress progress-danger progress-striped active notify_loading" id="search-progress-bar"><div class="bar">Loading, please wait...</div></div>'
}

function setFacetOpenness(options, context, facet) {
    var el = context.find("#facetview_filter_" + safeId(facet.field));
    var open = facet["open"];
    if (open) {
        el.find(".facetview_filtershow").find("i").removeClass("icon-plus");
        el.find(".facetview_filtershow").find("i").addClass("icon-minus");
        el.find(".facetview_filteroptions").show();
        el.find(".facetview_filtervalue").show();
        el.addClass("no-bottom");
    } else {
        el.find(".facetview_filtershow").find("i").removeClass("icon-minus");
        el.find(".facetview_filtershow").find("i").addClass("icon-plus");
        el.find(".facetview_filteroptions").hide();
        el.find(".facetview_filtervalue").hide();
        el.removeClass("no-bottom");
    }
}

function renderNotFound() {
    return "<tr class='facetview_not_found'>" +
        "<td>No results found that match your search criteria.  Try removing some of the filters you have set, or modifying the text in the search box.</td>" +
        "</tr>";
}

/////////////////////////////////////////////////////////////////
// functions for use as plugins to be passed to facetview instances
////////////////////////////////////////////////////////////////

function doajScrollTop(options, context) {
    $(".facetview_increment").click(function(event) {
        event.preventDefault();
        $('html, body').animate({
            scrollTop: $("body").offset().top
        }, 1000);
    });

    $(".facetview_decrement").click(function(event) {
        event.preventDefault();
        $('html, body').animate({
            scrollTop: $("body").offset().top
        }, 1000);
    });
}

function doajPostRender(options, context) {
    doajScrollTop(options, context);

    // toggle the abstracts
    $('.abstract_text', context).hide();
    $(".abstract_action", context).unbind("click").click(function(event) {
        event.preventDefault();
        var el = $(this);
        var text = el.html();
        var newText = text == "(expand)" ? "(collapse)" : "(expand)";
        el.html(newText);
        $('.abstract_text[rel="' + el.attr("rel") + '"]').slideToggle(300);
        return true;
    });
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
        "<td><p>You do not have any journals in the DOAJ that meet your search criteria</p>" +
        "<p>If you have not set any search criteria, this means you do not currently have any journals in the DOAJ.</p>" +
        "</tr>";
}

function publisherReapplicationNotFound() {
    return "<tr class='facetview_not_found'>" +
        "<td><p>You do not have any active reapplications that meet your search criteria</p>" +
        "<p>If you have not set any search criteria, you do not have any further reapplications to complete at this stage.</p>" +
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

var publisherStatusMapping = {
    "reapplication" : {"text" : "pending" }
};
function publisherStatusMap(value) {
    if (statusMapping.hasOwnProperty(value)) {
        return statusMapping[value];
    }
    return value;
}