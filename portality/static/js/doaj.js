/** base namespace for all DOAJ-specific functions */
// ~~ DOAJ:Library ~~
var doaj = {
    scrollPosition: 100,
    init : function() {
        // Use Feather icons
        feather.replace();

        // Responsive menu
        var openMenu = document.querySelector(".secondary-nav__menu-toggle");
        var nav = document.querySelector(".secondary-nav__menu");

        if (openMenu) {
            openMenu.addEventListener('click', function () {
                nav.classList.toggle("secondary-nav__menu-toggle--active");
            }, false);
        }

        // On scroll, display back-to-top button & add class to header primary menu
        var topBtn = document.getElementById("top"),
            topNav = document.querySelector(".primary-nav");

        function displayOnScroll() {
            if (topBtn && topNav) {
                if (document.body.scrollTop > doaj.scrollPosition || document.documentElement.scrollTop > doaj.scrollPosition) {
                    topBtn.style.display = "flex";
                    topNav.classList.add("primary-nav--scrolled");
                } else {
                    topBtn.style.display = "none";
                    topNav.classList.remove("primary-nav--scrolled");
                }
            }
        }

        window.addEventListener("scroll", function() {
          displayOnScroll();
        });

        // Tabs
        jQuery (function($) {
            $("[role='tab']").click(function(e) {
                e.preventDefault();
                let el = $(this);

                el.attr("aria-selected", "true");
                el.siblings().children().attr("aria-selected", "false");

                let tabpanelShow = el.attr("href");
                if (!tabpanelShow) {
                    let innerLink = el.find("a");
                    innerLink.attr("aria-selected", "true");
                    tabpanelShow = innerLink.attr("href")
                }

                $(tabpanelShow).attr("aria-hidden", "false");
                $(tabpanelShow).siblings().attr("aria-hidden", "true");
            });
        });

        // Close flash notifications
        jQuery(document).ready(function($) {
            $(".flash_close").on("click", function(event) {
                event.preventDefault();
                var container = $(this).parents(".flash_container");
                container.remove();
            });
        });

        doaj.bindMiniSearch();
    },

    bitlyShortener : function(query, success_callback, error_callback) {
        // ~~-> Bitly:ExternalService ~~
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

    bindMiniSearch : function() {
        const namespace = "doaj-minisearch";
        const container = "." + namespace + "--container";
        $(container + " [name=content-type]").on("change", function() {
            let that = $(this);
            if (!that.is(":checked")) {
                return;
            }
            let fields = that.parents(container).find("[name=fields]");
            if (that.val() === "journals") {
                fields.html(`
                    <option value="all">In all fields</option>
                    <option value="title">Title</option>
                    <option value="issn">ISSN</option>
                    <option value="subject">Subject</option>
                    <option value="publisher">Publisher</option>
                `)
            } else {
                fields.html(`
                    <option value="all">In all fields</option>
                    <option value="title">Title</option>
                    <option value="abstract">Abstract</option>
                    <option value="subject">Subject</option>
                    <option value="author">Author</option>
                `)
            }
        });
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

        if (isNaN(monthnum) || isNaN(year)) {
            return "";
        }

        return doaj.monthmap[monthnum] + " " + String(year);
    },

    humanDate : function(datestr) {
        var date = new Date(datestr);
        var dom = date.getUTCDate();
        var monthnum = date.getUTCMonth();
        var year = date.getUTCFullYear();

        if (isNaN(monthnum) || isNaN(year) || isNaN(dom)) {
            return "";
        }

        return String(dom) + " " + doaj.monthmap[monthnum] + " " + String(year);
    },

    humanDateTime : function(datestr) {
        var date = new Date(datestr);
        var dom = date.getUTCDate();
        var monthnum = date.getUTCMonth();
        var year = date.getUTCFullYear();
        var hour = date.getUTCHours();
        var minute = date.getUTCMinutes();

        if (isNaN(monthnum) || isNaN(year) || isNaN(dom) || isNaN(hour) || isNaN(minute)) {
            return "";
        }

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
    },

    scroller : function(selector, notFirstTime, duration, callback) {
        if (!duration) {
            duration = 1
        }
        if (notFirstTime === undefined) {
            notFirstTime = true;
        }

        if (doaj.scroller.hasOwnProperty("doScroll")) {
            $("html, body").animate(
                {
                    scrollTop: $(selector).offset().top
                },
                {
                    duration: duration,
                    always: callback
                }
            );
        } else {
            doaj.scroller.doScroll = true;
        }
    },

    searchQuerySource : function (params) {
        // ~~-> Edges:Technology ~~
        // ~~-> Elasticsearch:Technology ~~
        // ~~-> Edges:Query ~~
        let terms = params.terms;
        let term = params.term;
        let queryString = params.queryString;
        let sort = params.sort;

        let musts = [];
        if (terms) {
            for (let term of terms) {
                musts.push({"terms" : term})
            }
        }

        if (term) {
            for (let t of term) {
                musts.push({"term" : t});
            }
        }

        if (queryString) {
            musts.push({
                "query_string" : {
                    "default_operator" : "AND",
                    "query" : queryString
                }
            })
        }

        let query = {"match_all": {}}
        if (musts.length > 0) {
            query = {
                "bool" : {
                    "must" : musts
                }
            }
        }

        let obj = {"query": query}
        if (sort) {
            if (Array.isArray(sort)) {
                obj["sort"] = sort;
            } else {
                obj["sort"] = [sort];
            }
        }

        let source = JSON.stringify(obj)
        return encodeURIComponent(source)
    }
};


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
