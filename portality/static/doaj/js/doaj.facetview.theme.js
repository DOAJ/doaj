var licenceMap = {
    "CC BY" : ["/static/doaj/images/cc/by.png", "https://creativecommons.org/licenses/by/4.0/"],
    "CC BY-NC" : ["/static/doaj/images/cc/by-nc.png", "https://creativecommons.org/licenses/by-nc/4.0/"],
    "CC BY-NC-ND" : ["/static/doaj/images/cc/by-nc-nd.png", "https://creativecommons.org/licenses/by-nc-nd/4.0/"],
    "CC BY-NC-SA" : ["/static/doaj/images/cc/by-nc-sa.png", "https://creativecommons.org/licenses/by-nc-sa/4.0/"],
    "CC BY-ND" : ["/static/doaj/images/cc/by-nd.png", "https://creativecommons.org/licenses/by-nd/4.0/"],
    "CC BY-SA" : ["/static/doaj/images/cc/by-sa.png", "https://creativecommons.org/licenses/by-sa/4.0/"]
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

// called when a request to open or close the facet is received
// this should move the facet to the state dictated by facet.open
function setFacetOpenness(options, context, facet) {
    var el = context.find("#facetview_filter_" + safeId(facet.field));
    var open = facet["open"]
    if (open) {
        el.find(".facetview_filtershow").find("i").removeClass("icon-plus");
        el.find(".facetview_filtershow").find("i").addClass("icon-minus");
        el.find(".facetview_tooltip").show();
        el.find(".facetview_tooltip_value").hide();
        el.find(".facetview_filteroptions").show();
        el.find(".facetview_filtervalue").show();
        el.addClass("no-bottom");
    } else {
        el.find(".facetview_filtershow").find("i").removeClass("icon-minus");
        el.find(".facetview_filtershow").find("i").addClass("icon-plus");
        el.find(".facetview_tooltip").hide();
        el.find(".facetview_tooltip_value").hide();
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

// addition of embeddable widget into share link box
function searchOptions(options) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * class: facetview_startagain - reset the search parameters
     * class: facetview_pagesize - size of each result page
     * class: facetview_order - ordering direction of results
     * class: facetview_orderby - list of fields which can be ordered by
     * class: facetview_searchfield - list of fields which can be searched on
     * class: facetview_freetext - input field for freetext search
     * class: facetview_force_search - button which triggers a search on the current page status
     *
     * should (not must) respect the following configs
     *
     * options.search_sortby - list of sort fields and directions
     * options.searchbox_fieldselect - list of fields search can be focussed on
     * options.sharesave_link - whether to provide a copy of a link which can be saved
     * options.search_button - whether to provide a button to force a search
     */

    var thefacetview = "";

    // share and save link + embed link
    if (options.sharesave_link) {
        thefacetview += '<a class="btn facetview_sharesave" title="share or embed this search" style="margin:0 5px 21px 0px;" href="">share | embed</a>';
    }

    // initial button group of search controls
    thefacetview += '<div class="btn-group" style="display:inline-block; margin-right:5px;"> \
        <a class="btn btn-small facetview_startagain" title="clear all search settings and start again" href=""><i class="icon-remove"></i></a> \
        <a class="btn btn-small facetview_pagesize" title="change result set size" href="#"></a>';

    if (options.search_sortby.length > 0) {
        thefacetview += '<a class="btn btn-small facetview_order" title="current order descending. Click to change to ascending" \
            href="desc"><i class="icon-arrow-down"></i></a>';
    }
    thefacetview += '</div>';

    // selection for search ordering
    if (options.search_sortby.length > 0) {
        thefacetview += '<select class="facetview_orderby" style="border-radius:5px; \
            -moz-border-radius:5px; -webkit-border-radius:5px; width:100px; background:#eee; margin:0 5px 21px 0;"> \
            <option value="">order by ... relevance</option>';

        for (var each = 0; each < options.search_sortby.length; each++) {
            var obj = options.search_sortby[each];
            var sortoption = '';
            if ($.type(obj['field']) == 'array') {
                sortoption = sortoption + '[';
                sortoption = sortoption + "'" + obj['field'].join("','") + "'";
                sortoption = sortoption + ']';
            } else {
                sortoption = obj['field'];
            }
            thefacetview += '<option value="' + sortoption + '">' + obj['display'] + '</option>';
        };
        thefacetview += '</select>';
    }

    // select box for fields to search on
    if ( options.searchbox_fieldselect.length > 0 ) {
        thefacetview += '<select class="facetview_searchfield" style="border-radius:5px 0px 0px 5px; \
            -moz-border-radius:5px 0px 0px 5px; -webkit-border-radius:5px 0px 0px 5px; width:100px; margin:0 -2px 21px 0; background:#ecf4ff;">';
        thefacetview += '<option value="">search all</option>';

        for (var each = 0; each < options.searchbox_fieldselect.length; each++) {
            var obj = options.searchbox_fieldselect[each];
            thefacetview += '<option value="' + obj['field'] + '">' + obj['display'] + '</option>';
        };
        thefacetview += '</select>';
    };

    // text search box
    var corners = "border-radius:0px 5px 5px 0px; -moz-border-radius:0px 5px 5px 0px; -webkit-border-radius:0px 5px 5px 0px;"
    if (options.search_button) {
        corners = "border-radius:0px 0px 0px 0px; -moz-border-radius:0px 0px 0px 0px; -webkit-border-radius:0px 0px 0px 0px;"
    }
    thefacetview += '<input type="text" class="facetview_freetext span4" style="display:inline-block; margin:0 0 21px 0; background:#ecf4ff; ' + corners + '" name="q" \
        value="" placeholder="search term" />';

    // search button
    if (options.search_button) {
        thefacetview += "<a class='btn btn-info facetview_force_search' style='margin:0 0 21px 0px; border-radius:0px 5px 5px 0px; \
            -moz-border-radius:0px 5px 5px 0px; -webkit-border-radius:0px 5px 5px 0px;'><i class='icon-white icon-search'></i></a>"
    }

    // share and save link box
    if (options.sharesave_link) {
        thefacetview += '<div class="facetview_sharesavebox alert alert-info" style="display:none;"> \
            <button type="button" class="facetview_sharesave close">×</button> \
            <p>Share a link to this search';

        // if there is a url_shortener available, render a link
        if (options.url_shortener) {
            thefacetview += " <a href='#' class='facetview_shorten_url btn btn-mini' style='margin-left: 30px'><i class='icon-black icon-resize-small'></i> shorten url</a>";
            thefacetview += " <a href='#' class='facetview_lengthen_url btn btn-mini' style='display: none; margin-left: 30px'><i class='icon-black icon-resize-full'></i> original url</a>";
        }

        thefacetview += '</p> \
            <textarea class="facetview_sharesaveurl" style="width:100%">' + shareableUrl(options) + '</textarea>';

        // The text area for the embeddable widget
        thefacetview += '<p>Embed this search in your webpage</p>\
        <textarea class="facetview_embedwidget" style="width:100%">' + doajGenFixedQueryWidget(options) + '</textarea> \
            </div>';
    }

    return thefacetview
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

function doajToggleAbstract(options, context) {
    // toggle the abstracts
    $('.abstract_text', context).hide();
    $(".abstract_action", context).unbind("click").click(function(event) {
        event.preventDefault();
        var el = $(this);
        $('.abstract_text[rel="' + el.attr("rel") + '"]').slideToggle(300);
        return true;
    });
}

function doajPostRender(options, context) {
    doajScrollTop(options, context);
    doajToggleAbstract(options, context);

    // Update the widget options & generated text
    if (options.sharesave_link) {
        var widget_text = doajGenFixedQueryWidget(options);
        $('.facetview_embedwidget', context).val(widget_text);
    }
}

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

function doajRenderActiveTermsFilter(options, facet, field, filter_list) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * class: facetview_filterselected - anchor tag for any clickable filter selection
     * class: facetview_clear - anchor tag for any link which will remove the filter (should also provide data-value and data-field)
     * class: facetview_inactive_link - any link combined with facetview_filterselected which should not execute when clicked
     *
     * should (not must) respect the config
     *
     * options.show_filter_field - whether to include the name of the field the filter is active on
     * options.show_filter_logic - whether to include AND/OR along with filters
     * facet.value_function - the value function to be applied to all displayed values
     */

    // DOAJ note: we are overriding this (99.9% the same as facetview2's bootstrap2 theme)
    // because we need to change the class of the cross icon used to close active filters.
    // We use FontAwesome at the DOAJ because the colours are overridable unlike Bootstrap's glyphicons.

    var clean = safeId(field);
    var display = facet.display ? facet.display : facet.field;
    var logic = facet.logic ? facet.logic : options.default_facet_operator;

    var frag = "<div id='facetview_filter_group_" + clean + "' class='btn-group'>";

    if (options.show_filter_field) {
        frag += '<span class="facetview_filterselected_text"><strong>' + display + ':</strong>&nbsp;</span>';
    }

    for (var i = 0; i < filter_list.length; i++) {
        var value = filter_list[i];
        if (facet.value_function) {
            value = facet.value_function(value)
        }

        frag += '<span class="facetview_filterselected_text">' + value + '</span>&nbsp;';
        frag += '<a class="facetview_filterselected facetview_clear" data-field="' + field + '" data-value="' + value + '" alt="remove" title="Remove" href="' + value + '">';
        frag += '<i class="fa fa-remove" style="margin-top:1px;"></i>';
        frag += "</a>";

        if (i !== filter_list.length - 1 && options.show_filter_logic) {
            frag += '<span class="facetview_filterselected_text">&nbsp;<strong>' + logic + '</strong>&nbsp;</span>';
        }
    }
    frag += "</div>";

    return frag
}

function doajRenderActiveDateHistogramFilter(options, facet, field, value) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * class: facetview_filterselected - anchor tag for any clickable filter selection
     * class: facetview_clear - anchor tag for any link which will remove the filter (should also provide data-value and data-field)
     * class: facetview_inactive_link - any link combined with facetview_filterselected which should not execute when clicked
     *
     * should (not must) respect the config
     *
     * options.show_filter_field - whether to include the name of the field the filter is active on
     */

    // DOAJ note: we are overriding this (99.9% the same as facetview2's bootstrap2 theme)
    // because we need to change the class of the cross icon used to close active filters.
    // We use FontAwesome at the DOAJ because the colours are overridable unlike Bootstrap's glyphicons.

    var clean = safeId(field);
    var display = facet.display ? facet.display : facet.field;

    var frag = "<div id='facetview_filter_group_" + clean + "' class='btn-group'>";

    if (options.show_filter_field) {
        frag += '<span class="facetview_filterselected_text"><strong>' + display + ':</strong>&nbsp;</span>';
    }

    var data_from = value.from ? " data-from='" + value.from + "' " : "";

    var valdisp = value.from;
    if (facet.value_function) {
        valdisp = facet.value_function(valdisp);
    }

    frag += '<span class="facetview_filterselected_text">' + valdisp + '</span>&nbsp;';
    frag += '<a class="facetview_filterselected facetview_clear" data-field="' + field + '" ' + data_from +
            ' alt="remove" title="Remove" href="#">';
    frag += '<i class="fa fa-remove" style="margin-top:1px;"></i>';
    frag += "</a>";

    frag += "</div>";

    return frag
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
