/** base namespace for all DOAJ-specific functions */
var doaj = {
    bitlyShortener : function(query, success_callback, error_callback) {

        function callbackWrapper(data) {
            success_callback(data.url);
        }

        function errorHandler() {
            alert("Sorry, we're unable to generate short urls at this time");
            error_callback();
        }

        var page = window.location.protocol + '//' + window.location.host + window.location.pathname;

        $.ajax({
            type: "POST",
            contentType: "application/json",
            dataType: "jsonp",
            url: "/service/shorten",
            data : JSON.stringify({page: page, query: query}),
            success: callbackWrapper,
            error: errorHandler
        });
    },

    journal_toc_id : function(journal) {
        // if e-issn is available, use that
        // if not, but a p-issn is available, use that
        // if neither ISSN is available, use the internal ID
        var ids = journal.bibjson.identifier;
        var pissns = [];
        var eissns = [];
        if (ids) {
            for (var i = 0; i < ids.length; i++) {
                if (ids[i].type === "pissn") {
                    pissns.push(ids[i].id)
                } else if (ids[i].type === "eissn") {
                    eissns.push(ids[i].id)
                }
            }
        }

        var toc_id = undefined;
        if (eissns.length > 0) { toc_id = eissns[0]; }
        if (!toc_id && pissns.length > 0) { toc_id = pissns[0]; }
        if (!toc_id) { toc_id = journal.id; }

        return toc_id;
    },

    monthmap : [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"
    ],

    licenceMap : {
        "CC BY" : ["/static/doaj/images/cc/by.png", "https://creativecommons.org/licenses/by/4.0/"],
        "CC BY-NC" : ["/static/doaj/images/cc/by-nc.png", "https://creativecommons.org/licenses/by-nc/4.0/"],
        "CC BY-NC-ND" : ["/static/doaj/images/cc/by-nc-nd.png", "https://creativecommons.org/licenses/by-nc-nd/4.0/"],
        "CC BY-NC-SA" : ["/static/doaj/images/cc/by-nc-sa.png", "https://creativecommons.org/licenses/by-nc-sa/4.0/"],
        "CC BY-ND" : ["/static/doaj/images/cc/by-nd.png", "https://creativecommons.org/licenses/by-nd/4.0/"],
        "CC BY-SA" : ["/static/doaj/images/cc/by-sa.png", "https://creativecommons.org/licenses/by-sa/4.0/"]
    },

    humanYearMonth : function(datestr) {
        var date = new Date(datestr);
        var monthnum = date.getUTCMonth();
        var year = date.getUTCFullYear();

        return doaj.monthmap[monthnum] + " " + String(year);
    },

    humanDate : function(datestr) {
        var date = new Date(datestr);
        var dom = date.getUTCDate();
        var monthnum = date.getUTCMonth();
        var year = date.getUTCFullYear();

        return String(dom) + " " + doaj.monthmap[monthnum] + " " + String(year);
    },

    humanDateTime : function(datestr) {
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

        return String(dom) + " " + doaj.monthmap[monthnum] + " " + String(year) + " at " + String(hour) + ":" + String(minute);
    },

    iso_datetime2date : function(isodate_str) {
        /* >>> '2003-04-03T00:00:00Z'.substring(0,10)
         * "2003-04-03"
         */
        return isodate_str.substring(0,10);
    },

    iso_datetime2date_and_time : function(isodate_str) {
        /* >>> "2013-12-13T22:35:42Z".replace('T',' ').replace('Z','')
         * "2013-12-13 22:35:42"
         */
        if (!isodate_str) { return "" }
        return isodate_str.replace('T',' ').replace('Z','')
    }
};

jQuery(document).ready(function() {
    $.noop(); // just a placeholder, delete when adding code here
});


function setCookieConsent(event) {
    event.preventDefault();
    $.ajax({
        type: "GET",
        url: "/cookie_consent",
        success: function() {
            $("#cookie-consent").remove();
        },
        error : function() {
            alert("We weren't able to set your cookie consent preferences, please try again later.");
        }
    })
}

function dissmissSiteNote(event) {
    event.preventDefault();
    $.ajax({
        type: "GET",
        url: "/dismiss_site_note",
        success: function() {
            $("#site-note").remove();
        },
        error : function() {
            alert("Something went wrong, we weren't able to dismiss this note. Please try again later.");
        }
    })
}