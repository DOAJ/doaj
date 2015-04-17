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

function doajPager(options) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * class: facetview_decrement - anchor to move the page back
     * class: facetview_increment - anchor to move the page forward
     * class: facetview_inactive_link - for links which should not have any effect (helpful for styling bootstrap lists without adding click features)
     *
     * should (not must) respect the config
     *
     * options.from - record number results start from (may be a string)
     * options.page_size - number of results per page
     * options.data.found - the total number of records in the search result set
     */

    // ensure our starting points are integers, then we can do maths on them
    var from = parseInt(options.from);
    var size = parseInt(options.page_size);

    // calculate the human readable values we want
    var to = from + size;
    from = from + 1; // zero indexed
    if (options.data.found < to) { to = options.data.found }
    var total = options.data.found;
    total = total.toLocaleString();

    var backlink = '<a alt="previous" title="previous" class="facetview_decrement pull-left" style="color:#333; cursor: pointer; font-size: 24px"><span class="icon icon-arrow-left"></span></a>';
    if (from < size) {
        backlink = '<a class="facetview_decrement facetview_inactive_link" style="color:#333">&nbsp;</a>'
    }

    var nextlink = '<a alt="next" title="next" class="facetview_increment pull-right" style="color:#333; cursor: pointer; font-size: 24px"><span class="icon icon-arrow-right"></span></a>';
    if (options.data.found <= to) {
        nextlink = '<a class="facetview_increment facetview_inactive_link" style="color:#333">&nbsp;</a>'
    }

    var meta = '<div class="row-fluid" style="font-size: 18px"><div class="span3">&nbsp;</div>';
    meta += '<div class="span1">' + backlink + '</div>';
    meta += '<div class="span4 text-center"><p style="font-weight: bold; text-align: center">' + from + ' &ndash; ' + to + ' of ' + total + '</p></div>';
    meta += '<div class="span1">' + nextlink + '</div>';

    return meta
}

function doajScrollTop(options, context) {
    $(".facetview_increment").click(function(event) {
        event.preventDefault();
        $('html, body').animate({
            scrollTop: $("body").offset().top
        }, 1);
    });

    $(".facetview_decrement").click(function(event) {
        event.preventDefault();
        $('html, body').animate({
            scrollTop: $("body").offset().top
        }, 1);
    });
}

function doajPostRender(options, context) {
    doajScrollTop(options, context);

    // toggle the abstracts
    $('.abstract_text', context).hide();
    $(".abstract_action", context).unbind("click").click(function(event) {
        event.preventDefault();
        var el = $(this);
        //var text = el.html();
        //var newText = text == "(expand)" ? "(collapse)" : "(expand)";
        //el.html(newText);
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
    "reapplication" : "pending"
};
function publisherStatusMap(value) {
    if (publisherStatusMapping.hasOwnProperty(value)) {
        return publisherStatusMapping[value];
    }
    return value;
}

//////////////////////////////////////////////////////
// date formatting function
/////////////////////////////////////////////////////

var monthmap = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"
];

function humanDate(datestr) {
    var date = new Date(datestr);
    var dom = date.getUTCDate();
    var monthnum = date.getUTCMonth();
    var year = date.getUTCFullYear();

    return String(dom) + " " + monthmap[monthnum] + " " + String(year);
}