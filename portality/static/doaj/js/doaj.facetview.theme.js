var licenceMap = {
    "CC BY" : ["/static/doaj/images/cc/by.png", "http://creativecommons.org/licenses/by/3.0/"],
    "CC BY-NC" : ["/static/doaj/images/cc/by-nc.png", "http://creativecommons.org/licenses/by-nc/3.0/"],
    "CC BY-NC-ND" : ["/static/doaj/images/cc/by-nc-nd.png", "http://creativecommons.org/licenses/by-nc-nd/3.0/"],
    "CC BY-NC-SA" : ["/static/doaj/images/cc/by-nc-sa.png", "http://creativecommons.org/licenses/by-nc-sa/3.0/"],
    "CC BY-ND" : ["/static/doaj/images/cc/by-nd.png", "http://creativecommons.org/licenses/by-nd/3.0/"],
    "CC BY-SA" : ["/static/doaj/images/cc/by-sa.png", "http://creativecommons.org/licenses/by-sa/3.0/"]
}


/////////////////////////////////////////////////////
// result render functions
////////////////////////////////////////////////////

function publicSearchResult(options, resultobj) {
    if (resultobj.bibjson && resultobj.bibjson.journal) {
        // it is an article
        return renderPublicArticle(options, resultobj);
    } else {
        // it is a journal
        return renderPublicJournal(options, resultobj);
    }
}

function renderPublicJournal(options, resultobj) {
    // start off the string to be rendered
    var result = options.resultwrap_start;
    result += "<div class='row-fluid'>";

    // add the journal icon
    result += "<div class='span1'>";
    result += "<i style='font-size: 24px' class='icon icon-book'></i>";
    result += "</div>";

    // start the main box that all the details go in
    result += "<div class='span9'>";

    // set the title
    if (resultobj.bibjson.title) {
        result += "<span class='title'><a href='/toc/" + resultobj.id + "'>" + resultobj.bibjson.title + "</a></span><br>";
    }

    // set the alternative title
    if (resultobj.bibjson.alternative_title) {
        result += "<span class='alternative_title' style='color: #aaaaaa'>" + resultobj.bibjson.alternative_title + "</span><br>";
    }

    // set the issn
    if (resultobj.bibjson && resultobj.bibjson.identifier) {
        var ids = resultobj.bibjson.identifier;
        var issns = [];
        for (var i = 0; i < ids.length; i++) {
            if (ids[i].type === "pissn" || ids[i].type === "eissn") {
                issns.push(ids[i].id)
            }
        }
        if (issns.length > 0) {
            result += "ISSN: " + issns.join(", ") + "<br>"
        }
    }

    // set the homepage url
    if (resultobj.bibjson && resultobj.bibjson.link) {
        var ls = resultobj.bibjson.link;
        for (var i = 0; i < ls.length; i++) {
            var t = ls[i].type;
            if (t == 'homepage') {
                result += "<a href='" + ls[i].url + "'>" + ls[i].url + "</a><br>";
            }
        }
    }

    // add the subjects
    if (resultobj.index && resultobj.index.subject && resultobj.index.subject.length > 0) {
        result += "<strong>Subjects:</strong><br>";
        result += resultobj.index.subject.join(", ");
    }

    // close the main details box
    result += "</div>";

    // start the journal properties side-bar
    result += "<div class='span2'>";

    // set the tick if it is relevant
    if (resultobj.admin && resultobj.admin.ticked) {
        result += "<img src='/static/doaj/images/tick_long.png' title='Accepted after March 2014' alt='Tick icon: journal was accepted after March 2014' style='padding-bottom: 3px'>​​<br>";
    }

    // licence
    if (resultobj.bibjson.license) {
        var ltitle = undefined;
        var lics = resultobj.bibjson.license;
        if (lics.length > 0) {
            ltitle = lics[0].title
        }
        if (ltitle) {
            if (licenceMap[ltitle]) {
                var urls = licenceMap[ltitle];
                result += "<a href='" + urls[1] + "' title='" + ltitle + "' target='_blank'><img src='" + urls[0] + "' width='80' height='15' valign='middle' alt='" + ltitle + "'></a><br>"
            } else {
                result += "<strong>License: " + ltitle + "</strong>"
            }
        }
    }

    // peer review type
    if (resultobj.bibjson.editorial_review && resultobj.bibjson.editorial_review.process) {
        var proc = resultobj.bibjson.editorial_review.process;
        if (proc === "None") {
            proc = "No peer review"
        }
        result += "<strong>" + proc + "</strong><br>"
    }

    // APC
    if (resultobj.bibjson.apc) {
        if (resultobj.bibjson.apc.currency || resultobj.bibjson.apc.average_price) {
            result += "<strong>APC: ";
            if (resultobj.bibjson.apc.average_price) {
                result += resultobj.bibjson.apc.average_price;
            } else {
                result += "price unknown ";
            }
            if (resultobj.bibjson.apc.currency) {
                result += resultobj.bibjson.apc.currency
            } else {
                result += " currency unknown";
            }
            result += "</strong>";
        } else {
            result += "<strong>No APC</strong>";
        }
    }

    // close the journal properties side-bar
    result += "</div>";

    // close off the result with the ending strings, and then return
    result += "</div>";
    result += options.resultwrap_end;
    return result;
}

