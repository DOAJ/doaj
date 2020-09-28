/** base namespace for all DOAJ-specific functions */
var doaj = {
    init : function() {
        // Use Feather icons
        feather.replace();

        // Responsive menu
        var openMenu = document.querySelector(".secondary-nav__menu-toggle");
        var nav = document.querySelector(".secondary-nav__menu");

        openMenu.addEventListener('click', function() {
            nav.classList.toggle("secondary-nav__menu-toggle--active");
        }, false);

        // Back-to-top button
        var topBtn = document.getElementById("top");

        window.onscroll = function() {scrollFunction()};

        function scrollFunction() {
            if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
                if (topBtn) {
                    topBtn.style.display = "flex";
                }
            } else {
                if (topBtn) {
                    topBtn.style.display = "none";
                }

            }
        }

        // When the user clicks on the button, scroll to the top of the document
        function topFunction() {
            document.body.scrollTop = 0; // For Safari
            document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
        }

        // Offset when clicking on anchor link or sidenav link to compensate for fixed header
        var headerHeight = 70;

        // When on the same page
        jQuery (function($) {
            // Tabs
            $("[role='tab']").click(function(e) {
                e.preventDefault();
                $(this).attr("aria-selected", "true");
                $(this).parent().siblings().children().attr("aria-selected", "false");
                var tabpanelShow = $(this).attr("href");
                $(tabpanelShow).attr("aria-hidden", "false");
                $(tabpanelShow).siblings().attr("aria-hidden", "true");
            });

            $('a[href*="#"]:not([href="#"])').click(function() {
                var target = $(this.hash);
                $('html,body').animate({
                    scrollTop: target.offset().top - headerHeight
                }, 50, 'linear');
            });
            if (location.hash){
                var id = $(location.hash);
            }

            $(window).on('load', function() {
                if (location.hash){
                    let offset = id.offset();
                    if (offset) {
                        $('html,body').animate({
                            scrollTop: offset.top - headerHeight
                        }, 50, 'linear')
                    }
                }
            });
        });

        // Coming from another page
        jQuery (document).ready (function($) {
            var hash= window.location.hash;
            if ( hash === '' || hash === '#' || hash === undefined ) return false;
            var target = $(hash);
            target = target.length ? target : $('[name=' + hash.slice(1) +']');
            if (target.length) {
                $('html,body').animate({
                    scrollTop: target.offset().top - headerHeight //offsets for fixed header
                }, 50, 'linear');
            }
        } );

        jQuery(document).ready(function($) {
            $(".flash_close").on("click", function(event) {
                event.preventDefault();
                var container = $(this).parents(".flash_container");
                container.remove();
            })
        });
    },

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