function renderPublicArticle(options, resultobj) {

    function makeCitation(record) {
        // get all the relevant citation properties
        var ctitle = record.bibjson.journal ? record.bibjson.journal.title : undefined;
        var cvol = record.bibjson.journal ? record.bibjson.journal.volume : undefined;
        var ciss = record.bibjson.journal ? record.bibjson.journal.number: undefined;
        var cstart = record.bibjson.start_page;
        var cend = record.bibjson.end_page;
        var cyear = record.bibjson.year;

        // we're also going to need the issn
        var issns = [];
        if (resultobj.bibjson && resultobj.bibjson.identifier) {
            var ids = resultobj.bibjson.identifier;
            for (var i = 0; i < ids.length; i++) {
                if (ids[i].type === "pissn" || ids[i].type === "eissn") {
                    issns.push(ids[i].id)
                }
            }
        }

        var citation = "";
        if (ctitle) {
            if (issns.length > 0) {
                citation += "<a href='/toc/" + issns[0] + "'>" + ctitle + "</a>";
            } else {
                citation += ctitle;
            }
        }

        if (cvol) {
            if (citation !== "") { citation += ", " }
            citation += "Vol " + cvol;
        }

        if (ciss) {
            if (citation !== "") { citation += ", " }
            citation += "Iss " + ciss;
        }

        if (cstart || cend) {
            if (citation !== "") { citation += ", " }
            if ((cstart && !cend) || (!cstart && cend)) {
                citation += "p ";
            } else {
                citation += "Pp ";
            }
            if (cstart) {
                citation += cstart;
            }
            if (cend) {
                if (cstart) {
                    citation += "-"
                }
                citation += cend;
            }
        }

        if (cyear) {
            if (citation !== "") { citation += " " }
            citation += "(" + cyear + ")";
        }

        return citation;
    }

    // start off the string to be rendered
    var result = options.resultwrap_start;
    result += "<div class='row-fluid'>";

    // add the journal icon
    result += "<div class='span1'>";
    result += "<i style='font-size: 24px' class='icon icon-file'></i>";
    result += "</div>";

    // start the main box that all the details go in
    result += "<div class='span9'>";

    // set the title
    if (resultobj.bibjson.title) {
        result += "<span class='title'><a href='/article/" + resultobj.id + "'>" + resultobj.bibjson.title + "</a></span><br>";
    }

    // set the doi
    if (resultobj.bibjson && resultobj.bibjson.identifier) {
        var ids = resultobj.bibjson.identifier;
        for (var i = 0; i < ids.length; i++) {
            if (ids[i].type === "doi") {
                var doi = ids[i].id;
                var tendot = doi.indexOf("10.");
                var url = "http://dx.doi.org/" + doi.substring(tendot);
                result += "DOI: <a href='" + url + "'>" + doi.substring(tendot) + "</a><br>";
            }
        }
    }

    // set the citation
    var cite = makeCitation(resultobj);
    if (cite) {
        result += cite + "<br>";
    }

    // set the fulltext
    if (resultobj.bibjson && resultobj.bibjson.link) {
        var ls = resultobj.bibjson.link;
        for (var i = 0; i < ls.length; i++) {
            var t = ls[i].type;
            if (t == 'fulltext') {
                result += "Fulltext: <a href='" + ls[i].url + "'>" + ls[i].url + "</a><br>";
            }
        }
    }

    // close the main details box
    result += "</div>";

    // start the journal properties side-bar
    result += "<div class='span2'>";

    // set the tick if it is relevant
    if (resultobj.admin && resultobj.admin.ticked) {
        result += "<img src='/static/doaj/images/tick_long.png' title='Accepted after March 2014' alt='Tick icon: journal was accepted after March 2014' style='padding-bottom: 3px'>​​<br>";
    }

    // licence
    if (resultobj.bibjson.journal && resultobj.bibjson.journal.license) {
        var ltitle = undefined;
        var lics = resultobj.bibjson.journal.license;
        if (lics.length > 0) {
            ltitle = lics[0].title
        }
        if (ltitle) {
            if (licenceMap[ltitle]) {
                var urls = licenceMap[ltitle];
                result += "<a href='" + urls[1] + "' title='" + ltitle + "' target='_blank'><img src='" + urls[0] + "' width='80' height='15' valign='middle' alt='" + ltitle + "'></a><br>"
            } else {
                result += "<strong>License: " + ltitle + "</strong>"
            }
        }
    }

    // close the article properties side-bar
    result += "</div>";

    // close off the main result
    result += "</div>";

    // create the abstract section if desired
    if (resultobj.bibjson.abstract) {
        // start the abstract section
        result += "<div class='row-fluid'><div class='span1'>&nbsp;</div><div class='span11'>";

        result += "<strong>Abstract</strong>&nbsp;&nbsp;";
        result += '<a class="abstract_action" href="" rel="' + resultobj.id + '">(expand)</a><br>';
        result += '<div class="abstract_text" rel="' + resultobj.id + '">' + resultobj.bibjson.abstract + '</div>';

        // close off the abstract section
        result += "</div></div>";
    }

    // close off the result and return
    result += options.resultwrap_end;
    return result;
}

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

function doajPostRender(options, context) {
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
    })
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