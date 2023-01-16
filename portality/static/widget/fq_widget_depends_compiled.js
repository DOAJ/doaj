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

        // Display back-to-top button on scroll
        var topBtn = document.getElementById("top");

        function displayTopBtn() {
            if (topBtn) {
                if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
                    topBtn.style.display = "flex";
                } else {
                    topBtn.style.display = "none";
                }
            }
        }

        // Hide header menu on down scroll; display on scroll up
        var prevScrollPos = window.pageYOffset,
            topNav = document.querySelector(".primary-nav");

        function hideNav() {
            var currentScrollPos = window.pageYOffset;

            if (prevScrollPos > currentScrollPos) {
                topNav.classList.remove("primary-nav--scrolled");
            } else {
                topNav.classList.add("primary-nav--scrolled");
            }
            prevScrollPos = currentScrollPos;
        }

        window.onscroll = function() {
            displayTopBtn();
            hideNav();
        };

        // Tabs
        jQuery (function($) {
            $("[role='tab']").click(function(e) {
                e.preventDefault();
                $(this).attr("aria-selected", "true");
                $(this).parent().siblings().children().attr("aria-selected", "false");
                var tabpanelShow = $(this).attr("href");
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

$.extend(true, doaj, {
    publicSearchConfig : {
        publicSearchPath : '/query/journal,article/_search?ref=fqw',
        lccTree: '{{ lcc_tree|tojson }}'
    }
});
/** @namespace */
var es = {

    /////////////////////////////////////////////////////
    // fixed properties, like special characters, etc

    // The reserved characters in elasticsearch query strings
    // Note that the "\" has to go first, as when these are substituted, that character
    // will get introduced as an escape character
    specialChars : ["\\", "+", "-", "=", "&&", "||", ">", "<", "!", "(", ")", "{", "}", "[", "]", "^", '"', "~", "*", "?", ":", "/"],

    // FIXME: specialChars is not currently used for encoding, but it would be worthwhile giving the option
    // to allow/disallow specific values, but that requires a much better (automated) understanding of the
    // query DSL

    // the reserved special character set with * and " removed, so that users can do quote searches and wildcards
    // if they want
    specialCharsSubSet : ["\\", "+", "-", "=", "&&", "||", ">", "<", "!", "(", ")", "{", "}", "[", "]", "^", "~", "?", ":", "/"],

    // values that have to be in even numbers in the query or they will be escaped
    characterPairs : ['"'],

    // distance units allowed by ES
    distanceUnits : ["km", "mi", "miles", "in", "inch", "yd", "yards", "kilometers", "mm", "millimeters", "cm", "centimeters", "m", "meters"],

    // request method to be used throughout.  Set this before using the module if you want it different
    requestMethod : "get",

    ////////////////////////////////////////////////////

    ////////////////////////////////////////////////////
    // object factories

    aggregationFactory : function(type, params) {
        var constructors = {
            terms: es.newTermsAggregation,
            range: es.newRangeAggregation,
            geo_distance: es.newGeoDistanceAggregation,
            date_histogram: es.newDateHistogramAggregation,
            stats: es.newStatsAggregation,
            cardinality: es.newCardinalityAggregation
        };

        if (constructors[type]) {
            return constructors[type](params);
        }

    },

    filterFactory : function(type, params) {
        var constructors = {
            query_string: es.newQueryString,
            term: es.newTermFilter,
            terms: es.newTermsFilter,
            range: es.newRangeFilter,
            geo_distance_range: es.newGeoDistanceRangeFilter
        };

        if (constructors[type]) {
            return constructors[type](params);
        }
    },

    ////////////////////////////////////////////////////
    /** @namespace */
    /** Query objects for standard query structure */
    /**
     *
     * @param filtered {Boolean} Is this an ES filtered query?
     * @param size=10 {Number} What amount of results are required. ES defaults to 10.
     * @param from {Number} Beginning point for results.
     * @param fields {String[]} Required fields.
     * @param aggs {String[]} ES aggregations.
     * @param must {String[]} ES must query.
     * @param source {String} ES source.
     * @param should {String[]} ES should.
     * @param mustNot {String[]} ES must not.
     * @param partialFields ???
     * @param scriptFields ???
     * @param minimumShouldMatch ???
     * @param facets {String[]} for older versions of ES
     */

    newQuery : function(params) {
        if (!params) { params = {} }
        return new es.Query(params);
    },
    /** @class */
    Query : function(params) {
        // properties that can be set directly (thought note that they may need to be read via their getters)
        this.filtered = false;  // this is no longer present in es5.x
        this.size = params.size !== undefined ? params.size : false;
        this.from = params.from || false;
        this.fields = params.fields || [];
        this.aggs = params.aggs || [];
        this.must = params.must || [];
        this.mustNot = params.mustNot || [];
        this.trackTotalHits = true;   // FIXME: hard code this for the moment, we can introduce the ability to vary it later

        // defaults from properties that will be set through their setters (see the bottom
        // of the function)
        this.queryString = false;
        this.sort = [];

        // ones that we haven't used yet, so are awaiting implementation
        // NOTE: once we implement these, they also need to be considered in merge()
        this.source = params.source || false;
        this.should = params.should || [];
        this.partialFields = params.partialFields || false;
        this.scriptFields = params.scriptFields || false;
        this.minimumShouldMatch = params.minimumShouldMatch || false;
        this.partialFields = params.partialFields || false;
        this.scriptFields = params.scriptFields || false;

        // for old versions of ES, so are not necessarily going to be implemented
        this.facets = params.facets || [];

        this.getSize = function() {
            if (this.size !== undefined && this.size !== false) {
                return this.size;
            }
            return 10;
        };
        this.getFrom = function() {
            if (this.from) {
                return this.from
            }
            return 0;
        };
        this.addField = function(field) {
            if ($.inArray(field, this.fields) === -1) {
                this.fields.push(field);
            }
        };

        this.setQueryString = function(params) {
            var qs = params;
            if (!(params instanceof es.QueryString)) {
                if ($.isPlainObject(params)) {
                    qs = es.newQueryString(params);
                } else {
                    qs = es.newQueryString({queryString: params});
                }
            }
            this.queryString = qs;
        };
        this.getQueryString = function() {
            return this.queryString;
        };
        this.removeQueryString = function() {
            this.queryString = false;
        };

        this.setSortBy = function(params) {
            // overwrite anything that was there before
            this.sort = [];
            // ensure we have a list of sort options
            var sorts = params;
            if (!$.isArray(params)) {
                sorts = [params]
            }
            // add each one
            for (var i = 0; i < sorts.length; i++) {
                this.addSortBy(sorts[i]);
            }
        };
        this.addSortBy = function(params) {
            // ensure we have an instance of es.Sort
            var sort = params;
            if (!(params instanceof es.Sort)) {
                sort = es.newSort(params);
            }
            // prevent repeated sort options being added
            for (var i = 0; i < this.sort.length; i++) {
                var so = this.sort[i];
                if (so.field === sort.field) {
                    return;
                }
            }
            // add the sort option
            this.sort.push(sort);
        };
        this.prependSortBy = function(params) {
            // ensure we have an instance of es.Sort
            var sort = params;
            if (!(params instanceof es.Sort)) {
                sort = es.newSort(params);
            }
            this.removeSortBy(sort);
            this.sort.unshift(sort);
        };
        this.removeSortBy = function(params) {
            // ensure we have an instance of es.Sort
            var sort = params;
            if (!(params instanceof es.Sort)) {
                sort = es.newSort(params);
            }
            var removes = [];
            for (var i = 0; i < this.sort.length; i++) {
                var so = this.sort[i];
                if (so.field === sort.field) {
                    removes.push(i);
                }
            }
            removes = removes.sort().reverse();
            for (var i = 0; i < removes.length; i++) {
                this.sort.splice(removes[i], 1);
            }
        };
        this.getSortBy = function() {
            return this.sort;
        };

        this.setSourceFilters = function(params) {
            if (!this.source) {
                this.source = {include: [], exclude: []};
            }
            if (params.include) {
                this.source.include = params.include;
            }
            if (params.exclude) {
                this.source.exclude = params.exclude;
            }
        };

        this.addSourceFilters = function(params) {
            if (!this.source) {
                this.source = {include: [], exclude: []};
            }
            if (params.include) {
                if (this.source.include) {
                    Array.prototype.push.apply(this.source.include, params.include);
                } else {
                    this.source.include = params.include;
                }
            }
            if (params.exclude) {
                if (this.source.include) {
                    Array.prototype.push.apply(this.source.include, params.include);
                } else {
                    this.source.include = params.include;
                }
            }
        };

        this.getSourceIncludes = function() {
            if (!this.source) {
                return [];
            }
            return this.source.include;
        };

        this.getSourceExcludes = function() {
            if (!this.source) {
                return [];
            }
            return this.source.exclude;
        };

        this.addFacet = function() {};
        this.removeFacet = function() {};
        this.clearFacets = function() {};

        this.getAggregation = function(params) {
            var name = params.name;
            for (var i = 0; i < this.aggs.length; i++) {
                var a = this.aggs[i];
                if (a.name === name) {
                    return a;
                }
            }
        };
        this.addAggregation = function(agg, overwrite) {
            if (overwrite) {
                this.removeAggregation(agg.name);
            } else {
                for (var i = 0; i < this.aggs.length; i++) {
                    if (this.aggs[i].name === agg.name) {
                        return;
                    }
                }
            }
            this.aggs.push(agg);
        };
        this.removeAggregation = function(name) {
            var removes = [];
            for (var i = 0; i < this.aggs.length; i++) {
                if (this.aggs[i].name === name) {
                    removes.push(i);
                }
            }
            removes = removes.sort().reverse();
            for (var i = 0; i < removes.length; i++) {
                this.aggs.splice(removes[i], 1);
            }
        };
        this.clearAggregations = function() {
            this.aggs = [];
        };
        this.listAggregations = function() {
            return this.aggs;
        };

        this.addMust = function(filter) {
            var existing = this.listMust(filter);
            if (existing.length === 0) {
                this.must.push(filter);
            }
        };
        this.listMust = function(template) {
            return this.listFilters({boolType: "must", template: template});
        };
        this.removeMust = function(template) {
            var removes = [];
            for (var i = 0; i < this.must.length; i++) {
                var m = this.must[i];
                if (m.matches(template)) {
                    removes.push(i);
                }
            }
            removes = removes.sort().reverse();
            for (var i = 0; i < removes.length; i++) {
                this.must.splice(removes[i], 1);
            }
            // return the count of filters that were removed
            return removes.length;
        };
        this.clearMust = function() {
            this.must = [];
        };

        this.addMustNot = function(filter) {
            var existing = this.listMustNot(filter);
            if (existing.length === 0) {
                this.mustNot.push(filter);
            }
        };
        this.listMustNot = function(template) {
            return this.listFilters({boolType: "must_not", template: template});
        };
        this.removeMustNot = function(template) {
            var removes = [];
            for (var i = 0; i < this.mustNot.length; i++) {
                var m = this.mustNot[i];
                if (m.matches(template)) {
                    removes.push(i);
                }
            }
            removes = removes.sort().reverse();
            for (var i = 0; i < removes.length; i++) {
                this.mustNot.splice(removes[i], 1);
            }
            // return the count of filters that were removed
            return removes.length;
        };
        this.clearMustNot = function() {
            this.mustNot = [];
        };

        this.addShould = function() {};
        this.listShould = function() {};
        this.removeShould = function() {};
        this.clearShould = function() {};



        /////////////////////////////////////////////////
        // interrogative functions

        this.hasFilters = function() {
            return this.must.length > 0 || this.should.length > 0 || this.mustNot.length > 0
        };

        // in general better to use the listMust, listShould, listMustNot, directly.
        // those methods each use this method internally anyway
        this.listFilters = function(params) {
            var boolType = params.boolType || "must";
            var template = params.template || false;

            //var field = params.field || false;
            //var filterType = params.filterType || false;

            // first get the boolean filter field that we're going to look in
            var bool = [];
            if (boolType === "must") {
                bool = this.must;
            } else if (boolType === "should") {
                bool = this.should;
            } else if (boolType === "must_not") {
                bool = this.mustNot;
            }

            if (!template) {
                return bool;
            }
            var l = [];
            for (var i = 0; i < bool.length; i++) {
                var m = bool[i];
                if (m.matches(template)) {
                    l.push(m);
                }
            }
            return l;
        };

        ////////////////////////////////////////////////
        // create, parse, serialise functions

        this.merge = function(source) {
            // merge this query (in place) with the provided query, where the provided
            // query is dominant (i.e. any properties it has override this object)
            //
            // These are the merge rules:
            // this.filtered - take from source
            // this.size - take from source if set
            // this.from - take from source if set
            // this.fields - append any new ones from source
            // this.aggs - append any new ones from source, overwriting any with the same name
            // this.must - append any new ones from source
            // this.mustNot - append any new ones from source
            // this.queryString - take from source if set
            // this.sort - prepend any from source
            // this.source - append any new ones from source

            this.filtered = source.filtered;
            if (source.size) {
                this.size = source.size;
            }
            if (source.from) {
                this.from = source.from;
            }
            if (source.fields && source.fields.length > 0) {
                for (var i = 0; i < source.fields.length; i++) {
                    this.addField(source.fields[i]);
                }
            }
            var aggs = source.listAggregations();
            for (var i = 0; i < aggs.length; i++) {
                this.addAggregation(aggs[i], true);
            }
            var must = source.listMust();
            for (var i = 0; i < must.length; i++) {
                this.addMust(must[i]);
            }
            let mustNot = source.listMustNot();
            for (let i = 0; i < mustNot.length; i++) {
                this.addMustNot(mustNot[i]);
            }
            if (source.getQueryString()) {
                this.setQueryString(source.getQueryString())
            }
            var sorts = source.getSortBy();
            if (sorts && sorts.length > 0) {
                sorts.reverse();
                for (var i = 0; i < sorts.length; i++) {
                    this.prependSortBy(sorts[i])
                }
            }
            var includes = source.getSourceIncludes();
            var excludes = source.getSourceExcludes();
            this.addSourceFilters({include: includes, exclude: excludes});
        };

        this.objectify = function(params) {
            if (!params) {
                params = {};
            }
            // this allows you to specify which bits of the query get objectified
            var include_query_string = params.include_query_string === undefined ? true : params.include_query_string;
            var include_filters = params.include_filters === undefined ? true : params.include_filters;
            var include_paging = params.include_paging === undefined ? true : params.include_paging;
            var include_sort = params.include_sort === undefined ? true : params.include_sort;
            var include_fields = params.include_fields === undefined ? true : params.include_fields;
            var include_aggregations = params.include_aggregations === undefined ? true : params.include_aggregations;
            var include_source_filters = params.include_source_filters === undefined ? true : params.include_source_filters;

            // queries will be separated in queries and bool filters, which may then be
            // combined later
            var q = {};
            var query_part = {};
            var bool = {};

            // query string
            if (this.queryString && include_query_string) {
                $.extend(query_part, this.queryString.objectify());
            }

            if (include_filters) {
                // add any MUST filters
                if (this.must.length > 0) {
                    var musts = [];
                    for (var i = 0; i < this.must.length; i++) {
                        var m = this.must[i];
                        musts.push(m.objectify());
                    }
                    bool["must"] = musts;
                }
                // add any must_not filters
                if (this.mustNot.length > 0) {
                    let mustNots = [];
                    for (var i = 0; i < this.mustNot.length; i++) {
                        var m = this.mustNot[i];
                        mustNots.push(m.objectify());
                    }
                    bool["must_not"] = mustNots;
                }
            }

            var qpl = Object.keys(query_part).length;
            var bpl = Object.keys(bool).length;
            var query_portion = {};
            if (qpl === 0 && bpl === 0) {
                query_portion["match_all"] = {};
            } else if (qpl === 0 && bpl > 0) {
                query_portion["bool"] = bool;
            } else if (qpl > 0 && bpl === 0) {
                query_portion = query_part;
            } else if (qpl > 0 && bpl > 0) {
                query_portion["bool"] = bool;
                query_portion["bool"]["must"].push(query_part);
            }
            q["query"] = query_portion;

            if (include_paging) {
                // page size
                if (this.size !== undefined && this.size !== false) {
                    q["size"] = this.size;
                }

                // page number (from)
                if (this.from) {
                    q["from"] = this.from;
                }
            }

            // sort option
            if (this.sort.length > 0 && include_sort) {
                q["sort"] = [];
                for (var i = 0; i < this.sort.length; i++) {
                    q.sort.push(this.sort[i].objectify())
                }
            }

            // fields
            if (this.fields.length > 0 && include_fields) {
                q["stored_fields"] = this.fields;
            }

            // add any aggregations
            if (this.aggs.length > 0 && include_aggregations) {
                q["aggs"] = {};
                for (var i = 0; i < this.aggs.length; i++) {
                    var agg = this.aggs[i];
                    $.extend(q.aggs, agg.objectify())
                }
            }

            // add the source filters
            if (include_source_filters && this.source && (this.source.include || this.source.exclude)) {
                q["_source"] = {};
                if (this.source.include.length > 0) {
                    q["_source"]["include"] = this.source.include;
                }
                if (this.source.exclude.length > 0) {
                    q["_source"]["exclude"] = this.source.exclude;
                }
            }

            // set whether to track the total
            if (this.trackTotalHits) {
                q["track_total_hits"] = true;
            }

            return q;
        };

        // When a query is requested as a string, dump via JSON.
        es.Query.prototype.toString = function queryToString() {
            return JSON.stringify(this.objectify())
        };

        this.parse = function(obj) {

            function parseBool(bool, target) {
                if (bool.must) {
                    for (var i = 0; i < bool.must.length; i++) {
                        var type = Object.keys(bool.must[i])[0];
                        var fil = es.filterFactory(type, {raw: bool.must[i]});
                        if (fil && type !== "query_string") {
                            target.addMust(fil);
                        } else if (fil && type === "query_string") {
                            // FIXME: this will work fine as long as there are no nested bools
                            target.setQueryString(fil);
                        }
                    }
                }
                if (bool.must_not) {
                    for (var i = 0; i < bool.must_not.length; i++) {
                        var type = Object.keys(bool.must_not[i])[0];
                        var fil = es.filterFactory(type, {raw: bool.must_not[i]});
                        if (fil) {
                            target.addMustNot(fil);
                        }
                    }
                }
            }

            function parseQuery(q, target) {
                var keys = Object.keys(q);
                for (var i = 0; i < keys.length; i++) {
                    var type = keys[i];
                    if (type === "bool") {
                        parseBool(q.bool, target);
                        continue;
                    }
                    var impl = es.filterFactory(type, {raw: q[type]});
                    if (impl) {
                        if (type === "query_string") {
                            target.setQueryString(impl);
                        }
                        // FIXME: other non-filtered queries?
                    }
                }
            }

            // parse the query itself
            if (obj.query) {
                if (obj.query.filtered) {
                    this.filtered = true;
                    var bool = obj.query.filtered.filter.bool;
                    if (bool) {
                        parseBool(bool, this);
                    }
                    var q = obj.query.filtered.query;
                    parseQuery(q, this);
                } else {
                    var q = obj.query;
                    parseQuery(q, this);
                }
            }

            if (obj.size) {
                this.size = obj.size;
            }

            if (obj.from) {
                this.from = obj.from;
            }

            if (obj.stored_fields) {
                this.fields = obj.stored_fields;
            }

            if (obj.sort) {
                for (var i = 0; i < obj.sort.length; i++) {
                    var so = obj.sort[i];
                    this.addSortBy(es.newSort({raw: so}));
                }
            }

            if (obj.aggs || obj.aggregations) {
                var aggs = obj.aggs ? obj.aggs : obj.aggregations;
                var anames = Object.keys(aggs);
                for (var i = 0; i < anames.length; i++) {
                    var name = anames[i];
                    var agg = aggs[name];
                    var type = Object.keys(agg)[0];
                    var raw = {};
                    raw[name] = agg;
                    var oa = es.aggregationFactory(type, {raw: raw});
                    if (oa) {
                        this.addAggregation(oa);
                    }
                }
            }

            if (obj._source) {
                var source = obj._source;
                var include = [];
                var exclude = [];

                if (typeof source === "string") {
                    include.push(source);
                }
                else if (Array.isArray(source)) {
                    include = source;
                } else {
                    if (source.hasOwnProperty("include")) {
                        include = source.include;
                    }
                    if (source.hasOwnProperty("exclude")) {
                        exclude = source.exclude;
                    }
                }
                this.setSourceFilters({include: include, exclude: exclude});
            }
        };

        ///////////////////////////////////////////////////////////
        // final part of construction - set the dynamic properties
        // via their setters

        if (params.queryString) {
            this.setQueryString(params.queryString);
        }

        if (params.sort) {
            this.setSortBy(params.sort);
        }

        // finally, if we're given a raw query, parse it
        if (params.raw) {
            this.parse(params.raw)
        }
    },

    ///////////////////////////////////////////////
    // Query String

    newQueryString : function(params) {
        if (!params) { params = {} }
        return new es.QueryString(params);
    },
    QueryString : function(params) {
        this.queryString = params.queryString || false;
        this.defaultField = params.defaultField || false;
        this.defaultOperator = params.defaultOperator || "OR";

        this.fuzzify = params.fuzzify || false;     // * or ~
        this.escapeSet = params.escapeSet || es.specialCharsSubSet;
        this.pairs = params.pairs || es.characterPairs;
        this.unEscapeSet = params.unEscapeSet || es.specialChars;

        this.objectify = function() {
            var qs = this._escape(this._fuzzify(this.queryString));
            var obj = {query_string : {query : qs}};
            if (this.defaultOperator) {
                obj.query_string["default_operator"] = this.defaultOperator;
            }
            if (this.defaultField) {
                obj.query_string["default_field"] = this.defaultField;
            }
            return obj;
        };

        this.parse = function(obj) {
            if (obj.query_string) {
                obj = obj.query_string;
            }
            this.queryString = this._unescape(obj.query);
            if (obj.default_operator) {
                this.defaultOperator = obj.default_operator;
            }
            if (obj.default_field) {
                this.defaultField = obj.default_field;
            }
        };

        this._fuzzify = function(str) {
            if (!this.fuzzify || !(this.fuzzify === "*" || this.fuzzify === "~")) {
                return str;
            }

            if (!(str.indexOf('*') === -1 && str.indexOf('~') === -1 && str.indexOf(':') === -1)) {
                return str;
            }

            var pq = "";
            var optparts = str.split(' ');
            for (var i = 0; i < optparts.length; i++) {
                var oip = optparts[i];
                if (oip.length > 0) {
                    oip = oip + this.fuzzify;
                    this.fuzzify == "*" ? oip = "*" + oip : false;
                    pq += oip + " ";
                }
            }
            return pq;
        };

        this._escapeRegExp = function(string) {
            return string.replace(/([.*+?^=!:${}()|\[\]\/\\])/g, "\\$1");
        };

        this._replaceAll = function(string, find, replace) {
            return string.replace(new RegExp(this._escapeRegExp(find), 'g'), replace);
        };

        this._unReplaceAll = function(string, find) {
            return string.replace(new RegExp("\\\\(" + this._escapeRegExp(find) + ")", 'g'), "$1");
        };

        this._paired = function(string, pair) {
            var matches = (string.match(new RegExp(this._escapeRegExp(pair), "g"))) || [];
            return matches.length % 2 === 0;
        };

        this._escape = function(str) {
            // make a copy of the special characters (we may modify it in a moment)
            var scs = this.escapeSet.slice(0);

            // first check for pairs, and push any extra characters to be escaped
            for (var i = 0; i < this.pairs.length; i++) {
                var char = this.pairs[i];
                if (!this._paired(str, char)) {
                    scs.push(char);
                }
            }

            // now do the escape
            for (var i = 0; i < scs.length; i++) {
                var char = scs[i];
                str = this._replaceAll(str, char, "\\" + char);
            }

            return str;
        };

        this._unescape = function(str) {
            for (var i = 0; i < this.unEscapeSet.length; i++) {
                var char = this.unEscapeSet[i];
                str = this._unReplaceAll(str, char)
            }
            return str;
        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    //////////////////////////////////////////////
    // Sort Option

    newSort : function(params) {
        if (!params) { params = {} }
        return new es.Sort(params);
    },
    Sort : function(params) {
        this.field = params.field || "_score";
        this.order = params.order || "desc";

        this.objectify = function() {
            var obj = {};
            obj[this.field] = {order: this.order};
            return obj;
        };

        this.parse = function(obj) {
            this.field = Object.keys(obj)[0];
            if (obj[this.field].order) {
                this.order = obj[this.field].order;
            }
        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    //////////////////////////////////////////////
    // Root Aggregation and aggregation implementations

    newAggregation : function(params) {
        if (!params) { params = {} }
        return new es.Aggregation(params);
    },
    Aggregation : function(params) {
        this.name = params.name;
        this.aggs = params.aggs || [];

        this.addAggregation = function(agg) {
            for (var i = 0; i < this.aggs.length; i++) {
                if (this.aggs[i].name === agg.name) {
                    return;
                }
            }
            this.aggs.push(agg);
        };
        this.removeAggregation = function() {};
        this.clearAggregations = function() {};

        // for use by sub-classes, for their convenience in rendering
        // the overall structure of the aggregation to an object
        this._make_aggregation = function(type, body) {
            var obj = {};
            obj[this.name] = {};
            obj[this.name][type] = body;

            if (this.aggs.length > 0) {
                obj[this.name]["aggs"] = {};
                for (var i = 0; i < this.aggs.length; i++) {
                    $.extend(obj[this.name]["aggs"], this.aggs[i].objectify())
                }
            }

            return obj;
        };

        this._parse_wrapper = function(obj, type) {
            this.name = Object.keys(obj)[0];
            var body = obj[this.name][type];

            var aggs = obj[this.name].aggs ? obj[this.name].aggs : obj[this.name].aggregations;
            if (aggs) {
                var anames = Object.keys(aggs);
                for (var i = 0; i < anames.length; i++) {
                    var name = anames[i];
                    var agg = aggs[anames[i]];
                    var subtype = Object.keys(agg)[0];
                    var raw = {};
                    raw[name] = agg;
                    var oa = es.aggregationFactory(subtype, {raw: raw});
                    if (oa) {
                        this.addAggregation(oa);
                    }
                }
            }

            return body;
        }
    },

    newTermsAggregation : function(params) {
        if (!params) { params = {} }
        es.TermsAggregation.prototype = es.newAggregation(params);
        return new es.TermsAggregation(params);
    },
    TermsAggregation : function(params) {
        this.field = params.field || false;
        this.size = params.size || 10;

        // set the ordering for the first time
        this.orderBy = "_count";
        if (params.orderBy) {
            this.orderBy = params.orderBy;
            if (this.orderBy[0] !== "_") {
                this.orderBy = "_" + this.orderBy;
            }
        }
        this.orderDir = params.orderDir || "desc";

        // provide a method to set and normalise the ordering in future
        this.setOrdering = function(orderBy, orderDir) {
            this.orderBy = orderBy;
            if (this.orderBy[0] !== "_") {
                this.orderBy = "_" + this.orderBy;
            }
            this.orderDir = orderDir;
        };

        this.objectify = function() {
            var body = {field: this.field, size: this.size, order: {}};
            body.order[this.orderBy] = this.orderDir;
            return this._make_aggregation("terms", body);
        };

        this.parse = function(obj) {
            var body = this._parse_wrapper(obj, "terms");
            this.field = body.field;
            if (body.size) {
                this.size = body.size;
            }
            if (body.order) {
                this.orderBy = Object.keys(body.order)[0];
                this.orderDir = body.order[this.orderBy];
            }
        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    newCardinalityAggregation : function(params) {
        if (!params) { params = {} }
        es.CardinalityAggregation.prototype = es.newAggregation(params);
        return new es.CardinalityAggregation(params);
    },
    CardinalityAggregation : function(params) {
        this.field = es.getParam(params.field, false);

        this.objectify = function() {
            var body = {field: this.field};
            return this._make_aggregation("cardinality", body);
        };

        this.parse = function(obj) {
            var body = this._parse_wrapper(obj, "cardinality");
            this.field = body.field;
        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    newRangeAggregation : function(params) {
        if (!params) { params = {} }
        es.RangeAggregation.prototype = es.newAggregation(params);
        return new es.RangeAggregation(params);
    },
    RangeAggregation : function(params) {
        this.field = params.field || false;
        this.ranges = params.ranges || [];

        this.objectify = function() {
            var body = {field: this.field, ranges: this.ranges};
            return this._make_aggregation("range", body);
        };

        this.parse = function(obj) {
            var body = this._parse_wrapper(obj, "range");
            this.field = body.field;
            this.ranges = body.ranges;
        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    newGeoDistanceAggregation : function(params) {
        if (!params) { params = {} }
        es.GeoDistanceAggregation.prototype = es.newAggregation(params);
        return new es.GeoDistanceAggregation(params);
    },
    GeoDistanceAggregation : function(params) {
        this.field = params.field || false;
        this.lat = params.lat || false;
        this.lon = params.lon || false;
        this.unit = params.unit || "m";
        this.distance_type = params.distance_type || "sloppy_arc";
        this.ranges = params.ranges || [];

        this.objectify = function() {
            var body = {
                field: this.field,
                origin: {lat : this.lat, lon: this.lon},
                unit : this.unit,
                distance_type : this.distance_type,
                ranges: this.ranges
            };
            return this._make_aggregation("geo_distance", body);
        };

        this.parse = function(obj) {
            var body = this._parse_wrapper(obj, "geo_distance");
            this.field = body.field;

            // FIXME: only handles the lat/lon object - but there are several forms
            // this origin could take
            var origin = body.origin;
            if (origin.lat) {
                this.lat = origin.lat;
            }
            if (origin.lon) {
                this.lon = origin.lon;
            }

            if (body.unit) {
                this.unit = body.unit;
            }

            if (body.distance_type) {
                this.distance_type = body.distance_type;
            }

            this.ranges = body.ranges;
        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    newGeohashGridAggregation : function(params) {
        if (!params) { params = {} }
        es.GeohashGridAggregation.prototype = es.newAggregation(params);
        return new es.GeohashGridAggregation(params);
    },
    GeohashGridAggregation : function(params) {
        this.field = params.field || false;
        this.precision = params.precision || 3;

        this.objectify = function() {
            var body = {
                field: this.field,
                precision: this.precision
            };
            return this._make_aggregation("geohash_grid", body);
        };

        this.parse = function(obj) {
            var body = this._parse_wrapper(obj, "geohash_grid");
            this.field = body.field;
            this.precision = body.precision;
        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    newStatsAggregation : function(params) {
        if (!params) { params = {} }
        es.StatsAggregation.prototype = es.newAggregation(params);
        return new es.StatsAggregation(params);
    },
    StatsAggregation : function(params) {
        this.field = params.field || false;

        this.objectify = function() {
            var body = {field: this.field};
            return this._make_aggregation("stats", body);
        };

        this.parse = function(obj) {

        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    newSumAggregation : function(params) {
        if (!params) { params = {} }
        es.SumAggregation.prototype = es.newAggregation(params);
        return new es.SumAggregation(params);
    },
    SumAggregation : function(params) {
        this.field = params.field || false;

        this.objectify = function() {
            var body = {field: this.field};
            return this._make_aggregation("sum", body);
        };

        this.parse = function(obj) {

        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    newDateHistogramAggregation : function(params) {
        if (!params) { params = {} }
        es.DateHistogramAggregation.prototype = es.newAggregation(params);
        return new es.DateHistogramAggregation(params);
    },
    DateHistogramAggregation : function(params) {
        this.field = params.field || false;
        this.interval = params.interval || "month";
        this.format = params.format || false;

        this.objectify = function() {
            var body = {field: this.field, interval: this.interval};
            if (this.format) {
                body["format"] = this.format;
            }
            return this._make_aggregation("date_histogram", body);
        };

        this.parse = function(obj) {
            var body = this._parse_wrapper(obj, "date_histogram");
            this.field = body.field;
            if (body.interval) {
                this.interval = body.interval;
            }
            if (body.format) {
                this.format = body.format;
            }
        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    newFiltersAggregation : function(params) {
        if (!params) { params = {} }
        es.FiltersAggregation.prototype = es.newAggregation(params);
        return new es.FiltersAggregation(params);
    },
    FiltersAggregation : function(params) {
        this.filters = params.filters || {};

        this.objectify = function() {
            var body = {filters: this.filters};
            return this._make_aggregation("filters", body);
        };

        this.parse = function(obj) {
            var body = this._parse_wrapper(obj, "filters");
            this.filters = body.filters;
        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    ///////////////////////////////////////////////////
    // Filters

    newFilter : function(params) {
        if (!params) { params = {} }
        return new es.Filter(params);
    },
    Filter : function(params) {
        this.field = params.field;
        this.type_name = params.type_name;
        this.matches = function(other) {
            // type must match
            if (other.type_name !== this.type_name) {
                return false;
            }
            // field (if set) must match
            if (other.field && other.field !== this.field) {
                return false;
            }
            // otherwise this matches
            return true;
        };
        this.objectify = function() {};
        this.parse = function() {};
    },

    newTermFilter : function(params) {
        if (!params) { params = {} }
        params.type_name = "term";
        es.TermFilter.prototype = es.newFilter(params);
        return new es.TermFilter(params);
    },
    TermFilter : function(params) {
        // this.filter handled by superclass
        this.value = params.value || false;

        this.matches = function(other) {
            // ask the parent object first
            // var pm = this.__proto__.matches.call(this, other);
            var pm = Object.getPrototypeOf(this).matches.call(this, other);
            if (!pm) {
                return false;
            }
            // value (if set) must match
            if (other.value && other.value !== this.value) {
                return false;
            }

            return true;
        };

        this.objectify = function() {
            var obj = {term : {}};
            obj.term[this.field] = this.value;
            return obj;
        };

        this.parse = function(obj) {
            if (obj.term) {
                obj = obj.term;
            }
            this.field = Object.keys(obj)[0];
            this.value = obj[this.field];
        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    newExistsFilter : function(params) {
        if (!params) { params = {} }
        params.type_name = "term";
        es.ExistsFilter.prototype = es.newFilter(params);
        return new es.ExistsFilter(params);
    },
    ExistsFilter : function(params) {
        this.objectify = function() {
            return {exists : {field: this.field}};
        };

        this.parse = function(obj) {
            if (obj.exists) {
                obj = obj.exists;
            }
            this.field = obj.field;
        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    newTermsFilter : function(params) {
        if (!params) { params = {} }
        params.type_name = "terms";
        es.TermsFilter.prototype = es.newFilter(params);
        return new es.TermsFilter(params);
    },
    TermsFilter : function(params) {
        // this.field handled by superclass
        this.values = params.values || false;
        this.execution = params.execution || false;

        this.matches = function(other) {
            // ask the parent object first
            // var pm = this.__proto__.matches.call(this, other);
            var pm = Object.getPrototypeOf(this).matches.call(this, other);
            if (!pm) {
                return false;
            }

            // values (if set) must be the same list
            if (other.values) {
                if (other.values.length !== this.values.length) {
                    return false;
                }
                for (var i = 0; i < other.values.length; i++) {
                    if ($.inArray(other.values[i], this.values) === -1) {
                        return false;
                    }
                }
            }

            return true;
        };

        this.objectify = function() {
            var val = this.values || [];
            var obj = {terms : {}};
            obj.terms[this.field] = val;
            if (this.execution) {
                obj.terms["execution"] = this.execution;
            }
            return obj;
        };

        this.parse = function(obj) {
            if (obj.terms) {
                obj = obj.terms;
            }
            this.field = Object.keys(obj)[0];
            this.values = obj[this.field];
            if (obj.execution) {
                this.execution = obj.execution;
            }
        };

        this.add_term = function(term) {
            if (!this.values) {
                this.values = [];
            }
            if ($.inArray(term, this.values) === -1) {
                this.values.push(term);
            }
        };

        this.has_term = function(term) {
            if (!this.values) {
                return false;
            }
            return $.inArray(term, this.values) >= 0;
        };

        this.remove_term = function(term) {
            if (!this.values) {
                return;
            }
            var idx = $.inArray(term, this.values);
            if (idx >= 0) {
                this.values.splice(idx, 1);
            }
        };

        this.has_terms = function() {
            return (this.values !== false && this.values.length > 0)
        };

        this.term_count = function() {
            return this.values === false ? 0 : this.values.length;
        };

        this.clear_terms = function() {
            this.values = false;
        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    newRangeFilter : function(params) {
        if (!params) { params = {} }
        params.type_name = "range";
        es.RangeFilter.prototype = es.newFilter(params);
        return new es.RangeFilter(params);
    },
    RangeFilter : function(params) {
        // this.field handled by superclass
        this.lt = es.getParam(params.lt, false);
        this.lte = es.getParam(params.lte, false);
        this.gte = es.getParam(params.gte, false);
        this.format = es.getParam(params.format, false);

        // normalise the values to strings
        if (this.lt) { this.lt = this.lt.toString() }
        if (this.lte) { this.lte = this.lte.toString() }
        if (this.gte) { this.gte = this.gte.toString() }

        this.matches = function(other) {
            // ask the parent object first
            // var pm = this.__proto__.matches.call(this, other);
            var pm = Object.getPrototypeOf(this).matches.call(this, other);
            if (!pm) {
                return false;
            }

            // ranges (if set) must match
            if (other.lt) {
                if (other.lt !== this.lt) {
                    return false;
                }
            }
            if (other.lte) {
                if (other.lte !== this.lte) {
                    return false;
                }
            }
            if (other.gte) {
                if (other.gte !== this.gte) {
                    return false;
                }
            }

            if (other.format) {
                if (other.format !== this.format) {
                    return false;
                }
            }

            return true;
        };

        this.objectify = function() {
            var obj = {range: {}};
            obj.range[this.field] = {};
            if (this.lte !== false) {
                obj.range[this.field]["lte"] = this.lte;
            }
            if (this.lt !== false && this.lte === false) {
                obj.range[this.field]["lt"] = this.lt;
            }
            if (this.gte !== false) {
                obj.range[this.field]["gte"] = this.gte;
            }
            if (this.format !== false) {
                obj.range[this.field]["format"] = this.format;
            }
            return obj;
        };

        this.parse = function(obj) {
            if (obj.range) {
                obj = obj.range;
            }
            this.field = Object.keys(obj)[0];
            if (obj[this.field].lte !== undefined && obj[this.field].lte !== false) {
                this.lte = obj[this.field].lte;
            }
            if (obj[this.field].lt !== undefined && obj[this.field].lt !== false) {
                this.lt = obj[this.field].lt;
            }
            if (obj[this.field].gte !== undefined && obj[this.field].gte !== false) {
                this.gte = obj[this.field].gte;
            }
            if (obj[this.field].format !== undefined && obj[this.field].format !== false) {
                this.format = obj[this.field].format;
            }
        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    newGeoDistanceRangeFilter : function(params) {
        if (!params) { params = {} }
        params.type_name = "geo_distance_range";
        es.GeoDistanceRangeFilter.prototype = es.newFilter(params);
        return new es.GeoDistanceRangeFilter(params);
    },
    GeoDistanceRangeFilter : function(params) {
        // this.field is handled by superclass
        this.lt = params.lt || false;
        this.gte = params.gte || false;
        this.lat = params.lat || false;
        this.lon = params.lon || false;
        this.unit = params.unit || "m";

        this.objectify = function() {
            var obj = {geo_distance_range: {}};
            obj.geo_distance_range[this.field] = {lat: this.lat, lon: this.lon};
            if (this.lt) {
                obj.geo_distance_range["lt"] = this.lt + this.unit;
            }
            if (this.gte) {
                obj.geo_distance_range["gte"] = this.gte + this.unit;
            }
            return obj;
        };

        this.parse = function(obj) {
            function endsWith(str, suffix) {
                return str.indexOf(suffix, str.length - suffix.length) !== -1;
            }

            function splitUnits(str) {
                var unit = false;
                for (var i = 0; i < es.distanceUnits.length; i++) {
                    var cu = es.distanceUnits[i];
                    if (endsWith(str, cu)) {
                        str = str.substring(0, str.length - cu.length);
                        unit = str.substring(str.length - cu.length);
                    }
                }

                return [str, unit];
            }

            if (obj.geo_distance_range) {
                obj = obj.geo_distance_range;
            }
            this.field = Object.keys(obj)[0];
            this.lat = obj[this.field].lat;
            this.lon = obj[this.field].lon;

            var lt = obj[this.field].lt;
            var gte = obj[this.field].gte;

            if (lt) {
                lt = lt.trim();
                var parts = splitUnits(lt);
                this.lt = parts[0];
                this.unit = parts[1];
            }

            if (gte) {
                gte = gte.trim();
                var parts = splitUnits(gte);
                this.gte = parts[0];
                this.unit = parts[1];
            }
        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    newGeoBoundingBoxFilter : function(params) {
        if (!params) { params = {} }
        params.type_name = "geo_bounding_box";
        return edges.instantiate(es.GeoBoundingBoxFilter, params, es.newFilter);
    },
    GeoBoundingBoxFilter : function(params) {
        this.top_left = params.top_left || false;
        this.bottom_right = params.bottom_right || false;

        this.matches = function(other) {
            // ask the parent object first
            var pm = Object.getPrototypeOf(this).matches.call(this, other);
            if (!pm) {
                return false;
            }
            if (other.top_left && other.top_left !== this.top_left) {
                return false;
            }
            if (other.bottom_right && other.bottom_right !== this.bottom_right) {
                return false;
            }
            return true;
        };

        this.objectify = function() {
            var obj = {geo_bounding_box : {}};
            obj.geo_bounding_box[this.field] = {
                top_left: this.top_left,
                bottom_right: this.bottom_right
            };
            return obj;
        };

        this.parse = function(obj) {
            if (obj.geo_bounding_box) {
                obj = obj.geo_bounding_box;
            }
            this.field = Object.keys(obj)[0];
            this.top_left = obj[this.field].top_left;
            this.bottom_right = obj[this.field].bottom_right;
        };

        if (params.raw) {
            this.parse(params.raw);
        }
    },

    ////////////////////////////////////////////////////
    // The result object

    newResult : function(params) {
        if (!params) { params = {} }
        return new es.Result(params);
    },
    Result : function(params) {
        this.data = params.raw;

        this.buckets = function(agg_name) {
            return this.data.aggregations[agg_name].buckets;
        };

        this.aggregation = function(agg_name) {
            return this.data.aggregations[agg_name];
        };

        this.results = function() {
            var res = [];
            if (this.data.hits && this.data.hits.hits) {
                for (var i = 0; i < this.data.hits.hits.length; i++) {
                    var source = this.data.hits.hits[i];
                    if ("_source" in source) {
                        res.push(source._source);
                    } else if ("_fields" in source) {
                        res.push(source._fields);
                    } else {
                        res.push(source);
                    }
                }
            }
            return res;
        };

        this.total = function() {
            if (this.data.hits && this.data.hits.total && this.data.hits.total.value) {
                return parseInt(this.data.hits.total.value);
            }
            return false;
        }
    },


    ////////////////////////////////////////////////////
    // Primary functions for interacting with elasticsearch

    doQuery : function(params) {
        // extract the parameters of the request
        var success = params.success;
        var error = params.error;
        var complete = params.complete;
        var search_url = params.search_url;
        var queryobj = params.queryobj;
        var datatype = params.datatype;

        // serialise the query
        var querystring = JSON.stringify(queryobj);

        // prep the callbacks (they are connected)
        var error_callback = es.queryError(error);
        var success_callback = es.querySuccess(success, error_callback);

        // make the call to the elasticsearch web service
        if (es.requestMethod === "get") {
            $.ajax({
                type: "get",
                url: search_url,
                data: {source: querystring},
                dataType: datatype,
                success: success_callback,
                error: error_callback,
                complete: complete
            });
        } else if (es.requestMethod === "post") {
            $.ajax({
                type: "post",
                url: search_url,
                data: querystring,
                contentType: "application/json",
                dataType: datatype,
                success: success_callback,
                error: error_callback,
                complete: complete
            });
        } else {
            throw "es.requestMethod must be either 'get' or 'post";
        }
    },

    querySuccess : function(callback, error_callback) {
        return function(data) {
            if (data.hasOwnProperty("error")) {
                error_callback(data);
                return;
            }

            var result = es.newResult({raw: data});
            callback(result);
        }
    },

    queryError : function(callback) {
        return function(data) {
            if (callback) {
                callback(data);
            } else {
                throw new Error(data);
            }
        }
    },

    /////////////////////////////////////////////////////

    getParam : function(value, def) {
        return value !== undefined ? value : def;
    }
};

/** @namespace */
var edges = {

    //////////////////////////////////////////////////////
    /** @namespace */
    /** function to run to start a new Edge */
    /** * @param selector="body" {String} The jquery selector for the element where the edge will be deployed.
     * @param search_url {String} The base search url which will respond to elasticsearch queries.  Generally ends with _search
     * @param datatype="jsonp" {String} Datatype for ajax requests to use - overall recommend using jsonp
     * @param preflightQueries {Dictionary} Dictionary of queries to be run before the primary query is executed: preflight id : es.newQuery(....). Results will appear with the same ids in this.preflightResults.
     Preflight queries are /not/ subject to the base query
     * @param baseQuery {String} Query that forms the basis of all queries that are assembled and run. Note that baseQuery is inviolable - it's requirements will always be enforced
     * @param openingQuery {String} Query to use to initialise the search.  Use this to set your opening values for things like page size, initial search terms, etc.  Any request to
     reset the interface will return to this query.
     * @param secondaryQueries {?} Dictionary of functions that will generate secondary queries which also need to be run at the point that cycle() is called.
     These functions and their resulting queries will be run /after/ the primary query (so can take advantage of the results).
     Their results will be stored in this.secondaryResults. Secondary queries are not subject the base query, although the functions may of course apply the base query too if they wish.
     secondary id : function()
     * @param initialSearch {Boolean} Should the init process do a search
     * @param  staticFiles {Object} List of static files (e.g. data files) to be loaded at startup, and made available
     on the object for use by components.
     {"id" : internal id to give the file, "url" : file url, "processor" : edges.csv.newObjectByRow, "datatype" : "text", "opening" : function to be run after processing for initial state}
     * @param manageUrl {Boolean} Should the search url be synchronised with the browser's url bar after search
     and should queries be retrieved from the url on init
     * @param urlQuerySource="source" {String} Query parameter in which the query for this edge instance will be stored.
     * @param template {Object} Template object that will be used to draw the frame for the edge.  May be left
     blank, in which case the edge will assume that the elements are already rendered on the page by the caller
     * @param components {Array} List of all the components that are involved in this edge
     * @param renderPacks=[edges.bs3, edges.nvd3, edges.highcharts, edges.google, edges.d3] {Array} Render packs to use to source automatically assigned rendering objects.
     Defaults to [edges.bs3, edges.nvd3, edges.highcharts, edges.google, edges.d3] */
    newEdge : function(params) {
        if (!params) { params = {} }
        return new edges.Edge(params);
    },
    /** @class */
    Edge : function(params) {

        /////////////////////////////////////////////
        // parameters that can be set via params arg

        // the jquery selector for the element where the edge will be deployed
        this.selector = edges.getParam(params.selector, "body");

        // the base search url which will respond to elasticsearch queries.  Generally ends with _search
        this.search_url = edges.getParam(params.search_url, false);

        // datatype for ajax requests to use - overall recommend using jsonp
        this.datatype = edges.getParam(params.datatype, "jsonp");

        // dictionary of queries to be run before the primary query is executed
        // {"<preflight id>" : es.newQuery(....)}
        // results will appear with the same ids in this.preflightResults
        // preflight queries are /not/ subject to the base query
        this.preflightQueries = edges.getParam(params.preflightQueries, false);

        // query that forms the basis of all queries that are assembled and run
        // Note that baseQuery is inviolable - it's requirements will always be enforced
        this.baseQuery = edges.getParam(params.baseQuery, false);

        // query to use to initialise the search.  Use this to set your opening
        // values for things like page size, initial search terms, etc.  Any request to
        // reset the interface will return to this query
        this.openingQuery = edges.getParam(params.openingQuery, typeof es !== 'undefined' ? es.newQuery() : false);

        // dictionary of functions that will generate secondary queries which also need to be
        // run at the point that cycle() is called.  These functions and their resulting
        // queries will be run /after/ the primary query (so can take advantage of the
        // results).  Their results will be stored in this.secondaryResults.
        // secondary queries are not subject the base query, although the functions
        // may of course apply the base query too if they wish
        // {"<secondary id>" : function() }
        this.secondaryQueries = edges.getParam(params.secondaryQueries, false);

        // dictionary mapping keys to urls that will be used for search.  These should be
        // the same keys as used in secondaryQueries, if those secondary queries should be
        // issued against different urls than the primary search_url.
        this.secondaryUrls = edges.getParam(params.secondaryUrls, false);

        // should the init process do a search
        this.initialSearch = edges.getParam(params.initialSearch, true);

        // list of static files (e.g. data files) to be loaded at startup, and made available
        // on the object for use by components
        // {"id" : "<internal id to give the file>", "url" : "<file url>", "processor" : edges.csv.newObjectByRow, "datatype" : "text", "opening" : <function to be run after processing for initial state>}
        this.staticFiles = edges.getParam(params.staticFiles, []);

        // should the search url be synchronised with the browser's url bar after search
        // and should queries be retrieved from the url on init
        this.manageUrl = edges.getParam(params.manageUrl, false);

        // query parameter in which the query for this edge instance will be stored
        this.urlQuerySource = edges.getParam(params.urlQuerySource, "source");

        // options to be passed to es.Query.objectify when prepping the query to be placed in the URL
        this.urlQueryOptions = edges.getParam(params.urlQueryOptions, false);

        // template object that will be used to draw the frame for the edge.  May be left
        // blank, in which case the edge will assume that the elements are already rendered
        // on the page by the caller
        this.template = edges.getParam(params.template, false);

        // list of all the components that are involved in this edge
        this.components = edges.getParam(params.components, []);

        // the query adapter
        this.queryAdapter = edges.getParam(params.queryAdapter, edges.newESQueryAdapter());

        // render packs to use to source automatically assigned rendering objects
        this.renderPacks = edges.getParam(params.renderPacks, [edges.bs3, edges.nvd3, edges.highcharts, edges.google, edges.d3]);

        // list of callbacks to be run synchronously with the edge instance as the argument
        // (these bind at the same points as all the events are triggered, and are keyed the same way)
        this.callbacks = edges.getParam(params.callbacks, {});

        /////////////////////////////////////////////
        // operational properties

        // the query most recently read from the url
        this.urlQuery = false;

        // original url parameters
        this.urlParams = {};

        // the short url for this page
        this.shortUrl = false;

        // the last primary ES query object that was executed
        this.currentQuery = false;

        // the last result object from the ES layer
        this.result = false;

        // the results of the preflight queries, keyed by their id
        this.preflightResults = {};

        // the actual secondary queries derived from the functions in this.secondaryQueries;
        this.realisedSecondaryQueries = {};

        // results of the secondary queries, keyed by their id
        this.secondaryResults = {};

        // if the search is currently executing
        this.searching = false;

        // jquery object that represents the selected element
        this.context = false;

        // raw access to this.staticFiles loaded resources, keyed by id
        this.static = {};

        // access to processed static files, keyed by id
        this.resources = {};

        // list of static resources where errors were encountered
        this.errorLoadingStatic = [];

        ////////////////////////////////////////////////////////
        // startup functions

        // at the bottom of this constructor, we'll call this function
        this.startup = function() {
            // obtain the jquery context for all our operations
            this.context = $(this.selector);

            // trigger the edges:init event
            this.trigger("edges:pre-init");

            // if we are to manage the URL, attempt to pull a query from it
            if (this.manageUrl) {
                var urlParams = this.getUrlParams();
                if (this.urlQuerySource in urlParams) {
                    this.urlQuery = es.newQuery({raw : urlParams[this.urlQuerySource]});
                    delete urlParams[this.urlQuerySource];
                }
                this.urlParams = urlParams;
            }

            // render the template if necessary
            if (this.template) {
                this.template.draw(this);
            }

            // call each of the components to initialise themselves
            for (var i = 0; i < this.components.length; i++) {
                var component = this.components[i];
                component.init(this);
            }

            // now call each component to render itself (pre-search)
            this.draw();

            // load any static files - this will happen asynchronously, so afterwards
            // we call finaliseStartup to finish the process
            var onward = edges.objClosure(this, "startupPart2");
            this.loadStaticsAsync(onward);
        };

        this.startupPart2 = function() {
            // FIXME: at this point we should check whether the statics all loaded correctly
            var onward = edges.objClosure(this, "startupPart3");
            this.runPreflightQueries(onward);
        };

        this.startupPart3 = function() {

            // determine whether to initialise with either the openingQuery or the urlQuery
            var requestedQuery = this.openingQuery;
            if (this.urlQuery) {
                // if there is a URL query, then we open with that, and then forget it
                requestedQuery = this.urlQuery;
                this.urlQuery = false
            }

            // request the components to contribute to the query
            for (var i = 0; i < this.components.length; i++) {
                var component = this.components[i];
                component.contrib(requestedQuery);
            }

            // finally push the query, which will reconcile it with the baseQuery
            this.pushQuery(requestedQuery);

            // trigger the edges:post-init event
            this.trigger("edges:post-init");

            // now issue a query
            this.cycle();
        };

        /////////////////////////////////////////////////////////
        // Edges lifecycle functions

        this.doQuery = function() {
            // the original doQuery has become doPrimaryQuery, so this has been aliased for this.cycle
            this.cycle();
        };

        this.cycle = function() {
            // if a search is currently executing, don't do anything, else turn it on
            // FIXME: should we queue them up? - see the d3 map for an example of how to do this
            if (this.searching) {
                return;
            }
            this.searching = true;

            // invalidate the short url
            this.shortUrl = false;

            // pre query event
            this.trigger("edges:pre-query");

            // if we are managing the url space, use pushState to set it
            if (this.manageUrl) {
                this.updateUrl();
            }

            // if there's a search url, do a query, otherwise call synchronise and draw directly
            if (this.search_url) {
                var onward = edges.objClosure(this, "cyclePart2");
                this.doPrimaryQuery(onward);
            } else {
                this.cyclePart2();
            }
        };

        this.cyclePart2 = function() {
            var onward = edges.objClosure(this, "cyclePart3");
            this.runSecondaryQueries(onward);
        };

        this.cyclePart3 = function() {
            this.synchronise();

            // pre-render trigger
            this.trigger("edges:pre-render");
            // render
            this.draw();
            // post render trigger
            this.trigger("edges:post-render");

            // searching has completed, so flip the switch back
            this.searching = false;
        };

        this.synchronise = function() {
            // ask the components to synchronise themselves with the latest state
            for (var i = 0; i < this.components.length; i++) {
                var component = this.components[i];
                component.synchronise()
            }
        };

        this.draw = function() {
            for (var i = 0; i < this.components.length; i++) {
                var component = this.components[i];
                component.draw(this);
            }
        };

        // reset the query to the start and re-issue the query
        this.reset = function() {
            // tell the world we're about to reset
            this.trigger("edges:pre-reset");

            // clone from the opening query
            var requestedQuery = this.cloneOpeningQuery();

            // request the components to contribute to the query
            for (var i = 0; i < this.components.length; i++) {
                var component = this.components[i];
                component.contrib(requestedQuery);
            }

            // push the query, which will reconcile it with the baseQuery
            this.pushQuery(requestedQuery);

            // tell the world that we've done the reset
            this.trigger("edges:post-reset");

            // now execute the query
            // this.doQuery();
            this.cycle();
        };

        this.sleep = function() {
            for (var i = 0; i < this.components.length; i++) {
                var component = this.components[i];
                component.sleep();
            }
        };

        this.wake = function() {
            for (var i = 0; i < this.components.length; i++) {
                var component = this.components[i];
                component.wake();
            }
        };

        ////////////////////////////////////////////////////
        //  functions for working with the queries

        this.cloneQuery = function() {
            if (this.currentQuery) {
                return $.extend(true, {}, this.currentQuery);
            }
            return false;
        };

        this.pushQuery = function(query) {
            if (this.baseQuery) {
                query.merge(this.baseQuery);
            }
            this.currentQuery = query;
        };

        this.cloneBaseQuery = function() {
            if (this.baseQuery) {
                return $.extend(true, {}, this.baseQuery);
            }
            return es.newQuery();
        };

        this.cloneOpeningQuery = function() {
            if (this.openingQuery) {
                return $.extend(true, {}, this.openingQuery);
            }
            return es.newQuery();
        };

        ////////////////////////////////////////////////////
        // functions to handle the query lifecycle

        // execute the query and all the associated workflow
        // FIXME: could replace this with an async group for neatness
        this.doPrimaryQuery = function(callback) {
            var context = {"callback" : callback};

            this.queryAdapter.doQuery({
                edge: this,
                success: edges.objClosure(this, "querySuccess", ["result"], context),
                error: edges.objClosure(this, "queryFail", ["response"], context)
            });
        };

        this.queryFail = function(params) {
            var callback = params.callback;
            var response = params.response;
            this.trigger("edges:query-fail");
            if (response.hasOwnProperty("responseText")) {
                console.log("ERROR: query fail: " + response.responseText);
            }
            if (response.hasOwnProperty("error")) {
                console.log("ERROR: search execution fail: " + response.error);
            }
            callback();
        };

        this.querySuccess = function(params) {
            this.result = params.result;
            var callback = params.callback;

            // success trigger
            this.trigger("edges:query-success");
            callback();
        };

        this.runPreflightQueries = function(callback) {
            if (!this.preflightQueries || Object.keys(this.preflightQueries).length == 0) {
                callback();
                return;
            }

            this.trigger("edges:pre-preflight");

            var entries = [];
            var ids = Object.keys(this.preflightQueries);
            for (var i = 0; i < ids.length; i++) {
                var id = ids[i];
                entries.push({id: id, query: this.preflightQueries[id]});
            }

            var that = this;
            var pg = edges.newAsyncGroup({
                list: entries,
                action: function(params) {
                    var entry = params.entry;
                    var success = params.success_callback;
                    var error = params.error_callback;

                    es.doQuery({
                        search_url: that.search_url,
                        queryobj: entry.query.objectify(),
                        datatype: that.datatype,
                        success: success,
                        error: error
                    });
                },
                successCallbackArgs: ["result"],
                success: function(params) {
                    var result = params.result;
                    var entry = params.entry;
                    that.preflightResults[entry.id] = result;
                },
                errorCallbackArgs : ["result"],
                error:  function(params) {
                    that.trigger("edges:error-preflight");
                },
                carryOn: function() {
                    that.trigger("edges:post-preflight");
                    callback();
                }
            });

            pg.process();
        };

        this.runSecondaryQueries = function(callback) {
            this.realisedSecondaryQueries = {};
            if (!this.secondaryQueries || Object.keys(this.secondaryQueries).length == 0) {
                callback();
                return;
            }

            // generate the query objects to be executed
            var entries = [];
            for (var key in this.secondaryQueries) {
                var entry = {};
                entry["query"] = this.secondaryQueries[key](this);
                entry["id"] = key;
                entry["search_url"] = this.search_url;
                if (this.secondaryUrls !== false && this.secondaryUrls.hasOwnProperty(key)) {
                    entry["search_url"] = this.secondaryUrls[key]
                }
                entries.push(entry);
                this.realisedSecondaryQueries[key] = entry.query;
            }

            var that = this;
            var pg = edges.newAsyncGroup({
                list: entries,
                action: function(params) {
                    var entry = params.entry;
                    var success = params.success_callback;
                    var error = params.error_callback;

                    es.doQuery({
                        search_url: entry.search_url,
                        queryobj: entry.query.objectify(),
                        datatype: that.datatype,
                        success: success,
                        complete: false
                    });
                },
                successCallbackArgs: ["result"],
                success: function(params) {
                    var result = params.result;
                    var entry = params.entry;
                    that.secondaryResults[entry.id] = result;
                },
                errorCallbackArgs : ["result"],
                error:  function(params) {
                    // FIXME: not really sure what to do about this
                },
                carryOn: function() {
                    callback();
                }
            });

            pg.process();
        };

        ////////////////////////////////////////////////
        // various utility functions

        this.getComponent = function(params) {
            var id = params.id;
            for (var i = 0; i < this.components.length; i++) {
                var component = this.components[i];
                if (component.id === id) {
                    return component;
                }
            }
            return false;
        };

        // return components in the requested category
        this.category = function(cat) {
            var comps = [];
            for (var i = 0; i < this.components.length; i++) {
                var component = this.components[i];
                if (component.category === cat) {
                    comps.push(component);
                }
            }
            return comps;
        };

        this.getRenderPackObject = function(oname, params) {
            for (var i = 0; i < this.renderPacks.length; i++) {
                var rp = this.renderPacks[i];
                if (rp && rp.hasOwnProperty(oname)) {
                    return rp[oname](params);
                }
            }

        };

        // get the jquery object for the desired element, in the correct context
        // you should ALWAYS use this, rather than the standard jquery $ object
        this.jq = function(selector) {
            return $(selector, this.context);
        };

        this.trigger = function(event_name) {
            if (event_name in this.callbacks) {
                this.callbacks[event_name](this);
            }
            this.context.trigger(event_name);
        };

        /////////////////////////////////////////////////////
        // URL management functions

        this.getUrlParams = function() {
            return edges.getUrlParams();
        };

        this.urlQueryArg = function(objectify_options) {
            if (!objectify_options) {
                if (this.urlQueryOptions) {
                    objectify_options = this.urlQueryOptions
                } else {
                    objectify_options = {
                        include_query_string : true,
                        include_filters : true,
                        include_paging : true,
                        include_sort : true,
                        include_fields : false,
                        include_aggregations : false
                    }
                }
            }
            var q = JSON.stringify(this.currentQuery.objectify(objectify_options));
            var obj = {};
            obj[this.urlQuerySource] = encodeURIComponent(q);
            return obj;
        };

        this.fullQueryArgs = function() {
            var args = $.extend(true, {}, this.urlParams);
            $.extend(args, this.urlQueryArg());
            return args;
        };

        this.fullUrlQueryString = function() {
            return this._makeUrlQuery(this.fullQueryArgs())
        };

        this._makeUrlQuery = function(args) {
            var keys = Object.keys(args);
            var entries = [];
            for (var i = 0; i < keys.length; i++) {
                var key = keys[i];
                var val = args[key];
                entries.push(key + "=" + val);  // NOTE we do not escape - this should already be done
            }
            return entries.join("&");
        };

        this.fullUrl = function() {
            var args = this.fullQueryArgs();
            var fragment = "";
            if (args["#"]) {
                fragment = "#" + args["#"];
                delete args["#"];
            }
            var wloc = window.location.toString();
            var bits = wloc.split("?");
            var url = bits[0] + "?" + this._makeUrlQuery(args) + fragment;
            return url;
        };

        this.updateUrl = function() {
            var currentQs = window.location.search;
            var qs = "?" + this.fullUrlQueryString();

            if (currentQs === qs) {
                return; // no need to push the state
            }

            var url = new URL(window.location.href);
            url.search = qs;

            if (currentQs === "") {
                window.history.replaceState("", "", url.toString());
            } else {
                window.history.pushState("", "", url.toString());
            }
        };

        /////////////////////////////////////////////
        // static file management

        this.loadStaticsAsync = function(callback) {
            if (!this.staticFiles || this.staticFiles.length == 0) {
                this.trigger("edges:post-load-static");
                callback();
                return;
            }

            var that = this;
            var pg = edges.newAsyncGroup({
                list: this.staticFiles,
                action: function(params) {
                    var entry = params.entry;
                    var success = params.success_callback;
                    var error = params.error_callback;

                    var id = entry.id;
                    var url = entry.url;
                    var datatype = edges.getParam(entry.datatype, "text");

                    $.ajax({
                        type: "get",
                        url: url,
                        dataType: datatype,
                        success: success,
                        error: error
                    })
                },
                successCallbackArgs: ["data"],
                success: function(params) {
                    var data = params.data;
                    var entry = params.entry;
                    if (entry.processor) {
                        var processed = entry.processor({data : data});
                        that.resources[entry.id] = processed;
                        if (entry.opening) {
                            entry.opening({resource : processed, edge: that});
                        }
                    }
                    that.static[entry.id] = data;
                },
                errorCallbackArgs : ["data"],
                error:  function(params) {
                    that.errorLoadingStatic.push(params.entry.id);
                    that.trigger("edges:error-load-static");
                },
                carryOn: function() {
                    that.trigger("edges:post-load-static");
                    callback();
                }
            });

            pg.process();
        };

        /////////////////////////////////////////////
        // final bits of construction
        this.startup();
    },

    //////////////////////////////////////////////////
    // Asynchronous resource loading feature

    newAsyncGroup : function(params) {
        if (!params) { params = {} }
        return new edges.AsyncGroup(params);
    },
    AsyncGroup : function(params) {
        this.list = params.list;
        this.successCallbackArgs = params.successCallbackArgs;
        this.errorCallbackArgs = params.errorCallbackArgs;

        var action = params.action;
        var success = params.success;
        var carryOn = params.carryOn;
        var error = params.error;

        this.functions = {
            action: action,
            success: success,
            carryOn: carryOn,
            error: error
        };

        this.checkList = [];

        this.finished = false;

        this.construct = function(params) {
            for (var i = 0; i < this.list.length; i++) {
                this.checkList.push(0);
            }
        };

        this.process = function(params) {
            if (this.list.length == 0) {
                this.functions.carryOn();
            }

            for (var i = 0; i < this.list.length; i++) {
                var context = {index: i};

                var success_callback = edges.objClosure(this, "_actionSuccess", this.successCallbackArgs, context);
                var error_callback = edges.objClosure(this, "_actionError", this.successCallbackArgs, context);
                var complete_callback = false;

                this.functions.action({entry: this.list[i],
                    success_callback: success_callback,
                    error_callback: error_callback,
                    complete_callback: complete_callback
                });
            }
        };

        this._actionSuccess = function(params) {
            var index = params.index;
            delete params.index;

            params["entry"] = this.list[index];
            this.functions.success(params);
            this.checkList[index] = 1;

            if (this._isComplete()) {
                this._finalise();
            }
        };

        this._actionError = function(params) {
            var index = params.index;
            delete params.index;

            params["entry"] = this.list[index];
            this.functions.error(params);
            this.checkList[index] = -1;

            if (this._isComplete()) {
                this._finalise();
            }
        };

        this._actionComplete = function(params) {

        };

        this._isComplete = function() {
            return $.inArray(0, this.checkList) === -1;
        };

        this._finalise = function() {
            if (this.finished) {
                return;
            }
            this.finished = true;
            this.functions.carryOn();
        };

        ////////////////////////////////////////
        this.construct();
    },

    /////////////////////////////////////////////
    // Query adapter base class and core ES implementation

    newQueryAdapter : function(params) {
        if (!params) { params = {} }
        return edges.instantiate(edges.QueryAdapter, params);
    },
    QueryAdapter : function(params) {
        this.doQuery = function(params) {};
    },

    newESQueryAdapter : function(params) {
        if (!params) { params = {} }
        return edges.instantiate(edges.ESQueryAdapter, params);
    },
    ESQueryAdapter : function(params) {
        this.doQuery = function(params) {
            var edge = params.edge;
            var query = params.query;
            var success = params.success;
            var error = params.error;

            if (!query) {
                query = edge.currentQuery;
            }

            es.doQuery({
                search_url: edge.search_url,
                queryobj: query.objectify(),
                datatype: edge.datatype,
                success: success,
                error: error
            });
        };
    },

    /////////////////////////////////////////////
    // Base classes for the various kinds of components

    newRenderer : function(params) {
        if (!params) { params = {} }
        return new edges.Renderer(params);
    },
    Renderer : function(params) {
        this.component = params.component || false;
        this.init = function(component) {
            this.component = component
        };
        this.draw = function(component) {};
        this.sleep = function() {};
        this.wake = function() {}
    },

    newComponent : function(params) {
        if (!params) { params = {} }
        return new edges.Component(params);
    },
    Component : function(params) {
        this.id = params.id;
        this.renderer = params.renderer;
        this.category = params.category || "none";
        this.defaultRenderer = params.defaultRenderer || "newRenderer";

        this.init = function(edge) {
            // record a reference to the parent object
            this.edge = edge;
            this.context = this.edge.jq("#" + this.id);

            // set the renderer from default if necessary
            if (!this.renderer) {
                this.renderer = this.edge.getRenderPackObject(this.defaultRenderer);
            }
            if (this.renderer) {
                this.renderer.init(this);
            }
        };

        this.draw = function() {
            if (this.renderer) {
                this.renderer.draw();
            }
        };

        this.contrib = function(query) {};
        this.synchronise = function() {};

        this.sleep = function() {
            if (this.renderer) {
                this.renderer.sleep();
            }
        };

        this.wake = function() {
            if (this.renderer) {
                this.renderer.wake();
            }
        };

        // convenience method for any renderer rendering a component
        this.jq = function(selector) {
            return this.edge.jq(selector);
        }
    },

    newSelector : function(params) {
        if (!params) { params = {} }
        edges.Selector.prototype = edges.newComponent(params);
        return new edges.Selector(params);
    },
    Selector : function(params) {
        // field upon which to build the selector
        this.field = params.field;

        // display name for the UI
        this.display = params.display || this.field;

        // whether the facet should be displayed at all (e.g. you may just want the data for a callback)
        this.active = params.active || true;

        // whether the facet should be acted upon in any way.  This might be useful if you want to enable/disable facets under different circumstances via a callback
        this.disabled = params.disabled || false;

        this.category = params.category || "selector";
    },

    newTemplate : function(params) {
        if (!params) { params = {} }
        return new edges.Template(params);
    },
    Template : function(params) {
        this.draw = function(edge) {}
    },

    newNestedEdge : function(params) {
        if (!params) { params = {}}
        params.category = params.category || "edge";
        params.renderer = false;
        params.defaultRenderer = false;
        return edges.instantiate(edges.NestedEdge, params, edges.newComponent)
    },
    NestedEdge : function(params) {
        this.constructOnInit = edges.getParam(params.constructOnInit, false);

        this.constructArgs = edges.getParam(params.constructArgs, {});

        this.inner = false;

        this.init = function(edge) {
            this.edge = edge;
            if (this.constructOnInit) {
                this.construct_and_bind();
            }
        };

        this.setConstructArg = function(key, value) {
            this.constructArgs[key] = value;
        };

        this.getConstructArg = function(key, def) {
            if (this.constructArgs.hasOwnProperty(key)) {
                return this.constructArgs[key];
            }
            return def;
        };

        this.construct_and_bind = function() {
            this.construct();
            if (this.inner) {
                this.inner.outer = this;
            }
        };

        this.construct = function() {};

        this.destroy = function() {
            if (this.inner) {
                this.inner.context.empty();
                this.inner.context.hide();
            }
            this.inner = false;
        };

        this.sleep = function() {
            this.inner.sleep();
            this.inner.context.hide();
        };

        this.wake = function() {
            if (this.inner) {
                this.inner.context.show();
                this.inner.wake();
            } else {
                this.construct_and_bind();
            }
        }
    },

    ///////////////////////////////////////////////////////////
    // Object construction tools

    // instantiate an object with the parameters and the (optional)
    // prototype
    instantiate : function(clazz, params, protoConstructor) {
        if (!params) { params = {} }
        if (protoConstructor) {
            clazz.prototype = protoConstructor(params);
        }
        var inst = new clazz(params);
        if (protoConstructor) {
            inst.__proto_constructor__ = protoConstructor;
        }
        return inst;
    },

    // call a method on the parent class
    up : function(inst, fn, args) {
        var parent = new inst.__proto_constructor__();
        parent[fn].apply(inst, args);
    },

    //////////////////////////////////////////////////////////////////
    // Closures for integrating the object with other modules

    // returns a function that will call the named function (fn) on
    // a specified object instance (obj), with all "arguments"
    // supplied to the closure by the caller
    //
    // if the args property is specified here, instead a parameters object
    // will be constructed with a one to one mapping between the names in args
    // and the values in the "arguments" supplied to the closure, until all
    // values in "args" are exhausted.
    //
    // so, for example,
    //
    // objClosure(this, "function")(arg1, arg2, arg3)
    // results in a call to
    // this.function(arg1, arg2, arg3, ...)
    //
    // and
    // objClosure(this, "function", ["one", "two"])(arg1, arg2, arg3)
    // results in a call to
    // this.function({one: arg1, two: arg2})
    //
    objClosure : function(obj, fn, args, context_params) {
        return function() {
            if (args) {
                var params = {};
                for (var i = 0; i < args.length; i++) {
                    if (arguments.length > i) {
                        params[args[i]] = arguments[i];
                    }
                }
                if (context_params) {
                    params = $.extend(params, context_params);
                }
                obj[fn](params);
            } else {
                var slice = Array.prototype.slice;
                var theArgs = slice.apply(arguments);
                if (context_params) {
                    theArgs.push(context_params);
                }
                obj[fn].apply(obj, theArgs);
            }
        }
    },

    // returns a function that is suitable for triggering by an event, and which will
    // call the specified function (fn) on the specified object (obj) with the element
    // which fired the event as the argument
    //
    // if "conditional" is specified, this is a function (which can take the event as an argument)
    // which is called to determine whether the event will propagate to the object function.
    //
    // so, for example
    //
    // eventClosure(this, "handler")(event)
    // results in a call to
    // this.handler(element)
    //
    // and
    //
    // eventClosure(this, "handler", function(event) { return event.type === "click" })(event)
    // results in a call (only in the case that the event is a click), to
    // this.handler(element)
    //
    eventClosure : function(obj, fn, conditional, preventDefault) {
        if (preventDefault === undefined) {
            preventDefault = true;
        }
        return function(event) {
            if (conditional) {
                if (!conditional(event)) {
                    return;
                }
            }
            if (preventDefault) {
                event.preventDefault();
            }
            obj[fn](this, event);
        }
    },

    //////////////////////////////////////////////////////////////////
    // CSS normalising/canonicalisation tools

    css_classes : function(namespace, field, renderer) {
        var cl = namespace + "-" + field;
        if (renderer) {
            cl += " " + cl + "-" + renderer.component.id;
        }
        return cl;
    },

    css_class_selector : function(namespace, field, renderer) {
        var sel = "." + namespace + "-" + field;
        if (renderer) {
            sel += sel + "-" + renderer.component.id;
        }
        return sel;
    },

    css_id : function(namespace, field, renderer) {
        var id = namespace + "-" + field;
        if (renderer) {
            id += "-" + renderer.component.id;
        }
        return id;
    },

    css_id_selector : function(namespace, field, renderer) {
        return "#" + edges.css_id(namespace, field, renderer);
    },

    //////////////////////////////////////////////////////////////////
    // Event binding utilities

    on : function(selector, event, caller, targetFunction, delay, conditional, preventDefault) {
        if (preventDefault === undefined) {
            preventDefault = true;
        }
        // if the caller has an inner component (i.e. it is a Renderer), use the component's id
        // otherwise, if it has a namespace (which is true of Renderers or Templates) use that
        if (caller.component && caller.component.id) {
            event = event + "." + caller.component.id;
        } else if (caller.namespace) {
            event = event + "." + caller.namespace;
        }

        // create the closure to be called on the event
        var clos = edges.eventClosure(caller, targetFunction, conditional, preventDefault);

        // now bind the closure directly or with delay
        // if the caller has an inner component (i.e. it is a Renderer) use the components jQuery selector
        // otherwise, if it has an inner, use the selector on that.
        if (delay) {
            if (caller.component) {
                caller.component.jq(selector).bindWithDelay(event, clos, delay);
            } else if (caller.edge) {
                caller.edge.jq(selector).bindWithDelay(event, clos, delay);
            } else {
                $(selector).bindWithDelay(event, clos, delay);
            }
        } else {
            if (caller.component) {
                var element = caller.component.jq(selector);
                element.off(event);
                element.on(event, clos);
            } else if (caller.edge) {
                var element = caller.edge.jq(selector);
                element.off(event);
                element.on(event, clos);
            } else {
                var element = $(selector);
                element.off(event);
                element.on(event, clos);
            }
        }
    },

    off : function(selector, event, caller) {
        // if the caller has an inner component (i.e. it is a Renderer), use the component's id
        // otherwise, if it has a namespace (which is true of Renderers or Templates) use that
        if (caller.component && caller.component.id) {
            event = event + "." + caller.component.id;
        } else if (caller.namespace) {
            event = event + "." + caller.namespace;
        }

        if (caller.component) {
            var element = caller.component.jq(selector);
            element.off(event);
        } else if (caller.edge) {
            var element = caller.edge.jq(selector);
            element.off(event);
        } else {
            var element = $(selector);
            element.off(event);
        }
    },

    //////////////////////////////////////////////////////////////////
    // Shared utilities

    getUrlParams : function() {
        var params = {};
        var url = window.location.href;
        var fragment = false;

        // break the anchor off the url
        if (url.indexOf("#") > -1) {
            fragment = url.slice(url.indexOf('#'));
            url = url.substring(0, url.indexOf('#'));
        }

        // extract and split the query args
        var args = url.slice(url.indexOf('?') + 1).split('&');

        for (var i = 0; i < args.length; i++) {
            var kv = args[i].split('=');
            if (kv.length === 2) {
                var key = kv[0].replace(/\+/g, "%20");
                key = decodeURIComponent(key);
                var val = kv[1].replace(/\+/g, "%20");
                val = decodeURIComponent(val);
                if (val[0] == "[" || val[0] == "{") {
                    // if it looks like a JSON object in string form...
                    // remove " (double quotes) at beginning and end of string to make it a valid
                    // representation of a JSON object, or the parser will complain
                    val = val.replace(/^"/,"").replace(/"$/,"");
                    val = JSON.parse(val);
                }
                params[key] = val;
            }
        }

        // record the fragment identifier if required
        if (fragment) {
            params['#'] = fragment;
        }

        return params;
    },

    escapeHtml : function(unsafe, def) {
        if (def === undefined) {
            def = "";
        }
        if (unsafe === undefined || unsafe == null) {
            return def;
        }
        try {
            if (typeof unsafe.replace !== "function") {
                return unsafe
            }
            return unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        } catch(err) {
            return def;
        }
    },

    /**
     * Determine if the object has a property at the given path in the object
     *
     * @param obj
     * @param path
     * @returns {boolean}
     */
    hasProp : function(obj, path) {
        var bits = path.split(".");
        var ctx = obj;
        for (var i = 0; i < bits.length; i++) {
            if (!ctx.hasOwnProperty(bits[i])) {
                return false;
            }
            ctx = ctx[bits[i]];
        }
        return true;
    },

    /**
     * Get the value of an element at the given path in an object
     *
     * @param path
     * @param rec
     * @param def
     * @returns {*}
     */
    objVal : function(path, rec, def) {
        if (def === undefined) {
            def = false;
        }
        var bits = path.split(".");
        var val = rec;
        for (var i = 0; i < bits.length; i++) {
            var field = bits[i];
            if (field in val) {
                val = val[field];
            } else {
                return def;
            }
        }
        return val;
    },

    /**
     * The same as objVal but will handle arrays at every level and condense the
     * results into a single array result.  Always returns an array, even if it is
     * a single result, OR returns a default, which is returned exactly as specified
     *
     * @param path
     * @param rec
     * @param def
     * @returns {*}
     */
    objVals : function(path, rec, def) {
        if (def === undefined) { def = false; }

        var bits = path.split(".");
        var contexts = [rec];

        for (var i = 0; i < bits.length; i++) {
            var pathElement = bits[i];
            var nextContexts = [];
            for (var j = 0; j < contexts.length; j++) {
                var context = contexts[j];
                if (pathElement in context) {
                    var nextLevel = context[pathElement];
                    if (i === bits.length - 1) {
                        // if this is the last path element, then
                        // we make the assumption that this is a well defined leaf node, for performance purposes
                        nextContexts.push(nextLevel);
                    } else {
                        // there are more path elements to retrieve, so we have to handle the various types
                        if ($.isArray(nextLevel)) {
                            nextContexts = nextContexts.concat(nextLevel);
                        } else if ($.isPlainObject(nextLevel)) {
                            nextContexts.push(nextLevel);
                        }
                        // if the value is a leaf node already then we throw it away
                    }
                }
            }
            contexts = nextContexts;
        }

        if (contexts.length === 0) {
            return def;
        }
        return contexts;
    },

    getParam : function(value, def) {
        return value !== undefined ? value : def;
    },

    safeId : function(unsafe) {
        return unsafe.replace(/&/g, "_")
                .replace(/</g, "_")
                .replace(/>/g, "_")
                .replace(/"/g, "_")
                .replace(/'/g, "_")
                .replace(/\./gi,'_')
                .replace(/\:/gi,'_')
                .replace(/\s/gi,"_");
    },

    numFormat : function(params) {
        var reflectNonNumbers = edges.getParam(params.reflectNonNumbers, false);
        var prefix = edges.getParam(params.prefix, "");
        var zeroPadding = edges.getParam(params.zeroPadding, false);
        var decimalPlaces = edges.getParam(params.decimalPlaces, false);
        var thousandsSeparator = edges.getParam(params.thousandsSeparator, false);
        var decimalSeparator = edges.getParam(params.decimalSeparator, ".");
        var suffix = edges.getParam(params.suffix, "");

        return function(number) {
            // ensure this is really a number
            var num = parseFloat(number);
            if (isNaN(num)) {
                if (reflectNonNumbers) {
                    return number;
                } else {
                    return num;
                }
            }

            // first off we need to convert the number to a string, which we can do directly, or using toFixed if that
            // is suitable here
            if (decimalPlaces !== false) {
                num = num.toFixed(decimalPlaces);
            } else {
                num  = num.toString();
            }

            // now "num" is a string containing the formatted number that we can work on

            var bits = num.split(".");

            if (zeroPadding !== false) {
                var zeros = zeroPadding - bits[0].length;
                var pad = "";
                for (var i = 0; i < zeros; i++) {
                    pad += "0";
                }
                bits[0] = pad + bits[0];
            }

            if (thousandsSeparator !== false) {
                bits[0] = bits[0].replace(/\B(?=(\d{3})+(?!\d))/g, thousandsSeparator);
            }

            if (bits.length == 1) {
                return prefix + bits[0] + suffix;
            } else {
                return prefix + bits[0] + decimalSeparator + bits[1] + suffix;
            }
        }
    },

    numParse : function(params) {
        var commaRx = new RegExp(",", "g");

        return function(num) {
            num = num.trim();
            num = num.replace(commaRx, "");
            if (num === "") {
                return 0.0;
            }
            return parseFloat(num);
        }
    },

    isEmptyObject: function(obj) {
        for(var key in obj) {
            if(obj.hasOwnProperty(key))
                return false;
        }
        return true;
    }
};

$.extend(edges, {
    //////////////////////////////////////////////////
    // Arbitrary filter-selector

    newFilterSetter : function(params) {
        if (!params) { params = {} }
        edges.FilterSetter.prototype = edges.newComponent(params);
        return new edges.FilterSetter(params);
    },
    FilterSetter : function(params) {
        /*
        [
            {
                id : "<identifier for this filter within the scope of this component>",
                display: "<How this filter should be described in the UI>",
                must : [<list of query object filters to be applied/removed if this filter is selected/removed>],
                agg_name : "<name of aggregation which informs this filter (defined in this.aggregations)>",
                bucket_field : "<field in the bucket to look in>",
                bucket_value: "<value in the bucket_field to match>"
            }
        ]
        */
        this.filters = edges.getParam(params.filters, []);

        this.aggregations = edges.getParam(params.aggregations, []);

        this.defaultRenderer = edges.getParam(params.defaultRenderer, "newFilterSetterRenderer");

        //////////////////////////////////////////
        // properties used to store internal state

        // map of filter id to document count from aggregation
        this.filter_counts = {};

        // map of filter id to whether it is active or not
        this.active_filters = {};

        //////////////////////////////////////////
        // overrides on the parent object's standard functions

        this.contrib = function(query) {
            for (var i = 0; i < this.aggregations.length; i++) {
                query.addAggregation(this.aggregations[i]);
            }
        };

        this.synchronise = function() {
            // first pull the count information from the aggregations
            for (var i = 0; i < this.filters.length; i++) {
                var filter_def = this.filters[i];

                if (!filter_def.agg_name || !filter_def.bucket_field || !filter_def.bucket_value) {
                    continue;
                }

                var agg = this.edge.result.aggregation(filter_def.agg_name);
                if (!agg) {
                    continue;
                }

                var bfield = filter_def.bucket_field;
                var bvalue = filter_def.bucket_value;
                var count = 0;

                var buckets = agg.buckets;
                for (var k = 0; k < buckets.length; k++) {
                    var bucket = buckets[k];
                    if (bucket[bfield] && bucket[bfield] == bvalue) {
                        count = bucket["doc_count"];
                        break;
                    }
                }

                this.filter_counts[filter_def.id] = count;
            }

            // now extract all the existing filters to find out if any of ours are active
            for (var i = 0; i < this.filters.length; i++) {
                var filter_def = this.filters[i];
                if (!filter_def.must) {
                    continue;
                }

                var toactivate = filter_def.must.length;
                var active = 0;
                for (var j = 0; j < filter_def.must.length; j++) {
                    var must = filter_def.must[j];
                    var current = this.edge.currentQuery.listMust(must);
                    if (current.length > 0) {
                        active += 1;
                    }
                }
                if (active === toactivate) {
                    this.active_filters[filter_def.id] = true;
                } else {
                    this.active_filters[filter_def.id] = false;
                }
            }
        };

        //////////////////////////////////////////
        // functions that can be called on this component to change its state

        this.addFilter = function(filter_id) {
            var filter = false;
            for (var i = 0; i < this.filters.length; i++) {
                if (this.filters[i].id === filter_id) {
                    filter = this.filters[i];
                    break;
                }
            }

            if (!filter || !filter.must) {
                return;
            }

            var nq = this.edge.cloneQuery();

            // add all of the must filters to the query
            for (var i = 0; i < filter.must.length; i++) {
                var must = filter.must[i];
                nq.addMust(must);
            }

            // reset the search page to the start and then trigger the next query
            nq.from = 0;
            this.edge.pushQuery(nq);
            this.edge.doQuery();
        };

        this.removeFilter = function(filter_id) {
            var filter = false;
            for (var i = 0; i < this.filters.length; i++) {
                if (this.filters[i].id === filter_id) {
                    filter = this.filters[i];
                    break;
                }
            }

            if (!filter || !filter.must) {
                return;
            }

            var nq = this.edge.cloneQuery();

            // add all of the must filters to the query
            for (var i = 0; i < filter.must.length; i++) {
                var must = filter.must[i];
                nq.removeMust(must);
            }

            // reset the search page to the start and then trigger the next query
            nq.from = 0;
            this.edge.pushQuery(nq);
            this.edge.doQuery();
        };
    },

    //////////////////////////////////////////////////
    // Search controller implementation and supporting search navigation/management

    newFullSearchController: function (params) {
        if (!params) {
            params = {}
        }
        edges.FullSearchController.prototype = edges.newComponent(params);
        return new edges.FullSearchController(params);
    },
    FullSearchController: function (params) {
        // if set, should be either * or ~
        // if *, * will be prepended and appended to each string in the freetext search term
        // if ~, ~ then ~ will be appended to each string in the freetext search term.
        // If * or ~ or : are already in the freetext search term, no action will be taken.
        this.fuzzify = params.fuzzify || false;

        // list of options by which the search results can be sorted
        // of the form of a list, thus: [{ field: '<field to sort by>', dir: "<sort dir>", display: '<display name>'}],
        this.sortOptions = params.sortOptions || false;

        // list of options for fields to which free text search can be constrained
        // of the form of a list thus: [{ field: '<field to search on>', display: '<display name>'}],
        this.fieldOptions = params.fieldOptions || false;

        // provide a function which will do url shortening for the share/save link
        this.urlShortener = params.urlShortener || false;

        // function to generate an embed snippet
        this.embedSnippet = edges.getParam(params.embedSnippet, false);

        // on free-text search, default operator for the elasticsearch query system to use
        this.defaultOperator = params.defaultOperator || "OR";

        this.defaultRenderer = params.defaultRenderer || "newFullSearchControllerRenderer";

        ///////////////////////////////////////////////
        // properties for tracking internal state

        // field on which to focus the freetext search (initially)
        this.searchField = false;

        // freetext search string
        this.searchString = false;

        this.sortBy = false;

        this.sortDir = "desc";

        // the short url for the current search, if it has been generated
        this.shortUrl = false;

        this.synchronise = function () {
            // reset the state of the internal variables
            this.searchString = false;
            this.searchField = false;
            this.sortBy = false;
            this.sortDir = "desc";
            this.shortUrl = false;

            if (this.edge.currentQuery) {
                var qs = this.edge.currentQuery.getQueryString();
                if (qs) {
                    this.searchString = qs.queryString;
                    this.searchField = qs.defaultField;
                }
                var sorts = this.edge.currentQuery.getSortBy();
                if (sorts.length > 0) {
                    this.sortBy = sorts[0].field;
                    this.sortDir = sorts[0].order;
                }
            }
        };

        this.setSort = function(params) {
            var dir = params.dir;
            var field = params.field;

            if (dir === undefined || dir === false) {
                dir = "desc";
            }

            var nq = this.edge.cloneQuery();

            // replace the existing sort criteria
            nq.setSortBy(es.newSort({
                field: field,
                order: dir
            }));

            // reset the search page to the start and then trigger the next query
            nq.from = 0;
            this.edge.pushQuery(nq);
            this.edge.doQuery();
        };

        this.changeSortDir = function () {
            var dir = this.sortDir === "asc" ? "desc" : "asc";
            var sort = this.sortBy ? this.sortBy : "_score";
            var nq = this.edge.cloneQuery();

            // replace the existing sort criteria
            nq.setSortBy(es.newSort({
                field: sort,
                order: dir
            }));

            // reset the search page to the start and then trigger the next query
            nq.from = 0;
            this.edge.pushQuery(nq);
            this.edge.doQuery();
        };

        this.setSortBy = function (field) {
            var nq = this.edge.cloneQuery();

            // replace the existing sort criteria
            if (!field || field === "") {
                field = "_score";
            }
            nq.setSortBy(es.newSort({
                field: field,
                order: this.sortDir
            }));

            // reset the search page to the start and then trigger the next query
            nq.from = 0;
            this.edge.pushQuery(nq);
            this.edge.doQuery();
        };

        this.setSearchField = function (field, cycle) {
            if (cycle === undefined) {
                cycle = true;
            }

            // track the search field, as this may not trigger a search
            this.searchField = field;
            if (!this.searchString || this.searchString === "") {
                return;
            }

            var nq = this.edge.cloneQuery();

            // set the query with the new search field
            nq.setQueryString(es.newQueryString({
                queryString: this.searchString,
                defaultField: field,
                defaultOperator: this.defaultOperator,
                fuzzify: this.fuzzify
            }));

            // reset the search page to the start and then trigger the next query
            nq.from = 0;
            this.edge.pushQuery(nq);
            if (cycle) {
                this.edge.doQuery();
            } else {
                this.searchField = field;
            }
        };

        this.setSearchText = function (text, cycle) {
            if (cycle === undefined) {
                cycle = true;
            }

            var nq = this.edge.cloneQuery();

            if (text !== "") {
                var params = {
                    queryString: text,
                    defaultOperator: this.defaultOperator,
                    fuzzify: this.fuzzify
                };
                if (this.searchField && this.searchField !== "") {
                    params["defaultField"] = this.searchField;
                }
                // set the query with the new search field
                nq.setQueryString(es.newQueryString(params));
            } else {
                nq.removeQueryString();
            }

            // reset the search page to the start and then trigger the next query
            nq.from = 0;
            this.edge.pushQuery(nq);
            if (cycle) {
                this.edge.doQuery();
            } else {
                this.searchString = text;
            }
        };

        this.clearSearch = function () {
            this.edge.reset();
        };

        this.generateShortUrl = function(callback) {
            var query = this.edge.currentQuery.objectify({
                include_query_string : true,
                include_filters : true,
                include_paging : true,
                include_sort : true,
                include_fields : false,
                include_aggregations : false
            });
            var success_callback = edges.objClosure(this, "setShortUrl", false, callback);
            var error_callback = function() {};
            this.urlShortener(query, success_callback, error_callback);
        };

        this.setShortUrl = function(short_url, callback) {
            if (short_url) {
                this.shortUrl = short_url;
            } else {
                this.shortUrl = false;
            }
            callback();
        };
    },

    newSelectedFilters: function (params) {
        if (!params) {
            params = {}
        }
        edges.SelectedFilters.prototype = edges.newComponent(params);
        return new edges.SelectedFilters(params);
    },
    SelectedFilters: function (params) {
        //////////////////////////////////////////
        // configuration options to be passed in

        // mapping from fields to names to display them as
        // if these come from a facet/selector, they should probably line up
        this.fieldDisplays = edges.getParam(params.fieldDisplays, {});

        // constraints that consist of multiple filters that we want to treat as a single
        // one {"filters" : [<es filter templates>], "display" : "...." }
        this.compoundDisplays = edges.getParam(params.compoundDisplays, []);

        // value maps on a per-field basis for Term(s) filters, to apply to values before display.
        // if these come from a facet/selector, they should probably be the same maps
        // {"<field>" : {"<value>" : "<display>"}}
        this.valueMaps = edges.getParam(params.valueMaps, {});

        // value functions on a per-field basis for Term(s) filters, to apply to values before display.
        // if these come from a facet/selector, they should probably be the same functions
        // {"<field>" : <function>}
        this.valueFunctions = edges.getParam(params.valueFunctions, {});

        // range display maps on a per-field basis for Range filters
        // if these come from a facet/selector, they should probably be the same maps
        // {"<field>" : [{"from" : "<from>", "to" : "<to>", "display" : "<display>"}]}
        this.rangeMaps = edges.getParam(params.rangeMaps, {});

        // range display functions on a per-field basis for Range filters
        // useful if you have a range selector which allows arbitrary ranges
        // {"<field>" : <function (receives field name, from and to as params dict)>}
        // must return {to: to, from: from, display: display}
        this.rangeFunctions = edges.getParam(params.rangeFunctions, {});

        // function to use to format any range that does not appear in the range maps
        this.formatUnknownRange = edges.getParam(params.formatUnknownRange, false);

        // if we get a filter for a field we have no config for, should we ignore it?
        this.ignoreUnknownFilters = edges.getParam(params.ignoreUnknownFilters, false);

        // override the parent's default renderer
        this.defaultRenderer = edges.getParam(params.defaultRenderer, "newSelectedFiltersRenderer");

        //////////////////////////////////////////
        // properties used to store internal state

        // active filters to be rendered out
        // each of the form:
        /*
         {
         filter : "<type name of filter used>"
         display: "<field display name>",
         rel: "<relationship between values (e.g. AND, OR)>",
         values: [
         {display: "<display value>", val: "<actual value>"}
         ]
         }
         */
        this.mustFilters = {};

        this.searchString = false;
        this.searchField = false;

        this.synchronise = function () {
            // reset the state of the internal variables
            this.mustFilters = {};
            this.searchString = false;
            this.searchField = false;

            if (!this.edge.currentQuery) {
                return;
            }

            // first see if we can detect all the compound filters and record them
            var inCompound = [];
            for (var i = 0; i < this.compoundDisplays.length; i++) {
                var cd = this.compoundDisplays[i];
                var count = 0;
                var fieldNames = [];
                for (var j = 0; j < cd.filters.length; j++) {
                    var filt = cd.filters[j];
                    var existing = this.edge.currentQuery.listMust(filt);
                    if (existing.length > 0) {
                        count++;
                        fieldNames.push(filt.field);
                    }
                }
                if (count === cd.filters.length) {
                    inCompound.concat(fieldNames);
                    this.mustFilters["compound_" + i] = {
                        filter: "compound",
                        display: cd.display,
                        query_filters: cd.filters
                    };
                }
            }

            // now pull out all the single type queries
            var musts = this.edge.currentQuery.listMust();
            for (var i = 0; i < musts.length; i++) {
                var f = musts[i];
                if (this.ignoreUnknownFilters && !(f.field in this.fieldDisplays) && $.inArray(f.field, inCompound) === -1) {
                    continue;
                }
                if (f.type_name === "term") {
                    this._synchronise_term(f);
                } else if (f.type_name === "terms") {
                    this._synchronise_terms(f);
                } else if (f.type_name === "range") {
                    this._synchronise_range(f);
                } else if (f.type_name === "geo_distance_range") {

                }
            }

            var qs = this.edge.currentQuery.getQueryString();
            if (qs) {
                this.searchString = qs.queryString;
                this.searchField = qs.defaultField;
            }
        };

        this.removeCompoundFilter = function(params) {
            var compound_id = params.compound_id;
            var filts = this.mustFilters[compound_id].query_filters;

            var nq = this.edge.cloneQuery();

            for (var i = 0; i < filts.length; i++) {
                var filt = filts[i];
                nq.removeMust(filt);
            }

            // reset the page to zero and reissue the query
            nq.from = 0;
            this.edge.pushQuery(nq);
            this.edge.doQuery();
        };

        this.removeFilter = function (boolType, filterType, field, value) {
            var nq = this.edge.cloneQuery();

            if (filterType === "term") {
                var template = es.newTermFilter({field: field, value: value});

                if (boolType === "must") {
                    nq.removeMust(template);
                }

            } else if (filterType === "terms") {
                var template = es.newTermsFilter({field: field});

                if (boolType === "must") {
                    var filters = nq.listMust(template);
                    for (var i = 0; i < filters.length; i++) {
                        if (filters[i].has_term(value)) {
                            filters[i].remove_term(value);
                        }

                        // if this means the filter no longer has values, remove the filter
                        if (!filters[i].has_terms()) {
                            nq.removeMust(filters[i]);
                        }
                    }
                }

            } else if (filterType == "range") {
                var params = {field: field};
                if (value.to) {
                    params[value.toType] = value.to;
                }
                if (value.from) {
                    params[value.fromType] = value.from;
                }
                var template = es.newRangeFilter(params);

                if (boolType === "must") {
                    nq.removeMust(template);
                }

            } else if (filterType == "geo_distance_range") {

            }

            // reset the page to zero and reissue the query
            nq.from = 0;
            this.edge.pushQuery(nq);
            this.edge.doQuery();
        };

        this.clearQueryString = function () {
            var nq = this.edge.cloneQuery();
            nq.removeQueryString();

            // reset the search page to the start and then trigger the next query
            nq.from = 0;
            this.edge.pushQuery(nq);
            this.edge.doQuery();
        };

        this.clearSearch = function () {
            this.edge.reset();
        };

        this._synchronise_term = function (filter) {
            var display = this.fieldDisplays[filter.field] || filter.field;

            // multiple term filters mean AND, so group them together here
            if (filter.field in this.mustFilters) {
                this.mustFilters[filter.field].values.push({
                    val: filter.value,
                    display: this._translate(filter.field, filter.value)
                })
            } else {
                this.mustFilters[filter.field] = {
                    filter: filter.type_name,
                    display: display,
                    values: [{val: filter.value, display: this._translate(filter.field, filter.value)}],
                    rel: "AND"
                }
            }
        };

        this._synchronise_terms = function (filter) {
            var display = this.fieldDisplays[filter.field] || filter.field;
            var values = [];
            for (var i = 0; i < filter.values.length; i++) {
                var v = filter.values[i];
                var d = this._translate(filter.field, v);
                values.push({val: v, display: d});
            }
            this.mustFilters[filter.field] = {
                filter: filter.type_name,
                display: display,
                values: values,
                rel: "OR"
            }
        };

        this._synchronise_range = function (filter) {
            var display = this.fieldDisplays[filter.field] || filter.field;

            var to = filter.lt;
            var toType = "lt";
            if (to === false) {
                to = filter.lte;
                toType = "lte";
            }

            var from = filter.gte;
            var fromType = "gte";
            if (from === false) {
                from = filter.gt;
                fromType = "gt";
            }

            var r = this._getRangeDef(filter.field, from, to);
            var values = [];
            if (!r) {
                values.push({to: to, toType: toType, from: from, fromType: fromType, display: this._formatUnknown(from, to)});
            } else {
                values.push(r);
            }

            this.mustFilters[filter.field] = {
                filter: filter.type_name,
                display: display,
                values: values
            }
        };

        this._translate = function (field, value) {
            if (field in this.valueMaps) {
                if (value in this.valueMaps[field]) {
                    return this.valueMaps[field][value];
                }
            } else if (field in this.valueFunctions) {
                return this.valueFunctions[field](value);
            }
            return value;
        };

        this._getRangeDef = function (field, from, to) {
            if (!this.rangeMaps[field] && !this.rangeFunctions[field]) {
                return false;
            }
            if (this.rangeMaps[field]) {
                for (var i = 0; i < this.rangeMaps[field].length; i++) {
                    var r = this.rangeMaps[field][i];
                    var frMatch = true;
                    var toMatch = true;
                    // if one is set and the other not, no match
                    if ((from && !r.from) || (!from && r.from)) {
                        frMatch = false;
                    }
                    if ((to && !r.to) || (!to && r.to)) {
                        toMatch = false;
                    }

                    // if both set, and they don't match, no match
                    if (from && r.from && from !== r.from) {
                        frMatch = false;
                    }
                    if (to && r.to && to !== r.to) {
                        toMatch = false;
                    }

                    // both have to match for a match
                    if (frMatch && toMatch) {
                        return r
                    }
                }
            } else if (this.rangeFunctions[field]) {
                var fn = this.rangeFunctions[field];
                return fn({field: field, from: from, to: to});
            }

            return false;
        };

        this._formatUnknown = function (from, to) {
            if (this.formatUnknownRange) {
                return this.formatUnknownRange(from, to)
            } else {
                // if they're the same just return one of them
                if (from !== false || to !== false) {
                    if (from === to) {
                        return from;
                    }
                }

                // otherwise calculate the display for the range
                var frag = "";
                if (from !== false) {
                    frag += from;
                } else {
                    frag += "< ";
                }
                if (to !== false) {
                    if (from !== false) {
                        frag += " - " + to;
                    } else {
                        frag += to;
                    }
                } else {
                    if (from !== false) {
                        frag += "+";
                    } else {
                        frag = "unknown";
                    }
                }
                return frag;
            }
        };
    },

    newPager: function (params) {
        if (!params) {
            params = {}
        }
        edges.Pager.prototype = edges.newComponent(params);
        return new edges.Pager(params);
    },
    Pager: function (params) {

        this.defaultRenderer = params.defaultRenderer || "newPagerRenderer";

        ///////////////////////////////////////
        // internal state

        this.from = false;
        this.to = false;
        this.total = false;
        this.page = false;
        this.pageSize = false;
        this.totalPages = false;

        this.synchronise = function () {
            // reset the state of the internal variables
            this.from = false;
            this.to = false;
            this.total = false;
            this.page = false;
            this.pageSize = false;
            this.totalPages = false;

            // calculate the properties based on the latest query/results
            if (this.edge.currentQuery) {
                this.from = parseInt(this.edge.currentQuery.getFrom()) + 1;
                this.pageSize = parseInt(this.edge.currentQuery.getSize());
            }
            if (this.edge.result) {
                this.total = this.edge.result.total()
            }
            if (this.from !== false && this.total !== false) {
                this.to = this.from + this.pageSize - 1;
                this.page = Math.ceil((this.from - 1) / this.pageSize) + 1;
                this.totalPages = Math.ceil(this.total / this.pageSize)
            }
        };

        this.setFrom = function (from) {
            var nq = this.edge.cloneQuery();

            from = from - 1; // account for the human readability of the value, ES is 0 indexed here
            if (from < 0) {
                from = 0;
            }
            nq.from = from;

            this.edge.pushQuery(nq);
            this.edge.doQuery();
        };

        this.setSize = function (size) {
            var nq = this.edge.cloneQuery();
            nq.size = size;
            this.edge.pushQuery(nq);
            this.edge.doQuery();
        };

        this.decrementPage = function () {
            var from = this.from - this.pageSize;
            this.setFrom(from);
        };

        this.incrementPage = function () {
            var from = this.from + this.pageSize;
            this.setFrom(from);
        };

        this.goToPage = function(params) {
            var page = params.page;
            var nf = ((page - 1) * this.pageSize) + 1;  // we're working with the human notion of from, here, so is indexed from 1
            this.setFrom(nf);
        }
    },

    newSearchingNotification: function (params) {
        if (!params) {
            params = {}
        }
        edges.SearchingNotification.prototype = edges.newComponent(params);
        return new edges.SearchingNotification(params);
    },
    SearchingNotification: function (params) {
        this.defaultRenderer = params.defaultRenderer || "newSearchingNotificationRenderer";

        this.finishedEvent = edges.getParam(params.finishedEvent, "edges:query-success");

        this.searching = false;

        this.init = function (edge) {
            Object.getPrototypeOf(this).init.call(this, edge);
            // this.__proto__.init.call(this, edge);
            edge.context.on("edges:pre-query", edges.eventClosure(this, "searchingBegan"));
            edge.context.on("edges:query-fail", edges.eventClosure(this, "searchingFinished"));
            edge.context.on(this.finishedEvent, edges.eventClosure(this, "searchingFinished"));
        };

        // specifically disable this function
        this.draw = function () {
        };

        this.searchingBegan = function () {
            this.searching = true;
            this.renderer.draw();
        };

        this.searchingFinished = function () {
            this.searching = false;
            this.renderer.draw();
        };
    },

    newLeaveSearchNavigation : function(params) {
        return edges.instantiate(edges.LeaveSearchNavigation, params, edges.newComponent)
    },
    LeaveSearchNavigation : function(params) {
        this.include_query_string = edges.getParam(params.include_query_string, true);
        this.include_filters = edges.getParam(params.include_filters, true);
        this.include_paging = edges.getParam(params.include_paging, false);
        this.include_sort = edges.getParam(params.include_sort, false);
        this.include_fields = edges.getParam(params.include_fields, false);
        this.include_aggregations = edges.getParam(params.include_aggregations, false);

        this.urlTemplate = edges.getParam(params.urlTemplate, "{query}");
        this.urlQueryPlaceholder = edges.getParam(params.urlQueryPlaceholder, "{query}");

        this.link = "#";

        this.synchronise = function() {
            this.link = "#";

            if (this.edge.currentQuery !== false) {
                var queryobj = this.edge.currentQuery.objectify({
                    include_query_string : this.include_query_string,
                    include_filters : this.include_filters,
                    include_paging : this.include_paging,
                    include_sort : this.include_sort,
                    include_fields : this.include_fields,
                    include_aggregations : this.include_aggregations
                });

                var j = JSON.stringify(queryobj);
                var frag = encodeURIComponent(j);

                this.link = this.urlTemplate.replace(this.urlQueryPlaceholder, frag);
            }
        };
    },

    ////////////////////////////////////////////////
    // Results list implementation

    newResultsDisplay: function (params) {
        return edges.instantiate(edges.ResultsDisplay, params, edges.newComponent);
    },
    ResultsDisplay: function (params) {
        ////////////////////////////////////////////
        // arguments that can be passed in

        // the category of the component
        this.category = params.category || "results";

        // the secondary results to get the data from, if not using the primary
        this.secondaryResults = edges.getParam(params.secondaryResults, false);

        // filter function that can be used to trim down the result set
        this.filter = edges.getParam(params.filter, false);

        // a sort function that can be used to organise the results
        this.sort = edges.getParam(params.sort, false);

        // the maximum number of results to be stored
        this.limit = edges.getParam(params.limit, false);

        this.infiniteScroll = edges.getParam(params.infiniteScroll, false);

        this.infiniteScrollPageSize = edges.getParam(params.infiniteScrollPageSize, 10);

        // the default renderer for the component to use
        this.defaultRenderer = params.defaultRenderer || "newResultsDisplayRenderer";

        //////////////////////////////////////
        // variables for tracking internal state

        // the results retrieved from ES.  If this is "false" this means that no synchronise
        // has been called on this object, which in turn means that initial searching is still
        // going on.  Once initialised this will be a list (which may in turn be empty, meaning
        // that no results were found)
        this.results = false;

        this.infiniteScrollQuery = false;

        this.hitCount = 0;

        this.synchronise = function () {
            // reset the state of the internal variables
            this.results = [];
            this.infiniteScrollQuery = false;
            this.hitCount = 0;

            var source = this.edge.result;
            if (this.secondaryResults !== false) {
                source = this.edge.secondaryResults[this.secondaryResults];
            }

            // if there are no sources to pull results from, leave us with an empty
            // result set
            if (!source) {
                return;
            }

            // first filter the results
            var results = source.results();
            this._appendResults({results: results});

            // record the hit count for later use
            this.hitCount = source.total();
        };

        this._appendResults = function(params) {
            var results = params.results;

            if (this.filter) {
                results = this.filter({results: results});
            }

            if (this.sort) {
                results.sort(this.sort);
            }

            if (this.limit !== false) {
                results = results.slice(0, this.limit);
            }

            this.results = this.results.concat(results);
        };

        this.infiniteScrollNextPage = function(params) {
            var callback = params.callback;

            // if we have exhausted the result set, don't try to get the next page
            if (this.results.length >= this.hitCount) {
                return;
            }

            if (!this.infiniteScrollQuery) {
                this.infiniteScrollQuery = this.edge.cloneQuery();
                this.infiniteScrollQuery.clearAggregations();
            }

            // move the from/size parameters to get us the next page
            var currentSize = this.infiniteScrollQuery.getSize();
            var currentFrom = this.infiniteScrollQuery.getFrom();
            if (currentFrom === false) {
                currentFrom = 0;
            }
            this.infiniteScrollQuery.from = currentFrom + currentSize;
            this.infiniteScrollQuery.size = this.infiniteScrollPageSize;

            var successCallback = edges.objClosure(this, "infiniteScrollSuccess", ["result"], {callback: callback});
            var errorCallback = edges.objClosure(this, "infiniteScrollError", false, {callback: callback});

            this.edge.queryAdapter.doQuery({
                edge: this.edge,
                query: this.infiniteScrollQuery,
                success: successCallback,
                error: errorCallback
            });
        };

        this.infiniteScrollSuccess = function(params) {
            var results = params.result.results();
            this._appendResults({results: results});
            params.callback();
        };

        this.infinteScrollError = function(params) {
            alert("error");
            params.callback();
        }
    }
});

$.extend(true, doaj, {
    facets : {
        inDOAJ : function() {
            return edges.newRefiningANDTermSelector({
                id: "in_doaj",
                category: "facet",
                field: "admin.in_doaj",
                display: "In DOAJ?",
                deactivateThreshold: 1,
                valueMap : {
                    1 : "True",
                    0 : "False"
                },
                renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                    controls: true,
                    open: false,
                    togglable: true,
                    countFormat: doaj.valueMaps.countFormat,
                    hideInactive: true
                })
            })
        }
    },

    valueMaps : {
        // This must be updated in line with the list in formcontext/choices.py
        applicationStatus : {
            'update_request' : 'Update Request',
            'revisions_required' : 'Revisions Required',
            'pending' : 'Pending',
            'in progress' : 'In Progress',
            'completed' : 'Completed',
            'on hold' : 'On Hold',
            'ready' : 'Ready',
            'rejected' : 'Rejected',
            'accepted' : 'Accepted'
        },

        displayYearPeriod : function(params) {
            var from = params.from;
            var to = params.to;
            var field = params.field;
            var display = (new Date(parseInt(from))).getUTCFullYear();
            return {to: to, toType: "lt", from: from, fromType: "gte", display: display}
        },

        schemaCodeToNameClosure : function(tree) {
            var nameMap = {};
            function recurse(ctx) {
                for (var i = 0; i < ctx.length; i++) {
                    var child = ctx[i];
                    var entry = {};
                    nameMap[doaj.subjects_schema + child.id] = child.text;
                    if (child.children && child.children.length > 0) {
                        recurse(child.children);
                    }
                }
            }
            recurse(tree);

            return function(code) {
                var name = nameMap[code];
                if (name) {
                    return name;
                }
                return code;
            }
        },

        countFormat : edges.numFormat({
            thousandsSeparator: ","
        })
    },

    components : {
        subjectBrowser : function(params) {
            var tree = params.tree;
            var hideEmpty = edges.getParam(params.hideEmpty, false);

            return edges.newTreeBrowser({
                id: "subject",
                category: "facet",
                field: "index.schema_codes_tree.exact",
                tree: function(tree) {
                    function recurse(ctx) {
                        var displayTree = [];
                        for (var i = 0; i < ctx.length; i++) {
                            var child = ctx[i];
                            var entry = {};
                            entry.display = child.text;
                            entry.value = doaj.subjects_schema + child.id;
                            if (child.children && child.children.length > 0) {
                                entry.children = recurse(child.children);
                            }
                            displayTree.push(entry);
                        }
                        displayTree.sort((a, b) => a.display > b.display ? 1 : -1);
                        return displayTree;
                    }
                    return recurse(tree);
                }(tree),
                pruneTree: true,
                size: 9999,
                nodeMatch: function(node, match_list) {
                    for (var i = 0; i < match_list.length; i++) {
                        var m = match_list[i];
                        if (node.value === m.key) {
                            return i;
                        }
                    }
                    return -1;
                },
                filterMatch: function(node, selected) {
                    return $.inArray(node.value, selected) > -1;
                },
                nodeIndex : function(node) {
                    return node.display.toLowerCase();
                },
                renderer: doaj.renderers.newSubjectBrowser({
                    title: "Subjects",
                    open: true,
                    hideEmpty: hideEmpty,
                    showCounts: false
                })
            })
        },
    },

    templates : {
        newPublicSearch: function (params) {
            return edges.instantiate(doaj.templates.PublicSearch, params, edges.newTemplate);
        },
        PublicSearch: function (params) {
            this.namespace = "doajpublicsearch";

            this.title = edges.getParam(params.title, "");
            this.titleBar = edges.getParam(params.titleBar, true);

            this.draw = function (edge) {
                this.edge = edge;

                var titleBarFrag = "";
                if (this.titleBar) {
                    titleBarFrag = '<header class="search__header"> \
                        <p class="label">Search</p>\n \
                        <h1>' + this.title + ' \
                            <span data-feather="help-circle" aria-hidden="true" data-toggle="modal" data-target="#modal-help" type="button"></span><span class="sr-only">Help</span> \
                        </h1> \
                        <div class="row">\
                            <form id="search-input-bar" class="col-md-9" role="search"></form>\
                        </div>\
                    </header>';
                }

                var frag = '<div id="searching-notification"></div>' + titleBarFrag + '\
                    <p id="share_embed"></p>\
                    <h2 id="result-count"></h2>\
                    <div class="row">\
                        <div class="col-md-3">\
                            <aside class="filters">\
                              <h2 class="filters__heading" type="button" data-toggle="collapse" data-target="#filters" aria-expanded="false">\
                                <span data-feather="sliders" aria-hidden="true"></span> Refine search results \
                              </h2>\
                              <ul class="collapse filters__list" id="filters" aria-expanded="false">\
                                  {{FACETS}}\
                              </ul>\
                            </aside>\
                        </div>\
                            \
                        <div class="col-md-9">\
                            <aside id="selected-filters"></aside>\
                            <nav>\
                                <h3 class="sr-only">Display options</h3>\
                                <div class="row">\
                                    <form class="col-sm-6" id="sort_by"></form>\
                                    <form class="col-sm-6 flex-end-col" id="rpp"></form>\
                                </div>\
                            </nav>\
                            <nav class="pagination" id="top-pager"></nav>\
                            <ol class="search-results" id="results"></ol>\
                            <nav class="pagination" id="bottom-pager"></nav>\
                        </div>\
                    </div>';

                // add the facets dynamically
                var facets = edge.category("facet");
                var facetContainers = "";
                for (var i = 0; i < facets.length; i++) {
                    facetContainers += '<li class="filter" id="' + facets[i].id + '"></li>';
                }
                frag = frag.replace(/{{FACETS}}/g, facetContainers);

                edge.context.html(frag);
            };
        },

        newFQWidget: function (params) {
            return edges.instantiate(doaj.templates.FQWidget, params, edges.newTemplate);
        },
        FQWidget: function (params) {
            this.namespace = "fqwidget";

            this.draw = function (edge) {
                this.edge = edge;

                var frag = `
                    <header>
                        <a href="https://doaj.org/" target="_blank" rel="noopener">
                            <svg height="30px" viewBox="0 0 149 53" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
                                <title>DOAJ Logotype</title>
                                <g id="logotype" fill="#282624" fill-rule="nonzero">
                                    <path d="M0,0.4219 L17.9297,0.4219 C24.8672,0.4688 30.0703,3.3516 33.5391,9.0703 C34.7812,10.9922 35.5664,13.0078 35.8945,15.1172 C36.1523,17.2266 36.2812,20.8711 36.2812,26.0508 C36.2812,31.5586 36.082,35.4023 35.6836,37.582 C35.4961,38.6836 35.2148,39.668 34.8398,40.5352 C34.4414,41.3789 33.9609,42.2578 33.3984,43.1719 C31.8984,45.5859 29.8125,47.5781 27.1406,49.1484 C24.4922,50.8359 21.2461,51.6797 17.4023,51.6797 L0,51.6797 L0,0.4219 Z M7.7695,44.332 L17.0508,44.332 C21.4102,44.332 24.5742,42.8438 26.543,39.8672 C27.4102,38.7656 27.9609,37.3711 28.1953,35.6836 C28.4062,34.0195 28.5117,30.9023 28.5117,26.332 C28.5117,21.8789 28.4062,18.6914 28.1953,16.7695 C27.9141,14.8477 27.2461,13.2891 26.1914,12.0938 C24.0352,9.1172 20.9883,7.6758 17.0508,7.7695 L7.7695,7.7695 L7.7695,44.332 Z"></path>
                                    <path d="M39.5938,26.0508 C39.5938,20.0977 39.7695,16.1133 40.1211,14.0977 C40.4961,12.082 41.0703,10.4531 41.8438,9.2109 C43.0859,6.8438 45.0781,4.7344 47.8203,2.8828 C50.5156,1.0078 53.8789,0.0469 57.9102,0 C61.9883,0.0469 65.3867,1.0078 68.1055,2.8828 C70.8008,4.7344 72.7461,6.8438 73.9414,9.2109 C74.809,10.4531 75.406,12.082 75.734,14.0977 C76.039,16.1133 76.191,20.0977 76.191,26.0508 C76.191,31.9102 76.039,35.8711 75.734,37.9336 C75.406,39.9961 74.809,41.6484 73.9414,42.8906 C72.7461,45.2578 70.8008,47.3438 68.1055,49.1484 C65.3867,51.0234 61.9883,52.0078 57.9102,52.1016 C53.8789,52.0078 50.5156,51.0234 47.8203,49.1484 C45.0781,47.3438 43.0859,45.2578 41.8438,42.8906 C41.4688,42.1172 41.1289,41.3789 40.8242,40.6758 C40.543,39.9492 40.3086,39.0352 40.1211,37.9336 C39.7695,35.8711 39.5938,31.9102 39.5938,26.0508 Z M47.3984,26.0508 C47.3984,31.0898 47.5859,34.5 47.9609,36.2812 C48.2891,38.0625 48.957,39.5039 49.9648,40.6055 C50.7852,41.6602 51.8633,42.5156 53.1992,43.1719 C54.5117,43.9453 56.082,44.332 57.9102,44.332 C59.7617,44.332 61.3672,43.9453 62.7266,43.1719 C64.0156,42.5156 65.0469,41.6602 65.8203,40.6055 C66.8281,39.5039 67.5195,38.0625 67.8945,36.2812 C68.2461,34.5 68.4219,31.0898 68.4219,26.0508 C68.4219,21.0117 68.2461,17.5781 67.8945,15.75 C67.5195,14.0156 66.8281,12.5977 65.8203,11.4961 C65.0469,10.4414 64.0156,9.5625 62.7266,8.8594 C61.3672,8.1797 59.7617,7.8164 57.9102,7.7695 C56.082,7.8164 54.5117,8.1797 53.1992,8.8594 C51.8633,9.5625 50.7852,10.4414 49.9648,11.4961 C48.957,12.5977 48.2891,14.0156 47.9609,15.75 C47.5859,17.5781 47.3984,21.0117 47.3984,26.0508 Z"></path>
                                    <path d="M104.008,33.3281 L96.59,10.9336 L96.449,10.9336 L89.031,33.3281 L104.008,33.3281 Z M106.223,40.2188 L86.781,40.2188 L82.844,51.6797 L74.617,51.6797 L93.25,0.4219 L99.754,0.4219 L118.387,51.6797 L110.195,51.6797 L106.223,40.2188 Z"></path>
                                    <path d="M124.82,40.8867 C125.547,41.8477 126.484,42.6328 127.633,43.2422 C128.781,43.9688 130.129,44.332 131.676,44.332 C133.738,44.3789 135.707,43.6641 137.582,42.1875 C138.496,41.4609 139.211,40.5 139.727,39.3047 C140.266,38.1562 140.535,36.7148 140.535,34.9805 L140.535,0.4219 L148.305,0.4219 L148.305,35.7539 C148.211,40.9102 146.523,44.8945 143.242,47.707 C139.984,50.5898 136.199,52.0547 131.887,52.1016 C125.934,51.9609 121.492,49.7344 118.562,45.4219 L124.82,40.8867 Z"></path>
                                </g>
                            </svg>
                        </a>
                        <h2 id="result-count"></h2>\
                        <p class="label label--tertiary">On the Directory of Open Access Journals</p>
                        <p></p>
                    </header>
                    <nav class="search-options">
                        <form class="colsearch-options__left" id="rpp"></form>
                    </nav>
                    <nav class="pagination" id="top-pager"></nav>
                    <ol class="search-results" id="results"></ol>
                    <nav class="pagination" id="bottom-pager"></nav>
                `

                edge.context.html(frag);
            };
        },

        newPublisherApplications: function (params) {
            return edges.instantiate(doaj.templates.PublisherApplications, params, edges.newTemplate);
        },
        PublisherApplications: function (params) {
            this.namespace = "doajpublisherapplications";

            this.draw = function (edge) {
                this.edge = edge;

                var frag = '<div class="row">\
                    <div class="col-md-12">\
                        <nav class="pagination" id="top-pager"></nav>\
                        <ol class="search-results" id="results"></ol>\
                        <nav class="pagination" id="bottom-pager"></nav>\
                    </div>\
                </div>';

                edge.context.html(frag);
            };
        }
    },

    renderers : {
        newSearchingNotificationRenderer: function (params) {
            return edges.instantiate(doaj.renderers.SearchingNotificationRenderer, params, edges.newRenderer);
        },
        SearchingNotificationRenderer: function (params) {

            this.scrollTarget = edges.getParam(params.scrollTarget, "body");

            // namespace to use in the page
            this.namespace = "doaj-notification";

            this.searching = false;

            this.draw = function () {
                if (this.component.searching) {
                    let id = edges.css_id(this.namespace, "loading", this);

                    this.component.edge.context.css("opacity", "0.3");
                    var frag = `<div id="` + id + `" class='loading overlay'>
                        <div></div>
                        <div></div>
                        <div></div>
                        <span class='sr-only'>Loading results…</span>
                      </div>`
                    this.component.edge.context.before(frag);
                    let offset = $(this.scrollTarget).offset().top
                    window.scrollTo(0, offset);
                } else {
                    let that = this;
                    let idSelector = edges.css_id_selector(this.namespace, "loading", this);
                    this.component.edge.context.animate(
                        {
                            opacity: "1",
                        },
                        {
                            duration: 1000,
                            always: function() {
                                $(idSelector).remove();
                            }
                        }
                    );
                }
            }
        },

        newSubjectBrowser : function(params) {
            return edges.instantiate(doaj.renderers.SubjectBrowser, params, edges.newRenderer);
        },
        SubjectBrowser : function(params) {
            this.title = edges.getParam(params.title, "");

            this.selectMode = edges.getParam(params.selectMode, "multiple");

            this.hideEmpty = edges.getParam(params.hideEmpty, false);

            this.togglable = edges.getParam(params.togglable, true);

            this.open = edges.getParam(params.open, false);

            this.showCounts = edges.getParam(params.showCounts, false);

            this.namespace = "doaj-subject-browser";

            this.lastScroll = 0;

            this.draw = function() {
                // for convenient short references ...
                var st = this.component.syncTree;
                var namespace = this.namespace;
                // var that = this;

                // var checkboxClass = edges.css_classes(namespace, "selector", this);
                // var countClass = edges.css_classes(namespace, "count", this);

                var treeReport = this._renderTree({tree: st, selectedPathOnly: false, showOneLevel: true});
                var treeFrag = treeReport.frag;

                if (treeFrag === "") {
                    treeFrag = "Loading…";
                }

                var toggleId = edges.css_id(namespace, "toggle", this);
                var resultsId = edges.css_id(namespace, "results", this);
                var searchId = edges.css_id(namespace, "search", this);
                var filteredId = edges.css_id(namespace, "filtered", this);
                var mainListId = edges.css_id(namespace, "main", this);

                var toggle = "";
                if (this.togglable) {
                    toggle = '<span data-feather="chevron-down" aria-hidden="true"></span>';
                }
                var placeholder = 'Search ' + this.component.nodeCount + ' subjects';
                var frag = '<h3 class="label label--secondary filter__heading" type="button" id="' + toggleId + '">' + this.title + toggle + '</h3>\
                    <div class="filter__body collapse" aria-expanded="false" style="height: 0px" id="' + resultsId + '">\
                        <label for="' + searchId + '" class="sr-only">' + placeholder + '</label>\
                        <input type="text" name="' + searchId + '" id="' + searchId + '" class="filter__search" placeholder="' + placeholder + '">\
                        <ul class="filter__choices" id="' + filteredId + '" style="display:none"></ul>\
                        <ul class="filter__choices" id="' + mainListId + '">{{FILTERS}}</ul>\
                    </div>';

                // substitute in the component parts
                frag = frag.replace(/{{FILTERS}}/g, treeFrag);

                // now render it into the page
                this.component.context.html(frag);
                feather.replace();

                // trigger all the post-render set-up functions
                this.setUIOpen();

                var mainListSelector = edges.css_id_selector(namespace, "main", this);
                this.component.jq(mainListSelector).scrollTop(this.lastScroll);

                var checkboxSelector = edges.css_class_selector(namespace, "selector", this);
                edges.on(checkboxSelector, "change", this, "filterToggle");

                var toggleSelector = edges.css_id_selector(namespace, "toggle", this);
                edges.on(toggleSelector, "click", this, "toggleOpen");

                var searchSelector = edges.css_id_selector(namespace, "search", this);
                edges.on(searchSelector, "keyup", this, "filterSubjects");
            };

            this._renderTree = function(params) {
                var st = edges.getParam(params.tree, []);
                var selectedPathOnly = edges.getParam(params.selectedPathOnly, true);
                var showOneLevel = edges.getParam(params.showOneLevel, true);
                var that = this;

                var checkboxClass = edges.css_classes(this.namespace, "selector", this);

                function renderEntry(entry) {
                    if (that.hideEmpty && entry.count === 0 && entry.childCount === 0) {
                        return "";
                    }

                    var id = edges.safeId(entry.value);
                    var checked = "";
                    if (entry.selected) {
                        checked = ' checked="checked" ';
                    }

                    var count = "";
                    if (that.showCounts) {
                        var countClass = edges.css_classes(that.namespace, "count", that);
                        count = ' <span class="' + countClass + '">(' + entry.count + '/' + entry.childCount + ')</span>';
                    }

                    var frag = '<input class="' + checkboxClass + '" data-value="' + edges.escapeHtml(entry.value) + '" id="' + id + '" type="checkbox" name="' + id + '"' + checked + '>\
                        <label for="' + id + '" class="filter__label">' + entry.display + count + '</label>';

                    return frag;
                }

                function recurse(tree) {
                    var selected = tree;

                    // first check to see if there are any elements at this level that are selected.  If there are,
                    // that is the only element that we'll render
                    if (selectedPathOnly) {
                        for (var i = 0; i < tree.length; i++) {
                            var entry = tree[i];
                            if (entry.selected) {
                                selected = [entry];
                                break;
                            }
                        }
                    }

                    // now go through either this tree level or just the selected elements, and render the relevant
                    // bits of the sub-tree
                    var anySelected = false;
                    var rFrag = "";
                    for (var i = 0; i < selected.length; i++) {
                        var entry = selected[i];
                        var entryFrag = renderEntry(entry);
                        if (entryFrag === "") {
                            continue;
                        }
                        if (entry.selected) {
                            anySelected = true;
                        }
                        if (entry.children) {
                            var childReport = recurse(entry.children);
                            if (childReport.anySelected) {
                                anySelected = true;
                            }
                            // only attach the children frag if, first any of these are true:
                            // - one of the children is selected
                            // - the entry itself is selected
                            // - we don't want to only show the selected path
                            if (!selectedPathOnly || childReport.anySelected || entry.selected) {
                                // Then, another level (separated out to save my brain from the tortuous logic)
                                // only attach the children frag if, any of these are true:
                                // - the entry or one of its children is selected
                                // - we want to show more than one level at a time
                                if (childReport.anySelected || entry.selected || !showOneLevel) {
                                    var cFrag = childReport.frag;
                                    if (cFrag !== "") {
                                        entryFrag += '<ul class="filter__choices">';
                                        entryFrag += cFrag;
                                        entryFrag += '</ul>';
                                    }
                                }
                            }
                        }

                        rFrag += '<li>';
                        rFrag += entryFrag;
                        rFrag += '</li>';
                    }
                    return {frag : rFrag, anySelected: anySelected};
                }

                return recurse(st);
            };

            this.setUIOpen = function () {
                // the selectors that we're going to use
                var resultsSelector = edges.css_id_selector(this.namespace, "results", this);
                var toggleSelector = edges.css_id_selector(this.namespace, "toggle", this);

                var results = this.component.jq(resultsSelector);
                var toggle = this.component.jq(toggleSelector);

                if (this.open) {
                    results.addClass("in").attr("aria-expanded", "true").css({"height": ""});
                    toggle.removeClass("collapsed").attr("aria-expanded", "true");
                } else {
                    results.removeClass("in").attr("aria-expanded", "false").css({"height" : "0px"});
                    toggle.addClass("collapsed").attr("aria-expanded", "false");
                }
            };

            this.filterToggle = function(element) {
                var mainListSelector = edges.css_id_selector(this.namespace, "main", this);
                this.lastScroll = this.component.jq(mainListSelector).scrollTop();
                var el = this.component.jq(element);
                // var filter_id = this.component.jq(element).attr("id");
                var checked = el.is(":checked");
                var value = el.attr("data-value");
                if (checked) {
                    this.component.addFilter({value: value});
                } else {
                    this.component.removeFilter({value: value});
                }
            };

            this.toggleOpen = function (element) {
                this.open = !this.open;
                this.setUIOpen();
            };

            this.filterSubjects = function(element) {
                var st = this.component.syncTree;
                var term = $(element).val();
                var that = this;

                var filterSelector = edges.css_id_selector(this.namespace, "filtered", this);
                var mainSelector = edges.css_id_selector(this.namespace, "main", this);
                var filterEl = this.component.jq(filterSelector);
                var mainEl = this.component.jq(mainSelector);

                if (term === "") {
                    filterEl.html("");
                    filterEl.hide();
                    mainEl.show();
                    return;
                }
                if (term.length < 3) {
                    filterEl.html("<li>Enter 3 characters or more to search</li>");
                    filterEl.show();
                    mainEl.hide();
                    return;
                }
                term = term.toLowerCase();

                function entryMatch(entry) {
                    if (that.hideEmpty && entry.count === 0 && entry.childCount === 0) {
                        return false;
                    }

                    var matchTerm = entry.index;
                    var includes =  matchTerm.includes(term);
                    if (includes) {
                        var idx = matchTerm.indexOf(term);
                        var display = entry.display;
                        return display.substring(0, idx) + "<strong>" + display.substring(idx, idx + term.length) + "</strong>" + display.substring(idx + term.length);
                    }
                }

                function recurse(tree) {
                    var filteredLayer = [];
                    for (var i = 0; i < tree.length; i++) {
                        var entry = tree[i];
                        var childReport = [];
                        if (entry.children) {
                            childReport = recurse(entry.children);
                        }
                        var selfMatch = entryMatch(entry);
                        if (selfMatch || childReport.length > 0) {
                            var newEntry = $.extend({}, entry);
                            delete newEntry.children;
                            if (selfMatch) {
                                newEntry.display = selfMatch;
                            }
                            if (childReport.length > 0) {
                                newEntry.children = childReport;
                            }
                            filteredLayer.push(newEntry);
                        }
                    }
                    return filteredLayer;
                }

                var filtered = recurse(st);

                if (filtered.length > 0) {
                    var displayReport = this._renderTree({tree: filtered, selectedPathOnly: false, showOneLevel: false});

                    filterEl.html(displayReport.frag);
                    mainEl.hide();
                    filterEl.show();

                    var checkboxSelector = edges.css_class_selector(this.namespace, "selector", this);
                    edges.on(checkboxSelector, "change", this, "filterToggle");
                } else {
                    filterEl.html("<li>No subjects match your search</li>");
                    mainEl.hide();
                    filterEl.show();
                }

            };
        },

        newFullSearchControllerRenderer: function (params) {
            return edges.instantiate(doaj.renderers.FullSearchControllerRenderer, params, edges.newRenderer);
        },
        FullSearchControllerRenderer: function (params) {
            // enable the search button
            this.searchButton = edges.getParam(params.searchButton, false);

            // text to include on the search button.  If not provided, will just be the magnifying glass
            this.searchButtonText = edges.getParam(params.searchButtonText, false);

            // should the clear button be rendered
            this.clearButton = edges.getParam(params.clearButton, true);

            // set the placeholder text for the search box
            this.searchPlaceholder = edges.getParam(params.searchPlaceholder, "Search");

            // amount of time between finishing typing and when a query is executed from the search box
            this.freetextSubmitDelay = edges.getParam(params.freetextSubmitDelay, 500);

            ////////////////////////////////////////
            // state variables

            this.focusSearchBox = false;

            this.namespace = "doaj-bs3-search-controller";

            this.draw = function () {
                var comp = this.component;

                var clearClass = edges.css_classes(this.namespace, "reset", this);
                var clearFrag = "";
                if (this.clearButton) {
                    clearFrag = '<button type="button" class="tag tag--secondary ' + clearClass + '" title="Clear all search and sort parameters and start again"> \
                            Clear all \
                        </button>';
                }

                // if sort options are provided render the orderer and the order by
                var sortOptions = "";
                if (comp.sortOptions && comp.sortOptions.length > 0) {
                    // classes that we'll use
                    var sortClasses = edges.css_classes(this.namespace, "sort", this);
                    var directionClass = edges.css_classes(this.namespace, "direction", this);
                    var sortFieldClass = edges.css_classes(this.namespace, "sortby", this);

                    sortOptions = '<div class="input-group ' + sortClasses + '"> \
                                    <button type="button" class="input-group__input ' + directionClass + '" title="" href="#"></button> \
                                    <select class="' + sortFieldClass + ' input-group__input"> \
                                        <option value="_score">Relevance</option>';

                    for (var i = 0; i < comp.sortOptions.length; i++) {
                        var field = comp.sortOptions[i].field;
                        var display = comp.sortOptions[i].display;
                        sortOptions += '<option value="' + field + '">' + edges.escapeHtml(display) + '</option>';
                    }

                    sortOptions += ' </select></div>';
                }

                // select box for fields to search on
                var field_select = "";
                if (comp.fieldOptions && comp.fieldOptions.length > 0) {
                    // classes that we'll use
                    var searchFieldClass = edges.css_classes(this.namespace, "field", this);

                    field_select += '<select class="' + searchFieldClass + ' input-group__input">';
                    field_select += '<option value="">search all</option>';

                    for (var i = 0; i < comp.fieldOptions.length; i++) {
                        var obj = comp.fieldOptions[i];
                        field_select += '<option value="' + obj['field'] + '">' + edges.escapeHtml(obj['display']) + '</option>';
                    }
                    field_select += '</select>';
                }

                // more classes that we'll use
                var textClass = edges.css_classes(this.namespace, "text", this);
                var searchClass = edges.css_classes(this.namespace, "search", this);

                // text search box id
                var textId = edges.css_id(this.namespace, "text", this);

                var searchFrag = "";
                if (this.searchButton) {
                    var text = '<span class="glyphicon glyphicon-white glyphicon-search"></span>';
                    if (this.searchButtonText !== false) {
                        text = this.searchButtonText;
                    }
                    searchFrag = '<button type="button" class="input-group__input ' + searchClass + '"> \
                            ' + text + ' \
                        </button>';
                }

                var searchClasses = edges.css_classes(this.namespace, "searchcombo", this);
                var searchBox = '<div class="input-group ' + searchClasses + '"> \
                                ' + field_select + '\
                                <input type="text" id="' + textId + '" class="' + textClass + ' form-control input-sm" name="q" value="" placeholder="' + this.searchPlaceholder + '" style="margin-left: -1px; width: 60%;"/> \
                                ' + searchFrag + ' \
                    </div>';

                if (searchBox !== "") {
                    searchBox = searchBox;
                }
                if (sortOptions !== "") {
                    sortOptions = '<div class="col-xs-6">' + sortOptions + '</div>';
                }
                if (clearFrag !== "") {
                    clearFrag = '<div class="col-xs-6" style="text-align: right;">' + clearFrag + '</div>';
                }

                var frag = searchBox + '<div class="row">' + sortOptions + clearFrag + '</div>';

                comp.context.html(frag);

                // now populate all the dynamic bits
                if (comp.sortOptions && comp.sortOptions.length > 0) {
                    this.setUISortDir();
                    this.setUISortField();
                }
                if (comp.fieldOptions && comp.fieldOptions.length > 0) {
                    this.setUISearchField();
                }
                this.setUISearchText();

                // attach all the bindings
                if (comp.sortOptions && comp.sortOptions.length > 0) {
                    var directionSelector = edges.css_class_selector(this.namespace, "direction", this);
                    var sortSelector = edges.css_class_selector(this.namespace, "sortby", this);
                    edges.on(directionSelector, "click", this, "changeSortDir");
                    edges.on(sortSelector, "change", this, "changeSortBy");
                }
                if (comp.fieldOptions && comp.fieldOptions.length > 0) {
                    var fieldSelector = edges.css_class_selector(this.namespace, "field", this);
                    edges.on(fieldSelector, "change", this, "changeSearchField");
                }
                var textSelector = edges.css_class_selector(this.namespace, "text", this);
                if (this.freetextSubmitDelay > -1) {
                    edges.on(textSelector, "keyup", this, "setSearchText", this.freetextSubmitDelay);
                } else {
                    function onlyEnter(event) {
                        var code = (event.keyCode ? event.keyCode : event.which);
                        return code === 13;
                    }

                    edges.on(textSelector, "keyup", this, "setSearchText", false, onlyEnter);
                }

                var resetSelector = edges.css_class_selector(this.namespace, "reset", this);
                edges.on(resetSelector, "click", this, "clearSearch");

                var searchSelector = edges.css_class_selector(this.namespace, "search", this);
                edges.on(searchSelector, "click", this, "doSearch");

                if (this.shareLink) {
                    var shareSelector = edges.css_class_selector(this.namespace, "toggle-share", this);
                    edges.on(shareSelector, "click", this, "toggleShare");

                    var closeShareSelector = edges.css_class_selector(this.namespace, "close-share", this);
                    edges.on(closeShareSelector, "click", this, "toggleShare");

                    if (this.component.urlShortener) {
                        var shortenSelector = edges.css_class_selector(this.namespace, "shorten", this);
                        edges.on(shortenSelector, "click", this, "toggleShorten");
                    }
                }

                // if we've been asked to focus the text box, do that
                if (this.focusSearchBox) {
                    $(textSelector).focus();
                    this.focusSearchBox = false;
                }
            };

            //////////////////////////////////////////////////////
            // functions for setting UI values

            this.setUISortDir = function () {
                // get the selector we need
                var directionSelector = edges.css_class_selector(this.namespace, "direction", this);
                var el = this.component.jq(directionSelector);
                if (this.component.sortDir === 'asc') {
                    el.html('sort ↑ by');
                    el.attr('title', 'Current order ascending. Click to change to descending');
                } else {
                    el.html('sort ↓ by');
                    el.attr('title', 'Current order descending. Click to change to ascending');
                }
            };

            this.setUISortField = function () {
                if (!this.component.sortBy) {
                    return;
                }
                // get the selector we need
                var sortSelector = edges.css_class_selector(this.namespace, "sortby", this);
                var el = this.component.jq(sortSelector);
                el.val(this.component.sortBy);
            };

            this.setUISearchField = function () {
                if (!this.component.searchField) {
                    return;
                }
                // get the selector we need
                var fieldSelector = edges.css_class_selector(this.namespace, "field", this);
                var el = this.component.jq(fieldSelector);
                el.val(this.component.searchField);
            };

            this.setUISearchText = function () {
                if (!this.component.searchString) {
                    return;
                }
                // get the selector we need
                var textSelector = edges.css_class_selector(this.namespace, "text", this);
                var el = this.component.jq(textSelector);
                el.val(this.component.searchString);
            };

            ////////////////////////////////////////
            // event handlers

            this.changeSortDir = function (element) {
                this.component.changeSortDir();
            };

            this.changeSortBy = function (element) {
                var val = this.component.jq(element).val();
                this.component.setSortBy(val);
            };

            this.changeSearchField = function (element) {
                var val = this.component.jq(element).val();
                this.component.setSearchField(val);
            };

            this.setSearchText = function (element) {
                this.focusSearchBox = true;
                var val = this.component.jq(element).val();
                this.component.setSearchText(val);
            };

            this.clearSearch = function (element) {
                this.component.clearSearch();
            };

            this.doSearch = function (element) {
                var textId = edges.css_id_selector(this.namespace, "text", this);
                var text = this.component.jq(textId).val();
                this.component.setSearchText(text);
            };
        },

        newSearchBoxFacetRenderer: function (params) {
            return edges.instantiate(doaj.renderers.SearchBoxFacetRenderer, params, edges.newRenderer);
        },
        SearchBoxFacetRenderer: function (params) {

            // set the placeholder text for the search box
            this.searchPlaceholder = edges.getParam(params.searchPlaceholder, "Search");

            // amount of time between finishing typing and when a query is executed from the search box
            this.freetextSubmitDelay = edges.getParam(params.freetextSubmitDelay, 500);

            this.title = edges.getParam(params.title, "");

            ////////////////////////////////////////
            // state variables

            this.focusSearchBox = false;

            this.namespace = "doaj-bs3-search-box-facet";

            this.draw = function () {
                var comp = this.component;

                // more classes that we'll use
                var textClass = edges.css_classes(this.namespace, "text", this);
                var textId = edges.css_id(this.namespace, "text", this);

                //var frag = '<div class="row">' + clearFrag + sortOptions + searchBox + '</div>';
                var frag = '<h3 class="label label--secondary filter__heading">' + edges.escapeHtml(this.title) + '</h3>\
                    <label for="' + textId + '" class="sr-only">' + edges.escapeHtml(this.title) + '</label>\
                    <input type="text" name="' + textId + '" id="' + textId + '" class="filter__search ' + textClass + '" placeholder="' + this.searchPlaceholder + '">';

                comp.context.html(frag);
                feather.replace();

                this.setUISearchText();

                var textSelector = edges.css_class_selector(this.namespace, "text", this);
                if (this.freetextSubmitDelay > -1) {
                    edges.on(textSelector, "keyup", this, "setSearchText", this.freetextSubmitDelay);
                } else {
                    function onlyEnter(event) {
                        var code = (event.keyCode ? event.keyCode : event.which);
                        return code === 13;
                    }

                    edges.on(textSelector, "keyup", this, "setSearchText", false, onlyEnter);
                }

                // if we've been asked to focus the text box, do that
                if (this.focusSearchBox) {
                    $(textSelector).focus();
                    this.focusSearchBox = false;
                }
            };

            //////////////////////////////////////////////////////
            // functions for setting UI values

            this.setUISearchText = function () {
                if (!this.component.searchString) {
                    return;
                }
                // get the selector we need
                var textSelector = edges.css_class_selector(this.namespace, "text", this);
                var el = this.component.jq(textSelector);
                el.val(this.component.searchString);
            };

            ////////////////////////////////////////
            // event handlers

            this.setSearchText = function (element) {
                this.focusSearchBox = true;
                var val = this.component.jq(element).val();
                this.component.setSearchText(val);
            };

            this.clearSearch = function (element) {
                this.component.clearSearch();
            };

            this.doSearch = function (element) {
                var textId = edges.css_id_selector(this.namespace, "text", this);
                var text = this.component.jq(textId).val();
                this.component.setSearchText(text);
            };
        },

        newPageSizeRenderer: function (params) {
            return edges.instantiate(doaj.renderers.PageSizeRenderer, params, edges.newRenderer);
        },
        PageSizeRenderer: function (params) {
            this.sizeOptions = edges.getParam(params.sizeOptions, [10, 25, 50, 100]);

            this.sizeLabel = edges.getParam(params.sizeLabel, "");

            this.namespace = "doaj-pagesize";

            this.draw = function () {
                // classes we'll need
                var sizeSelectClass = edges.css_classes(this.namespace, "size", this);
                var sizeSelectId = edges.css_classes(this.namespace, "page-size", this);

                // the number of records per page
                var sizer = '<label for="' + sizeSelectId + '">' + this.sizeLabel + '</label><select class="' + sizeSelectClass + '" name="' + sizeSelectId + '" id="' + sizeSelectId + '">{{SIZES}}</select>';
                var sizeopts = "";
                var optarr = this.sizeOptions.slice(0);
                if (this.component.pageSize && $.inArray(this.component.pageSize, optarr) === -1) {
                    optarr.push(this.component.pageSize)
                }
                optarr.sort(function (a, b) {
                    return a - b
                });  // sort numerically
                for (var i = 0; i < optarr.length; i++) {
                    var so = optarr[i];
                    var selected = "";
                    if (so === this.component.pageSize) {
                        selected = "selected='selected'";
                    }
                    sizeopts += '<option name="' + so + '" ' + selected + '>' + so + '</option>';
                }
                sizer = sizer.replace(/{{SIZES}}/g, sizeopts);

                this.component.context.html(sizer);

                var sizeSelector = edges.css_class_selector(this.namespace, "size", this);
                edges.on(sizeSelector, "change", this, "changeSize");

            };

            this.changeSize = function (element) {
                var size = $(element).val();
                this.component.setSize(size);
            };
        },

        newShareEmbedRenderer: function (params) {
            return edges.instantiate(doaj.renderers.ShareEmbedRenderer, params, edges.newRenderer);
        },
        ShareEmbedRenderer: function (params) {
            // enable the share/save link feature
            this.shareLinkText = edges.getParam(params.shareLinkText, "share");

            ////////////////////////////////////////
            // state variables

            // this.shareBoxOpen = false;

            this.showShortened = false;

            this.namespace = "doaj-share-embed";

            this.draw = function () {
                // reset these on each draw
                // this.shareBoxOpen = false;
                this.showShortened = false;

                var comp = this.component;

                var shareButtonFrag = "";
                var shareButtonClass = edges.css_classes(this.namespace, "toggle-share", this);
                var modalId = edges.css_id(this.namespace, "modal", this);
                shareButtonFrag = '<button data-toggle="modal" data-target="#' + modalId + '" class="' + shareButtonClass + ' button button--tertiary" role="button">' + this.shareLinkText + '</button>';

                var shorten = "";
                if (this.component.urlShortener) {
                    var shortenClass = edges.css_classes(this.namespace, "shorten", this);
                    shorten = '<p>Share a link to this search</p>'
                }
                var embed = "";
                if (this.component.embedSnippet) {
                    var embedClass = edges.css_classes(this.namespace, "embed", this);
                    embed = '<p>Embed this search in your site</p>\
                    <textarea style="width: 100%; height: 150px" readonly class="' + embedClass + '"></textarea>';
                }
                var shareBoxClass = edges.css_classes(this.namespace, "share", this);
                var shareUrlClass = edges.css_classes(this.namespace, "share-url", this);
                var shortenButtonClass = edges.css_classes(this.namespace, "shorten-url", this);
                var shareFrag = '<div class="' + shareBoxClass + '">\
                    ' + shorten + '\
                    <textarea style="width: 100%; height: 150px" readonly class="' + shareUrlClass + '"></textarea>\
                    <p><button class="' + shortenButtonClass + '">shorten url</button></p>\
                    ' + embed + '\
                </div>';

                var modal = '<section class="modal" id="' + modalId + '" tabindex="-1" role="dialog">\
                    <div class="modal__dialog" role="document">\
                        <form role="search">\
                            <header class="flex-space-between modal__heading"> \
                                <h2 class="modal__title">' + this.shareLinkText + '</h2>\
                              <span type="button" data-dismiss="modal" class="type-01"><span class="sr-only">Close</span>&times;</span>\
                            </header>\
                            ' + shareFrag + '\
                        </form>\
                    </div>\
                </section>';

                var frag = shareButtonFrag + modal;

                comp.context.html(frag);
                feather.replace();

                var shareSelector = edges.css_class_selector(this.namespace, "toggle-share", this);
                edges.on(shareSelector, "click", this, "toggleShare");

                if (this.component.urlShortener) {
                    var shortenSelector = edges.css_class_selector(this.namespace, "shorten-url", this);
                    edges.on(shortenSelector, "click", this, "toggleShorten");
                }
            };

            //////////////////////////////////////////////////////
            // functions for setting UI values

            this.toggleShare = function(element) {
                var shareUrlSelector = edges.css_class_selector(this.namespace, "share-url", this);
                var textarea = this.component.jq(shareUrlSelector);

                if (this.showShortened) {
                    textarea.val(this.component.shortUrl);
                } else {
                    textarea.val(this.component.edge.fullUrl());
                }
                if (this.component.embedSnippet) {
                    var embedSelector = edges.css_class_selector(this.namespace, "embed", this);
                    var embedTextarea = this.component.jq(embedSelector);
                    embedTextarea.val(this.component.embedSnippet(this));
                }
            };

            this.toggleShorten = function(element) {
                if (!this.component.shortUrl) {
                    var callback = edges.objClosure(this, "updateShortUrl");
                    this.component.generateShortUrl(callback);
                } else {
                    this.updateShortUrl();
                }
            };

            this.updateShortUrl = function() {
                var shareUrlSelector = edges.css_class_selector(this.namespace, "share-url", this);
                var shortenSelector = edges.css_class_selector(this.namespace, "shorten-url", this);
                var textarea = this.component.jq(shareUrlSelector);
                var button = this.component.jq(shortenSelector);
                if (this.showShortened) {
                    textarea.val(this.component.edge.fullUrl());
                    button.html('shorten url');
                    this.showShortened = false;
                } else {
                    textarea.val(this.component.shortUrl);
                    button.html('original url');
                    this.showShortened = true;
                }
            };
        },

        newSearchBarRenderer: function (params) {
            return edges.instantiate(doaj.renderers.SearchBarRenderer, params, edges.newRenderer);
        },
        SearchBarRenderer: function (params) {
            // enable the search button
            this.searchButton = edges.getParam(params.searchButton, false);

            // text to include on the search button.  If not provided, will just be the magnifying glass
            this.searchButtonText = edges.getParam(params.searchButtonText, false);

            // should the clear button be rendered
            this.clearButton = edges.getParam(params.clearButton, true);

            // set the placeholder text for the search box
            this.searchPlaceholder = edges.getParam(params.searchPlaceholder, "Search");

            // amount of time between finishing typing and when a query is executed from the search box
            this.freetextSubmitDelay = edges.getParam(params.freetextSubmitDelay, 500);

            ////////////////////////////////////////
            // state variables

            this.namespace = "doaj-bs3-search-controller";

            this.draw = function () {
                var comp = this.component;

                // FIXME: leaving this in in case we need to add it in production
                //var clearClass = edges.css_classes(this.namespace, "reset", this);
                //var clearFrag = "";
                //if (this.clearButton) {
                //    clearFrag = '<button type="button" class="btn btn-danger btn-sm ' + clearClass + '" title="Clear all search and sort parameters and start again"> \
                //            <span class="glyphicon glyphicon-remove"></span> \
                //        </button>';
                //}

                // select box for fields to search on
                var field_select = "";
                if (comp.fieldOptions && comp.fieldOptions.length > 0) {
                    // classes that we'll use
                    var searchFieldClass = edges.css_classes(this.namespace, "field", this);
                    var searchFieldId = edges.css_id(this.namespace, "fields", this);

                    field_select += '<select class="' + searchFieldClass + ' input-group__input" name="fields" id="' + searchFieldId + '">';
                    field_select += '<option value="">All fields</option>';

                    for (var i = 0; i < comp.fieldOptions.length; i++) {
                        var obj = comp.fieldOptions[i];
                        field_select += '<option value="' + obj['field'] + '">' + edges.escapeHtml(obj['display']) + '</option>';
                    }
                    field_select += '</select>';
                }

                // more classes that we'll use
                var textClass = edges.css_classes(this.namespace, "text", this);

                var searchFrag = "";
                if (this.searchButton) {
                    var text = '<span class="glyphicon glyphicon-white glyphicon-search"></span>';
                    if (this.searchButtonText !== false) {
                        text = this.searchButtonText;
                    }
                    searchFrag = '<span class="input-group-btn"> \
                        <button type="button" class="btn btn-info btn-sm ' + searchClass + '"> \
                            ' + text + ' \
                        </button> \
                    </span>';
                }

                var textId = edges.css_id(this.namespace, "text", this);
                var searchBox = '<input type="text" id="' + textId + '" class="' + textClass + ' input-group__input" name="q" value="" placeholder="' + this.searchPlaceholder + '"/>';

                var searchClass = edges.css_classes(this.namespace, "search", this);
                var button = '<button class="' + searchClass + ' input-group__input" type="submit">\
                              <span data-feather="search" aria-hidden="true"></span>\
                              <span class="sr-only"> Search</span></button>';

                // if (clearFrag !== "") {
                //     clearFrag = '<div class="col-md-1 col-xs-12">' + clearFrag + "</div>";
                //}

                var sr1 = '<label for="' + textId + '" class="sr-only">Search by keywords</label>';
                var sr2 = '<label for="' + searchFieldId + '" class="sr-only">In the field</label>';
                var frag = '<div class="input-group">' + sr1 + searchBox + sr2 + field_select + button + '</div>';

                comp.context.html(frag);

                if (comp.fieldOptions && comp.fieldOptions.length > 0) {
                    this.setUISearchField();
                }
                this.setUISearchText();

                if (comp.fieldOptions && comp.fieldOptions.length > 0) {
                    var fieldSelector = edges.css_class_selector(this.namespace, "field", this);
                    edges.on(fieldSelector, "change", this, "changeSearchField");
                }
                var textSelector = edges.css_class_selector(this.namespace, "text", this);
                if (this.freetextSubmitDelay > -1) {
                    edges.on(textSelector, "keyup", this, "setSearchText", this.freetextSubmitDelay);
                } else {
                    function onlyEnter(event) {
                        var code = (event.keyCode ? event.keyCode : event.which);
                        return code === 13;
                    }

                    edges.on(textSelector, "keyup", this, "setSearchText", false, onlyEnter);
                }

                //var resetSelector = edges.css_class_selector(this.namespace, "reset", this);
                //edges.on(resetSelector, "click", this, "clearSearch");

                var searchSelector = edges.css_class_selector(this.namespace, "search", this);
                edges.on(searchSelector, "click", this, "doSearch");

                // if we've been asked to focus the text box, do that
                if (this.focusSearchBox) {
                    $(textSelector).focus();
                    this.focusSearchBox = false;
                }
            };

            //////////////////////////////////////////////////////
            // functions for setting UI values

            this.setUISearchField = function () {
                if (!this.component.searchField) {
                    return;
                }
                // get the selector we need
                var fieldSelector = edges.css_class_selector(this.namespace, "field", this);
                var el = this.component.jq(fieldSelector);
                el.val(this.component.searchField);
            };

            this.setUISearchText = function () {
                if (!this.component.searchString) {
                    return;
                }
                // get the selector we need
                var textSelector = edges.css_class_selector(this.namespace, "text", this);
                var el = this.component.jq(textSelector);
                el.val(this.component.searchString);
            };

            ////////////////////////////////////////
            // event handlers

            this.changeSearchField = function (element) {
                // find out if there's any search text
                var textIdSelector = edges.css_id_selector(this.namespace, "text", this);
                var text = this.component.jq(textIdSelector).val();

                if (text === "") {
                    return;
                }

                // if there is search text, then proceed to run the search
                var val = this.component.jq(element).val();
                this.component.setSearchField(val, false);
                this.component.setSearchText(text);
            };

            this.setSearchText = function (element) {
                this.focusSearchBox = true;
                var val = this.component.jq(element).val();
                this.component.setSearchText(val, false);

                var searchFieldIdSelector = edges.css_id_selector(this.namespace, "fields", this);
                var field = this.component.jq(searchFieldIdSelector).val();
                this.component.setSearchField(field);
            };

            this.clearSearch = function (element) {
                this.component.clearSearch();
            };

            this.doSearch = function (element) {
                var textId = edges.css_id_selector(this.namespace, "text", this);
                var text = this.component.jq(textId).val();
                this.component.setSearchText(text);
            };
        },

        newFacetFilterSetterRenderer: function (params) {
            return edges.instantiate(doaj.renderers.FacetFilterSetterRenderer, params, edges.newRenderer);
        },
        FacetFilterSetterRenderer: function (params) {
            // whether the facet should be open or closed
            // can be initialised and is then used to track internal state
            this.open = edges.getParam(params.open, false);

            // whether the facet can be opened and closed
            this.togglable = edges.getParam(params.togglable, true);

            // whether the count should be displayed along with the term
            // defaults to false because count may be confusing to the user in an OR selector
            this.showCount = edges.getParam(params.showCount, true);

            // The display title for the facet
            this.facetTitle = edges.getParam(params.facetTitle, "Untitled");

            this.openIcon = edges.getParam(params.openIcon, "glyphicon glyphicon-plus");

            this.closeIcon = edges.getParam(params.closeIcon, "glyphicon glyphicon-minus");

            // namespace to use in the page
            this.namespace = "doaj-facet-filter-setter";

            this.draw = function () {
                // for convenient short references ...
                var comp = this.component;
                var namespace = this.namespace;

                var checkboxClass = edges.css_classes(namespace, "selector", this);

                var filters = "";
                for (var i = 0; i < comp.filters.length; i++) {
                    var filter = comp.filters[i];
                    var id = filter.id;
                    var display = filter.display;
                    var count = comp.filter_counts[id];
                    var active = comp.active_filters[id];

                    if (count === undefined) {
                        count = 0;
                    }

                    var checked = "";
                    if (active) {
                        checked = ' checked="checked" ';
                    }
                    filters += '<li>\
                            <input class="' + checkboxClass + '" id="' + id + '" type="checkbox" name="' + id + '"' + checked + '>\
                            <label for="' + id + '" class="filter__label">' + display + '</label>\
                        </li>';
                }

                var frag = '<h3 class="label label--secondary filter__heading">' + this.facetTitle + '</h3>\
                    <ul class="filter__choices">{{FILTERS}}</ul>';

                // substitute in the component parts
                frag = frag.replace(/{{FILTERS}}/g, filters);

                // now render it into the page
                comp.context.html(frag);

                // trigger all the post-render set-up functions
                this.setUIOpen();

                var checkboxSelector = edges.css_class_selector(namespace, "selector", this);
                edges.on(checkboxSelector, "change", this, "filterToggle");
            };

            this.setUIOpen = function () {
                // the selectors that we're going to use
                var resultsSelector = edges.css_id_selector(this.namespace, "results", this);
                var toggleSelector = edges.css_id_selector(this.namespace, "toggle", this);

                var results = this.component.jq(resultsSelector);
                var toggle = this.component.jq(toggleSelector);

                var openBits = this.openIcon.split(" ");
                var closeBits = this.closeIcon.split(" ");

                if (this.open) {
                    var i = toggle.find("i");
                    for (var j = 0; j < openBits.length; j++) {
                        i.removeClass(openBits[j]);
                    }
                    for (var j = 0; j < closeBits.length; j++) {
                        i.addClass(closeBits[j]);
                    }
                    results.show();
                } else {
                    var i = toggle.find("i");
                    for (var j = 0; j < closeBits.length; j++) {
                        i.removeClass(closeBits[j]);
                    }
                    for (var j = 0; j < openBits.length; j++) {
                        i.addClass(openBits[j]);
                    }
                    results.hide();
                }
            };

            this.filterToggle = function(element) {
                var filter_id = this.component.jq(element).attr("id");
                var checked = this.component.jq(element).is(":checked");
                if (checked) {
                    this.component.addFilter(filter_id);
                } else {
                    this.component.removeFilter(filter_id);
                }
            };

            this.toggleOpen = function (element) {
                this.open = !this.open;
                this.setUIOpen();
            };
        },

        newORTermSelectorRenderer: function (params) {
            return edges.instantiate(doaj.renderers.ORTermSelectorRenderer, params, edges.newRenderer);
        },
        ORTermSelectorRenderer: function (params) {
            // whether the facet should be open or closed
            // can be initialised and is then used to track internal state
            this.open = edges.getParam(params.open, false);

            this.togglable = edges.getParam(params.togglable, true);

            // whether the count should be displayed along with the term
            // defaults to false because count may be confusing to the user in an OR selector
            this.showCount = edges.getParam(params.showCount, false);

            // whether counts of 0 should prevent the value being rendered
            this.hideEmpty = edges.getParam(params.hideEmpty, false);

            // don't display the facet at all if there is no data to display
            this.hideIfNoData = edges.getParam(params.hideIfNoData, true);

            // namespace to use in the page
            this.namespace = "doaj-or-term-selector";

            this.draw = function () {
                // for convenient short references ...
                var ts = this.component;
                var namespace = this.namespace;

                if (this.hideIfNoData && ts.edge.result && ts.terms.length === 0) {
                    this.component.context.html("");
                    return;
                }

                // sort out all the classes that we're going to be using
                var countClass = edges.css_classes(namespace, "count", this);
                var checkboxClass = edges.css_classes(namespace, "selector", this);

                var toggleId = edges.css_id(namespace, "toggle", this);
                var resultsId = edges.css_id(namespace, "results", this);

                // this is what's displayed in the body if there are no results or the page is loading
                var results = "<li class='loading'><div></div><div></div><div></div><span class='sr-only'>Loading choices…</span></li>";
                if (ts.edge.result) {
                    results = "<li>No data to show</li>";
                }

                // if we want the active filters, render them
                var filterFrag = "";
                if (ts.selected.length > 0) {
                    var resultClass = edges.css_classes(namespace, "result", this);
                    for (var i = 0; i < ts.selected.length; i++) {
                        var filt = ts.selected[i];
                        var display = this.component._translate(filt);
                        let id = edges.safeId(filt);
                        filterFrag += '<li>\
                                <input class="' + checkboxClass + '" data-key="' + edges.escapeHtml(filt) + '" id="' + id + '" type="checkbox" name="' + id + '" checked="checked">\
                                <label for="' + id + '" class="filter__label">' + edges.escapeHtml(display) + '</label>\
                            </li>';
                    }
                }

                // render a list of the values
                if (ts.terms.length > 0) {
                    results = "";

                    for (var i = 0; i < ts.terms.length; i++) {
                        var val = ts.terms[i];
                        if (val.count === 0 && this.hideEmpty) {
                            continue
                        }

                        var active = $.inArray(val.term.toString(), ts.selected) > -1;
                        var checked = "";
                        if (active) {
                            continue;
                            checked = ' checked="checked" ';
                        }
                        var count = "";
                        if (this.showCount) {
                            count = ' <span class="' + countClass + '">(' + val.count + ')</span>';
                        }
                        var id = edges.safeId(val.term);
                        results += '<li>\
                                <input class="' + checkboxClass + '" data-key="' + edges.escapeHtml(val.term) + '" id="' + id + '" type="checkbox" name="' + id + '"' + checked + '>\
                                <label for="' + id + '" class="filter__label">' + edges.escapeHtml(val.display) + count + '</label>\
                            </li>';
                    }

                    /*
                    // render each value, if it is not also a filter that has been set
                    for (var i = 0; i < ts.terms.length; i++) {
                        var val = ts.terms[i];
                        // should we ignore the empty counts
                        if (val.count === 0 && this.hideEmpty) {
                            continue
                        }
                        // otherwise, render any that aren't selected already
                        if ($.inArray(val.term.toString(), ts.selected) === -1) {   // the toString() helps us normalise other values, such as integers
                            results += '<div class="' + resultClass + '"><a href="#" class="' + valClass + '" data-key="' + edges.escapeHtml(val.term) + '">' +
                                edges.escapeHtml(val.display) + "</a>";
                            if (this.showCount) {
                                results += ' <span class="' + countClass + '">(' + val.count + ')</span>';
                            }
                            results += "</div>";
                        }
                    }*/
                }

                /*
                // render the overall facet
                var frag = '<div class="' + facetClass + '">\
                        <div class="' + headerClass + '"><div class="row"> \
                            <div class="col-md-12">\
                                ' + header + '\
                            </div>\
                        </div></div>\
                        <div class="' + bodyClass + '">\
                            <div class="row" style="display:none" id="' + resultsId + '">\
                                <div class="col-md-12">\
                                    {{SELECTED}}\
                                </div>\
                                <div class="col-md-12"><div class="' + selectionsClass + '">\
                                    {{RESULTS}}\
                                </div>\
                            </div>\
                        </div>\
                        </div></div>';
                */

                var toggle = "";
                if (this.togglable) {
                    toggle = '<span data-feather="chevron-down" aria-hidden="true"></span>';
                }
                var frag = '<h3 class="label label--secondary filter__heading" type="button" id="' + toggleId + '">' + this.component.display + toggle + '</h3>\
                    <div class="filter__body collapse" aria-expanded="false" style="height: 0px" id="' + resultsId + '">\
                        <ul class="filter__choices">{{FILTERS}}</ul>\
                    </div>';

                // substitute in the component parts
                frag = frag.replace(/{{FILTERS}}/g, filterFrag + results);

                // now render it into the page
                ts.context.html(frag);
                feather.replace();

                // trigger all the post-render set-up functions
                this.setUIOpen();

                var checkboxSelector = edges.css_class_selector(namespace, "selector", this);
                edges.on(checkboxSelector, "change", this, "filterToggle");

                var toggleSelector = edges.css_id_selector(namespace, "toggle", this);
                edges.on(toggleSelector, "click", this, "toggleOpen");
                /*
                // sort out the selectors we're going to be needing
                var valueSelector = edges.css_class_selector(namespace, "value", this);
                var filterRemoveSelector = edges.css_class_selector(namespace, "filter-remove", this);
                var toggleSelector = edges.css_id_selector(namespace, "toggle", this);

                // for when a value in the facet is selected
                edges.on(valueSelector, "click", this, "termSelected");
                // for when the open button is clicked
                edges.on(toggleSelector, "click", this, "toggleOpen");
                // for when a filter remove button is clicked
                edges.on(filterRemoveSelector, "click", this, "removeFilter");
                 */
            };

            this.setUIOpen = function () {
                // the selectors that we're going to use
                var resultsSelector = edges.css_id_selector(this.namespace, "results", this);
                var toggleSelector = edges.css_id_selector(this.namespace, "toggle", this);

                var results = this.component.jq(resultsSelector);
                var toggle = this.component.jq(toggleSelector);

                if (this.open) {
                    //var i = toggle.find("i");
                    //for (var j = 0; j < openBits.length; j++) {
                    //    i.removeClass(openBits[j]);
                   // }
                    //for (var j = 0; j < closeBits.length; j++) {
                    //    i.addClass(closeBits[j]);
                    //}
                    //results.show();

                    results.addClass("in").attr("aria-expanded", "true").css({"height": ""});
                    toggle.removeClass("collapsed").attr("aria-expanded", "true");
                } else {
                    //var i = toggle.find("i");
                    //for (var j = 0; j < closeBits.length; j++) {
                    //    i.removeClass(closeBits[j]);
                   // }
                    //for (var j = 0; j < openBits.length; j++) {
                     //   i.addClass(openBits[j]);
                    //}
                    //results.hide();

                    results.removeClass("in").attr("aria-expanded", "false").css({"height" : "0px"});
                    toggle.addClass("collapsed").attr("aria-expanded", "false");
                }
            };

            this.filterToggle = function(element) {
                var term = this.component.jq(element).attr("data-key");
                var checked = this.component.jq(element).is(":checked");
                if (checked) {
                    this.component.selectTerm(term);
                } else {
                    this.component.removeFilter(term);
                }
            };

            /*
            this.termSelected = function (element) {
                var term = this.component.jq(element).attr("data-key");
                this.component.selectTerm(term);
            };

            this.removeFilter = function (element) {
                var term = this.component.jq(element).attr("data-key");
                this.component.removeFilter(term);
            };*/

            this.toggleOpen = function (element) {
                this.open = !this.open;
                this.setUIOpen();
            };
        },

        newDateHistogramSelectorRenderer: function (params) {
            return edges.instantiate(doaj.renderers.DateHistogramSelectorRenderer, params, edges.newRenderer);
        },
        DateHistogramSelectorRenderer: function (params) {

            ///////////////////////////////////////
            // parameters that can be passed in

            // whether to hide or just disable the facet if not active
            this.hideInactive = edges.getParam(params.hideInactive, false);

            // whether the facet should be open or closed
            // can be initialised and is then used to track internal state
            this.open = edges.getParam(params.open, false);

            this.togglable = edges.getParam(params.togglable, true);

            // whether to display selected filters
            this.showSelected = edges.getParam(params.showSelected, true);

            this.showCount = edges.getParam(params.showCount, true);

            // formatter for count display
            this.countFormat = edges.getParam(params.countFormat, false);

            // whether to suppress display of date range with no values
            this.hideEmptyDateBin = params.hideEmptyDateBin || true;

            // namespace to use in the page
            this.namespace = "doaj-datehistogram-selector";

            this.draw = function () {
                // for convenient short references ...
                var ts = this.component;
                var namespace = this.namespace;

                if (!ts.active && this.hideInactive) {
                    ts.context.html("");
                    return;
                }

                // sort out all the classes that we're going to be using
                var resultsListClass = edges.css_classes(namespace, "results-list", this);
                var resultClass = edges.css_classes(namespace, "result", this);
                var valClass = edges.css_classes(namespace, "value", this);
                var filterRemoveClass = edges.css_classes(namespace, "filter-remove", this);
                var facetClass = edges.css_classes(namespace, "facet", this);
                var headerClass = edges.css_classes(namespace, "header", this);
                var selectedClass = edges.css_classes(namespace, "selected", this);
                var checkboxClass = edges.css_classes(namespace, "selector", this);
                var countClass = edges.css_classes(namespace, "count", this);

                var toggleId = edges.css_id(namespace, "toggle", this);
                var resultsId = edges.css_id(namespace, "results", this);

                // this is what's displayed in the body if there are no results
                var results = "<li class='loading'><div></div><div></div><div></div><span class='sr-only'>Loading choices…</span></li>";
                if (ts.values !== false) {
                    results = "<li>No data available</li>";
                }

                // render a list of the values
                if (ts.values && ts.values.length > 0) {
                    results = "";

                    // get the terms of the filters that have already been set
                    var filterTerms = [];
                    for (var i = 0; i < ts.filters.length; i++) {
                        filterTerms.push(ts.filters[i].display);
                    }

                    // render each value, if it is not also a filter that has been set
                    for (var i = 0; i < ts.values.length; i++) {
                        var val = ts.values[i];
                        if ($.inArray(val.display, filterTerms) === -1) {

                            var ltData = "";
                            if (val.lt) {
                                ltData = ' data-lt="' + edges.escapeHtml(val.lt) + '" ';
                            }
                            //results += '<div class="' + resultClass + ' ' + myLongClass + '" '  + styles +  '><a href="#" class="' + valClass + '" data-gte="' + edges.escapeHtml(val.gte) + '"' + ltData + '>' +
                            //    edges.escapeHtml(val.display) + "</a> (" + count + ")</div>";

                            var count = "";
                            if (this.showCount) {
                                count = val.count;
                                if (this.countFormat) {
                                    count = this.countFormat(count)
                                }
                                count = ' <span class="' + countClass + '">(' + count + ')</span>';
                            }
                            var id = edges.safeId(val.display.toString());
                            results += '<li>\
                                    <input class="' + checkboxClass + '" data-gte="' + edges.escapeHtml(val.gte) + '"' + ltData + ' id="' + id + '" type="checkbox" name="' + id + '">\
                                    <label for="' + id + '" class="filter__label">' + edges.escapeHtml(val.display) + count + '</label>\
                                </li>';
                        }
                    }
                }

                // if we want the active filters, render them
                var filterFrag = "";
                if (ts.filters.length > 0 && this.showSelected) {
                    for (var i = 0; i < ts.filters.length; i++) {
                        var filt = ts.filters[i];
                        var ltData = "";
                        if (filt.lt) {
                            ltData = ' data-lt="' + edges.escapeHtml(filt.lt) + '" ';
                        }
                        filterFrag += '<li>\
                                    <input checked="checked" class="' + checkboxClass + '" data-gte="' + edges.escapeHtml(val.gte) + '"' + ltData + ' id="' + id + '" type="checkbox" name="' + id + '">\
                                    <label for="' + id + '" class="filter__label">' + edges.escapeHtml(val.display) + '</label>\
                                </li>';

                        /*
                        filterFrag += '<div class="' + resultClass + '"><strong>' + edges.escapeHtml(filt.display) + "&nbsp;";
                        filterFrag += '<a href="#" class="' + filterRemoveClass + '" data-gte="' + edges.escapeHtml(filt.gte) + '"' + ltData + '>';
                        filterFrag += '<i class="glyphicon glyphicon-black glyphicon-remove"></i></a>';
                        filterFrag += "</strong></a></div>";
                         */
                    }
                }

                /*
                // render the toggle capability
                var tog = ts.display;
                if (this.togglable) {
                    tog = '<a href="#" id="' + toggleId + '"><i class="glyphicon glyphicon-plus"></i>&nbsp;' + tog + "</a>";
                }

                // render the overall facet
                var frag = '<div class="' + facetClass + '">\
                        <div class="' + headerClass + '"><div class="row"> \
                            <div class="col-md-12">\
                                ' + tog + '\
                            </div>\
                        </div></div>\
                        ' + tooltipFrag + '\
                        <div class="row" style="display:none" id="' + resultsId + '">\
                            <div class="col-md-12">\
                                <div class="' + selectedClass + '">{{SELECTED}}</div>\
                                <div class="' + resultsListClass + '">{{RESULTS}}</div>\
                            </div>\
                        </div></div>';
                */

                var toggle = "";
                if (this.togglable) {
                    toggle = '<span data-feather="chevron-down" aria-hidden="true"></span>';
                }
                var frag = '<h3 class="label label--secondary filter__heading" type="button" id="' + toggleId + '">' + this.component.display + toggle + '</h3>\
                    <div class="filter__body collapse" aria-expanded="false" style="height: 0px" id="' + resultsId + '">\
                        <ul class="filter__choices">{{FILTERS}}</ul>\
                    </div>';

                // substitute in the component parts
                frag = frag.replace(/{{FILTERS}}/g, filterFrag + results);

                // now render it into the page
                ts.context.html(frag);
                feather.replace();

                // trigger all the post-render set-up functions
                this.setUIOpen();

                var checkboxSelector = edges.css_class_selector(namespace, "selector", this);
                edges.on(checkboxSelector, "change", this, "filterToggle");

                var toggleSelector = edges.css_id_selector(namespace, "toggle", this);
                edges.on(toggleSelector, "click", this, "toggleOpen");

                /*
                // sort out the selectors we're going to be needing
                var valueSelector = edges.css_class_selector(namespace, "value", this);
                var filterRemoveSelector = edges.css_class_selector(namespace, "filter-remove", this);
                var toggleSelector = edges.css_id_selector(namespace, "toggle", this);
                var tooltipSelector = edges.css_id_selector(namespace, "tooltip-toggle", this);
                var shortLongToggleSelector = edges.css_id_selector(namespace, "sl-toggle", this);

                // for when a value in the facet is selected
                edges.on(valueSelector, "click", this, "termSelected");
                // for when the open button is clicked
                edges.on(toggleSelector, "click", this, "toggleOpen");
                // for when a filter remove button is clicked
                edges.on(filterRemoveSelector, "click", this, "removeFilter");
                // toggle the full tooltip
                edges.on(tooltipSelector, "click", this, "toggleTooltip");
                // toggle show/hide full list
                edges.on(shortLongToggleSelector, "click", this, "toggleShortLong");

                 */
            };

            /////////////////////////////////////////////////////
            // UI behaviour functions

            this.setUIOpen = function () {
                // the selectors that we're going to use
                var resultsSelector = edges.css_id_selector(this.namespace, "results", this);
                var toggleSelector = edges.css_id_selector(this.namespace, "toggle", this);

                var results = this.component.jq(resultsSelector);
                var toggle = this.component.jq(toggleSelector);

                if (this.open) {
                    //var i = toggle.find("i");
                    //for (var j = 0; j < openBits.length; j++) {
                    //    i.removeClass(openBits[j]);
                   // }
                    //for (var j = 0; j < closeBits.length; j++) {
                    //    i.addClass(closeBits[j]);
                    //}
                    //results.show();

                    results.addClass("in").attr("aria-expanded", "true").css({"height": ""});
                    toggle.removeClass("collapsed").attr("aria-expanded", "true");
                } else {
                    //var i = toggle.find("i");
                    //for (var j = 0; j < closeBits.length; j++) {
                    //    i.removeClass(closeBits[j]);
                   // }
                    //for (var j = 0; j < openBits.length; j++) {
                     //   i.addClass(openBits[j]);
                    //}
                    //results.hide();

                    results.removeClass("in").attr("aria-expanded", "false").css({"height" : "0px"});
                    toggle.addClass("collapsed").attr("aria-expanded", "false");
                }
            };

            /////////////////////////////////////////////////////
            // event handlers

            this.filterToggle = function(element) {
                var gte = this.component.jq(element).attr("data-gte");
                var lt = this.component.jq(element).attr("data-lt");
                var checked = this.component.jq(element).is(":checked");
                if (checked) {
                    this.component.selectRange({gte: gte, lt: lt});
                } else {
                    this.component.removeFilter({gte: gte, lt: lt});
                }
            };

            /*
            this.termSelected = function (element) {
                var gte = this.component.jq(element).attr("data-gte");
                var lt = this.component.jq(element).attr("data-lt");
                this.component.selectRange({gte: gte, lt: lt});
            };

            this.removeFilter = function (element) {
                var gte = this.component.jq(element).attr("data-gte");
                var lt = this.component.jq(element).attr("data-lt");
                this.component.removeFilter({gte: gte, lt: lt});
            };

             */

            this.toggleOpen = function (element) {
                this.open = !this.open;
                this.setUIOpen();
            };
        },

        newSelectedFiltersRenderer: function (params) {
            return edges.instantiate(doaj.renderers.SelectedFiltersRenderer, params, edges.newRenderer);
        },
        SelectedFiltersRenderer: function (params) {

            this.showFilterField = edges.getParam(params.showFilterField, true);

            this.showSearchString = edges.getParam(params.showSearchString, false);

            this.ifNoFilters = edges.getParam(params.ifNoFilters, false);

            this.hideValues = edges.getParam(params.hideValues, []);

            this.omit = edges.getParam(params.omit, []);

            this.namespace = "doaj-selected-filters";

            this.draw = function () {
                // for convenient short references
                var sf = this.component;
                var ns = this.namespace;

                // sort out the classes we are going to use
                var fieldClass = edges.css_classes(ns, "field", this);
                var fieldNameClass = edges.css_classes(ns, "fieldname", this);
                var valClass = edges.css_classes(ns, "value", this);
                var containerClass = edges.css_classes(ns, "container", this);
                var removeClass = edges.css_classes(ns, "remove", this);

                var filters = "";

                if (this.showSearchString && sf.searchString) {
                    var field = sf.searchField;
                    var text = sf.searchString;
                    filters += '<span class="' + fieldClass + '">';
                    if (field) {
                        if (field in sf.fieldDisplays) {
                            field = sf.fieldDisplays[field];
                        }
                        filters += '<span class="' + fieldNameClass + '">' + field + ':</span>';
                    }
                    filters += '<span class="' + valClass + '">"' + text + '"</span>';
                    filters += '</span>';
                }

                var fields = Object.keys(sf.mustFilters);
                var showClear = false;
                for (var i = 0; i < fields.length; i++) {
                    var field = fields[i];
                    var def = sf.mustFilters[field];

                    // render any compound filters
                    if (def.filter === "compound") {
                        filters += '<li class="tag ' + valClass + '">';
                        filters += '<a href="DELETE" class="' + removeClass + '" data-compound="' + field + '" alt="Remove" title="Remove">';
                        filters += def.display;
                        filters += ' <span data-feather="x" aria-hidden="true"></span>';
                        filters += "</a>";
                        filters += "</li>";
                        showClear = true;
                    } else {
                        if ($.inArray(field, this.omit) > -1) {
                            continue;
                        }
                        showClear = true;

                        // then render any filters that have values
                        for (var j = 0; j < def.values.length; j++) {
                            var val = def.values[j];
                            var valDisplay = ": " + val.display;
                            if ($.inArray(field, this.hideValues) > -1) {
                                valDisplay = "";
                            }
                            filters += '<li class="tag ' + valClass + '">';

                            // the remove block looks different, depending on the kind of filter to remove
                            if (def.filter === "term" || def.filter === "terms") {
                                filters += '<a href="DELETE" class="' + removeClass + '" data-bool="must" data-filter="' + def.filter + '" data-field="' + field + '" data-value="' + val.val + '" alt="Remove" title="Remove">';
                                filters += def.display + valDisplay;
                                filters += ' <span data-feather="x" aria-hidden="true"></span>';
                                filters += "</a>";
                            } else if (def.filter === "range") {
                                var from = val.from ? ' data-' + val.fromType + '="' + val.from + '" ' : "";
                                var to = val.to ? ' data-' + val.toType + '="' + val.to + '" ' : "";
                                filters += '<a href="DELETE" class="' + removeClass + '" data-bool="must" data-filter="' + def.filter + '" data-field="' + field + '" ' + from + to + ' alt="Remove" title="Remove">';
                                filters += def.display + valDisplay;
                                filters += ' <span data-feather="x" aria-hidden="true"></span>';
                                filters += "</a>";
                            }

                            filters += "</li>";
                        }
                    }
                }

                if (showClear) {
                    var clearClass = edges.css_classes(this.namespace, "clear", this);
                    var clearFrag = '<a href="#" class="' + clearClass + '" title="Clear all search and sort parameters and start again"> \
                            CLEAR ALL \
                            <span data-feather="x" aria-hidden="true"></span>\
                        </a>';

                    filters += '<li class="tag tag--secondary ' + valClass + '">' + clearFrag + '</li>';
                }

                if (filters === "" && this.ifNoFilters) {
                    filters = this.ifNoFilters;
                }

                if (filters !== "") {
                    var frag = '<ul class="tags ' + containerClass + '">{{FILTERS}}</ul>';
                    frag = frag.replace(/{{FILTERS}}/g, filters);
                    sf.context.html(frag);
                    feather.replace();

                    // click handler for when a filter remove button is clicked
                    var removeSelector = edges.css_class_selector(ns, "remove", this);
                    edges.on(removeSelector, "click", this, "removeFilter");

                    // click handler for when the clear button is clicked
                    var clearSelector = edges.css_class_selector(ns, "clear", this);
                    edges.on(clearSelector, "click", this, "clearFilters");
                } else {
                    sf.context.html("");
                }
            };

            /////////////////////////////////////////////////////
            // event handlers

            this.removeFilter = function (element) {
                var el = this.component.jq(element);

                // if this is a compound filter, remove it by id
                var compound = el.attr("data-compound");
                if (compound) {
                    this.component.removeCompoundFilter({compound_id: compound});
                    return;
                }

                // otherwise follow the usual instructions for removing a filter
                var field = el.attr("data-field");
                var ft = el.attr("data-filter");
                var bool = el.attr("data-bool");

                var value = false;
                if (ft === "terms" || ft === "term") {
                    value = el.attr("data-value");
                } else if (ft === "range") {
                    value = {};

                    var from = el.attr("data-gte");
                    var fromType = "gte";
                    if (!from) {
                        from = el.attr("data-gt");
                        fromType = "gt";
                    }

                    var to = el.attr("data-lt");
                    var toType = "lt";
                    if (!to) {
                        to = el.attr("data-lte");
                        toType = "lte";
                    }

                    if (from) {
                        value["from"] = parseInt(from);
                        value["fromType"] = fromType;
                    }
                    if (to) {
                        value["to"] = parseInt(to);
                        value["toType"] = toType;
                    }
                }

                this.component.removeFilter(bool, ft, field, value);
            };

            this.clearFilters = function() {
                this.component.clearSearch();
            }
        },

        newPagerRenderer: function (params) {
            return edges.instantiate(doaj.renderers.PagerRenderer, params, edges.newRenderer);
        },
        PagerRenderer: function (params) {

            this.numberFormat = edges.getParam(params.numberFormat, false);

            this.namespace = "doaj-pager";

            this.draw = function () {
                if (this.component.total === false || this.component.total === 0) {
                    this.component.context.html("");
                    return;
                }

                // classes we'll need
                var navClass = edges.css_classes(this.namespace, "nav", this);
                var firstClass = edges.css_classes(this.namespace, "first", this);
                var prevClass = edges.css_classes(this.namespace, "prev", this);
                var pageClass = edges.css_classes(this.namespace, "page", this);
                var nextClass = edges.css_classes(this.namespace, "next", this);

                var first = '<li><span data-feather="chevrons-left" aria-hidden="true"></span> <a href="#" class="' + firstClass + '">First</a></li>';
                var prev = '<li><span data-feather="chevron-left" aria-hidden="true"></span> <a href="#" class="' + prevClass + '">Prev</a></li>';
                if (this.component.page === 1) {
                    first = '<li><span data-feather="chevrons-left" aria-hidden="true"></span> First</li>';
                    prev = '<li><span data-feather="chevron-left" aria-hidden="true"></span> Prev</li>';
                }

                var next = '<li><a href="#" class="' + nextClass + '">Next <span data-feather="chevron-right" aria-hidden="true"></span></a></li>';
                if (this.component.page === this.component.totalPages) {
                    next = '<li>Next <span data-feather="chevron-right" aria-hidden="true"></span></li>';
                }

                var pageNum = this.component.page;
                var totalPages = this.component.totalPages;
                if (this.numberFormat) {
                    pageNum = this.numberFormat(pageNum);
                    totalPages = this.numberFormat(totalPages);
                }
                var nav = '<h3 class="sr-only">Jump to&hellip;</h3><ul class="' + navClass + '">' + first + prev +
                    '<li class="' + pageClass + '"><strong>Page ' + pageNum + ' of ' + totalPages + '</strong></li>' +
                    next + "</ul>";

                this.component.context.html(nav);
                feather.replace();

                // now create the selectors for the functions
                var firstSelector = edges.css_class_selector(this.namespace, "first", this);
                var prevSelector = edges.css_class_selector(this.namespace, "prev", this);
                var nextSelector = edges.css_class_selector(this.namespace, "next", this);

                // bind the event handlers
                if (this.component.page !== 1) {
                    edges.on(firstSelector, "click", this, "goToFirst");
                    edges.on(prevSelector, "click", this, "goToPrev");
                }
                if (this.component.page !== this.component.totalPages) {
                    edges.on(nextSelector, "click", this, "goToNext");
                }
            };

            this.goToFirst = function (element) {
                this.component.setFrom(1);
            };

            this.goToPrev = function (element) {
                this.component.decrementPage();
            };

            this.goToNext = function (element) {
                this.component.incrementPage();
            };
        },

        newPublicSearchResultRenderer : function(params) {
            return edges.instantiate(doaj.renderers.PublicSearchResultRenderer, params, edges.newRenderer);
        },
        PublicSearchResultRenderer : function(params) {

            this.widget = params.widget;
            if (params.doaj_url) {
                this.doaj_url = params.doaj_url;
            }
            else {
                this.doaj_url = ""
            }

            this.actions = edges.getParam(params.actions, []);

            this.namespace = "doaj-public-search";

            this.selector = edges.getParam(params.selector, null)
            this.currentQueryString  = "";


            this.draw = function () {
                if (this.component.edge.currentQuery){
                    let qs = this.component.edge.currentQuery.getQueryString();
                    if (qs) {
                        this.currentQueryString = qs.queryString || "";
                    }
                }
                var frag = "<li class='alert'><p>You searched for ‘<i>";
                frag += edges.escapeHtml(this.currentQueryString);
                frag += "</i>’ and we found no results.</p>";
                frag += "<p>Please try the following:</p><ul>\
                    <li>Check the spelling and make sure that there are no missing characters.</li>\
                    <li>Use fewer words in your search to make the search less specific.</li>\
                    <li>Remove some of the filters you have set.</li>\
                    <li>Do your search again in English as much of the index uses English terms.</li>\
                    </ul></li>\
                ";

                if (this.component.results === false) {
                    frag = "";
                }

                var results = this.component.results;
                if (results && results.length > 0) {
                    // now call the result renderer on each result to build the records
                    frag = "";
                    for (var i = 0; i < results.length; i++) {
                        frag += this._renderResult(results[i]);
                    }
                }

                this.component.context.html(frag);
                feather.replace();

                // now bind the abstract expander
                var abstractAction = edges.css_class_selector(this.namespace, "abstractaction", this);
                edges.on(abstractAction, "click", this, "toggleAbstract");
            };

            this.toggleAbstract = function(element) {
                var el = $(element);
                var abstractText = edges.css_class_selector(this.namespace, "abstracttext", this);
                var at = this.component.jq(abstractText).filter('[rel="' + el.attr("rel") + '"]');

                if (el.attr("aria-expanded") === "false") {
                    el.removeClass("collapsed").attr("aria-expanded", "true");
                    at.addClass("in").attr("aria-expanded", "true");
                } else {
                    el.addClass("collapsed").attr("aria-expanded", "false");
                    at.removeClass("in").attr("aria-expanded", "false");
                }
            };

            this._renderResult = function(resultobj) {
                if (resultobj.bibjson && resultobj.bibjson.journal) {
                    // it is an article
                    return this._renderPublicArticle(resultobj);
                } else {
                    // it is a journal
                    return this._renderPublicJournal(resultobj);
                }
            };

            this._renderPublicJournal = function(resultobj) {

                var seal = "";
                if (edges.objVal("admin.seal", resultobj, false)) {
                    seal = '<a href="' + this.doaj_url + '/apply/seal" class="tag tag--featured" target="_blank">'
                    if (this.widget){
                        seal += '<img src="' + this.doaj_url + '/static/doaj/images/feather-icons/check-circle.svg" alt="check-circle icon">'
                    }
                    else {
                        seal += '<i data-feather="check-circle" aria-hidden="true"></i>'
                    }
                    seal += ' DOAJ Seal</a>';
                }
                var issn = resultobj.bibjson.pissn;
                if (!issn) {
                    issn = resultobj.bibjson.eissn;
                }
                if (issn) {
                    issn = edges.escapeHtml(issn);
                }

                var subtitle = "";
                if (edges.hasProp(resultobj, "bibjson.alternative_title")) {
                    subtitle = '<span class="search-results__subheading">' + edges.escapeHtml(resultobj.bibjson.alternative_title) + '</span>';
                }

                var published = "";
                if (edges.hasProp(resultobj, "bibjson.publisher")) {
                    var name = "";
                    var country = "";
                    if (resultobj.bibjson.publisher.name) {
                        name = 'by <em>' + edges.escapeHtml(resultobj.bibjson.publisher.name) + '</em>';
                    }
                    if (resultobj.bibjson.publisher.country && edges.hasProp(resultobj, "index.country")) {
                        country = 'in <strong>' + edges.escapeHtml(resultobj.index.country) + '</strong>';
                    }
                    published = 'Published ' + name + " " + country;
                }

                // add the subjects
                var subjects = "";
                if (edges.hasProp(resultobj, "index.classification_paths") && resultobj.index.classification_paths.length > 0) {
                    subjects = "<li>" + resultobj.index.classification_paths.join("</li><li>") + "</li>";
                }

                var update_or_added = "";
                if (resultobj.last_manual_update && resultobj.last_manual_update !== '1970-01-01T00:00:00Z') {
                    update_or_added = 'Last updated on ' + doaj.humanDate(resultobj.last_manual_update);
                } else {
                    update_or_added = 'Added on ' + doaj.humanDate(resultobj.created_date);
                }

                // FIXME: this is to present the number of articles indexed, which is not information we currently possess
                // at search time
                var articles = "";

                var apcs = '<li>';
                if (edges.hasProp(resultobj, "bibjson.apc.max") && resultobj.bibjson.apc.max.length > 0) {
                    apcs += "APCs: ";
                    let length = resultobj.bibjson.apc.max.length;
                    for (var i = 0; i < length; i++) {
                        apcs += "<strong>";
                        var apcRecord = resultobj.bibjson.apc.max[i];
                        if (apcRecord.hasOwnProperty("price")) {
                            apcs += edges.escapeHtml(apcRecord.price);
                        }
                        if (apcRecord.currency) {
                            apcs += ' (' + edges.escapeHtml(apcRecord.currency) + ')';
                        }
                        if (i < length - 1) {
                            apcs += ', ';
                        }
                        apcs += "</strong>";
                    }
                } else {
                    apcs += "<strong>No</strong> charges";
                }
                apcs += '</li>';

                var licenses = "";
                if (resultobj.bibjson.license && resultobj.bibjson.license.length > 0) {
                    var terms_url = resultobj.bibjson.ref.license_terms;
                    for (var i = 0; i < resultobj.bibjson.license.length; i++) {
                        var lic = resultobj.bibjson.license[i];
                        var license_url = lic.url || terms_url;
                        licenses += '<a href="' + license_url + '" target="_blank" rel="noopener">' + edges.escapeHtml(lic.type) + '</a>';
                        if (i != (resultobj.bibjson.license.length-1)) {
                            licenses += ', ';
                        }
                    }
                }

                var language = "";
                if (resultobj.index.language && resultobj.index.language.length > 0) {
                    language = '<li>\
                              Accepts manuscripts in <strong>' + resultobj.index.language.join(", ") + '</strong>\
                            </li>';
                }

                var actions = "";
                if (this.actions.length > 0) {
                    actions = '<h4 class="label">Actions</h4><ul class="tags">';
                    for (var i = 0; i < this.actions.length; i++) {
                        var act = this.actions[i];
                        var actSettings = act(resultobj);
                        if (actSettings) {
                            actions += '<li class="tag">\
                                <a href="' + actSettings.link + '">' + actSettings.label + '</a>\
                            </li>';
                        }
                    }
                    actions += '</ul>';
                }

                var frag = '<li class="card search-results__record">\
                    <article class="row">\
                      <div class="col-sm-8 search-results__main">\
                        <header>\
                          ' + seal + '\
                          <h3 class="search-results__heading">\
                            <a href="' + this.doaj_url + '/toc/' + issn + '" target="_blank">\
                              ' + edges.escapeHtml(resultobj.bibjson.title) + '\
                              <sup>'
                if (this.widget){
                    frag += '<img src="' + this.doaj_url + '/static/doaj/images/feather-icons/link.svg" alt="link icon">'
                }
                else {
                    frag += '<i data-feather="link" aria-hidden="true"></i>'
                }


                frag +='</sup>\
                            </a>\
                            ' + subtitle + '\
                          </h3>\
                        </header>\
                        <div class="search-results__body">\
                          <ul class="inlined-list">\
                            <li>\
                              ' + published + '\
                            </li>\
                            ' + language + '\
                          </ul>\
                          <ul>\
                            ' + subjects + '\
                          </ul>\
                        </div>\
                      </div>\
                      <aside class="col-sm-4 search-results__aside">\
                        <ul>\
                          <li>\
                            ' + update_or_added + '\
                          </li>\
                          ' + articles + '\
                          <li>\
                            <a href="' + resultobj.bibjson.ref.journal + '" target="_blank" rel="noopener">Website '

                if (this.widget){
                    frag += '<img src="' + this.doaj_url + '/static/doaj/images/feather-icons/external-link.svg" alt="external-link icon">'
                }
                else {
                    frag += '<i data-feather="external-link" aria-hidden="true"></i>'
                }



                frag += '</a></li>\
                          <li>\
                            ' + apcs + '\
                          </li>\
                          <li>\
                            ' + licenses + '\
                          </li>\
                        </ul>\
                        ' + actions + '\
                      </aside>\
                    </article>\
                  </li>';

                return frag;
            };

            this._renderPublicArticle = function(resultobj) {
                var journal = resultobj.bibjson.journal ? resultobj.bibjson.journal.title : "";

                var date = "";
                if (resultobj.index.date) {
                    let humanised = doaj.humanYearMonth(resultobj.index.date);
                    if (humanised) {
                        date = "(" + humanised + ")";
                    }
                }

                var title = "";
                if (resultobj.bibjson.title) {
                    title = edges.escapeHtml(resultobj.bibjson.title);
                }

                // set the authors
                var authors = "";
                if (edges.hasProp(resultobj, "bibjson.author") && resultobj.bibjson.author.length > 0) {
                    authors = '<ul class="inlined-list">';
                    var anames = [];
                    var bauthors = resultobj.bibjson.author;
                    for (var i = 0; i < bauthors.length; i++) {
                        var author = bauthors[i];
                        if (author.name) {
                            var field = edges.escapeHtml(author.name);
                            anames.push(field);
                        }
                    }
                    authors += '<li>' + anames.join(",&nbsp;</li><li>") + '</li>';
                    authors += '</ul>';

                }

                var keywords = "";
                if (edges.hasProp(resultobj, "bibjson.keywords") && resultobj.bibjson.keywords.length > 0) {
                    keywords = '<h4>Article keywords</h4><ul class="inlined-list">';
                    keywords+= '<li>' + resultobj.bibjson.keywords.join(",&nbsp;</li><li>") + '</li>';
                    keywords += '</ul>';
                }

                var subjects = "";
                if (edges.hasProp(resultobj, "index.classification_paths") && resultobj.index.classification_paths.length > 0) {
                    subjects = '<h4>Journal subjects</h4><ul>';
                    subjects += "<li>" + resultobj.index.classification_paths.join("<br>") + "</li>";
                    subjects += '</ul>';
                }

                var subjects_or_keywords = keywords === "" ? subjects : keywords;

                var abstract = "";
                if (resultobj.bibjson.abstract) {
                    var abstractAction = edges.css_classes(this.namespace, "abstractaction", this);
                    var abstractText = edges.css_classes(this.namespace, "abstracttext", this);

                    abstract = '<h4 class="' + abstractAction + '" type="button" aria-expanded="false" rel="' + resultobj.id + '">\
                            Abstract'
                    if (this.widget){
                        abstract += '<img src="' + this.doaj_url + '/static/doaj/images/feather-icons/plus.svg" alt="external-link icon">'
                    }
                    else {
                        abstract += '<i data-feather="plus" aria-hidden="true"></i>'
                    }
                    abstract += '</h4>\
                          <p rel="' + resultobj.id + '" class="collapse ' + abstractText + '" aria-expanded="false">\
                            ' + edges.escapeHtml(resultobj.bibjson.abstract) + '\
                          </p>';
                }

                var doi_url = false;
                if (resultobj.bibjson && resultobj.bibjson.identifier) {
                    var ids = resultobj.bibjson.identifier;
                    for (var i = 0; i < ids.length; i++) {
                        if (ids[i].type === "doi") {
                            var doi = ids[i].id;
                            var tendot = doi.indexOf("10.");
                            doi_url = "https://doi.org/" + edges.escapeHtml(doi.substring(tendot));
                        }
                    }
                }

                var ftl = false;
                if (edges.hasProp(resultobj, "bibjson.link") && resultobj.bibjson.link.length !== 0) {
                    var ls = resultobj.bibjson.link;
                    for (var i = 0; i < ls.length; i++) {
                        var t = ls[i].type;
                        if (t === 'fulltext') {
                            ftl = ls[i].url;
                        }
                    }
                } else if (doi_url) {
                    ftl = doi_url;
                }

                var issns = [];
                if (resultobj.bibjson && resultobj.bibjson.identifier) {
                    var ids = resultobj.bibjson.identifier;
                    for (var i = 0; i < ids.length; i++) {
                        if (ids[i].type === "pissn" || ids[i].type === "eissn") {
                            issns.push(edges.escapeHtml(ids[i].id))
                        }
                    }
                }
                // We have stopped syncing journal license to articles: https://github.com/DOAJ/doajPM/issues/2548
                /*
                var license = "";
                if (edges.hasProp(resultobj, "bibjson.journal.license") && resultobj.bibjson.journal.license.length > 0) {
                    for (var i = 0; i < resultobj.bibjson.journal.license.length; i++) {
                        var lic = resultobj.bibjson.journal.license[i];
                        license += '<a href="' + lic.url + '" target="_blank" rel="noopener">' + lic.type + '</a> ';
                    }
                }
                */

                var published = "";
                if (edges.hasProp(resultobj, "bibjson.journal.publisher")) {
                    var name = 'by <em>' + edges.escapeHtml(resultobj.bibjson.journal.publisher) + '</em>';
                    published = 'Published ' + name;
                }

                var frag = '<li class="card search-results__record">\
                    <article class="row">\
                      <div class="col-sm-8 search-results__main">\
                        <header>\
                          <p class="label"><a href="' + this.doaj_url + '/toc/' + issns[0] + '" target="_blank">\
                            ' + edges.escapeHtml(journal) + ' ' + date + '\
                          </a></p>\
                          <h3 class="search-results__heading">\
                            <a href="' + this.doaj_url + '/article/' + resultobj.id + '" class="" target="_blank">\
                              ' + title + '\
                            </a>\
                          </h3>\
                          ' + authors + '\
                        </header>\
                        <div class="search-results__body">\
                          ' + subjects_or_keywords + '\
                          ' + abstract + '\
                        </div>\
                      </div>\
                      <aside class="col-sm-4 search-results__aside">\
                        <ul>\
                          <li>\
                            <a href="' + ftl + '" target="_blank" rel="noopener"> Read online '
                if (this.widget){
                    frag += '<img src="' + this.doaj_url + '/static/doaj/images/feather-icons/external-link.svg" alt="external-link icon">'
                }
                else {
                    frag += '<i data-feather="external-link" aria-hidden="true"></i>'
                }
                frag += '</a></li>\
                          <li>\
                            <a href="' + this.doaj_url + '/toc/' + issns[0] + '" target="_blank" rel="noopener">About the journal</a>\
                          </li>\
                          <li>\
                            ' + published + '\
                          </li>\
                        </ul>\
                      </aside>\
                    </article></li>';
                        /*
                         <li>\
                            ' + license + '\
                         </li>\
                         */
                // close off the result and return
                return frag;
            };
        },

        newPublisherApplicationRenderer : function(params) {
            return edges.instantiate(doaj.renderers.PublisherApplicationRenderer, params, edges.newRenderer);
        },
        PublisherApplicationRenderer : function(params) {

            this.actions = edges.getParam(params.actions, []);

            this.namespace = "doaj-publisher-application";

            this.statusMap = {
                "draft" : "Not yet submitted",
                "accepted" : "Accepted to DOAJ",
                "rejected" : "Application rejected",
                "update_request" : "Pending",
                "revisions_required" : "Revisions Required",
                "pending" : "Pending",
                "in progress" : "Under review by an editor",
                "completed" : "Under review by an editor",
                "on hold" : "Under review by an editor",
                "ready" : "Under review by an editor"
            };

            this.draw = function () {
                var frag = "You do not have any applications yet";
                if (this.component.results === false) {
                    frag = "";
                }

                var results = this.component.results;
                if (results && results.length > 0) {
                    // now call the result renderer on each result to build the records
                    frag = "";
                    for (var i = 0; i < results.length; i++) {
                        frag += this._renderResult(results[i]);
                    }

                    var deleteTitleClass = edges.css_classes(this.namespace, "delete-title", this);
                    var deleteLinkClass = edges.css_classes(this.namespace, "delete-link", this);

                    frag += '<section class="modal in" id="modal-delete-application" tabindex="-1" role="dialog" style="display: none;"> \
                        <div class="modal__dialog" role="document">\
                            <header class="flex-space-between modal__heading"> \
                                <h2 class="modal__title">Delete this application</h2>\
                              <span type="button" data-dismiss="modal" class="type-01"><span class="sr-only">Close</span>&times;</span>\
                            </header>\
                            <p>Are you sure you want to delete your application for <strong><span class="' + deleteTitleClass + '"></span></strong>?</p> \
                            <a href="#" class="button button--primary ' + deleteLinkClass + '" role="button">Yes, delete it</a> <button class="button button--tertiary" data-dismiss="modal" class="modal__close">No</button>\
                        </div>\
                    </section>';
                }

                this.component.context.html(frag);
                feather.replace();

                // bindings for delete link handling
                var deleteSelector = edges.css_class_selector(this.namespace, "delete", this);
                edges.on(deleteSelector, "click", this, "deleteLinkClicked");
            };

            this.deleteLinkClicked = function(element) {
                var deleteTitleSelector = edges.css_class_selector(this.namespace, "delete-title", this);
                var deleteLinkSelector = edges.css_class_selector(this.namespace, "delete-link", this);

                var el = $(element);
                var href = el.attr("href");
                var title = el.attr("data-title");

                this.component.jq(deleteTitleSelector).html(title);
                this.component.jq(deleteLinkSelector).attr("href", href);
            };

            this._accessLink = function(resultobj) {
                if (resultobj.es_type === "draft_application") {
                    // if it's a draft, just link to the draft edit page
                    return [doaj.publisherApplicationsSearchConfig.applyUrl + resultobj['id'], "Edit"];
                } else {
                    var status = resultobj.admin.application_status;

                    // if it's an accepted application, link to the ToC
                    if (status === "accepted") {
                        var issn = resultobj.bibjson.pissn;
                        if (!issn) {
                            issn = resultobj.bibjson.eissn;
                        }
                        if (issn) {
                            issn = edges.escapeHtml(issn);
                        }
                        return [doaj.publisherApplicationsSearchConfig.tocUrl + issn, "View"];
                        // otherwise just link to the view page
                    } else {
                        return [doaj.publisherApplicationsSearchConfig.journalReadOnlyUrl + resultobj['id'], "View"];
                    }
                }
            };

            this._renderResult = function(resultobj) {

                var accessLink = this._accessLink(resultobj);

                var titleText = "Untitled";
                if (edges.hasProp(resultobj, "bibjson.title")) {
                    titleText = edges.escapeHtml(resultobj.bibjson.title);
                }
                var title = titleText;
                if (accessLink) {
                    title = '<a href="' + accessLink[0] + '">' + title + '</a>';
                }

                var subtitle = "";
                if (edges.hasProp(resultobj, "bibjson.alternative_title")) {
                    subtitle = '<span class="search-results__subheading">' + edges.escapeHtml(resultobj.bibjson.alternative_title) + '</span>';
                }

                var status = "";
                if (edges.hasProp(resultobj, "admin.application_status")) {
                    status = this.statusMap[resultobj.admin.application_status];
                    if (!status) {
                        status = "Status is unspecified";
                    }
                } else {
                    status = "Not yet submitted";
                }

                var completion = "";
                if (resultobj.es_type === "draft_application") {
                    // FIXME: how do we calculate completion
                }

                var last_updated = "Last updated ";
                last_updated += doaj.humanDate(resultobj.last_updated);

                var icon = "edit-3";
                if (accessLink[1] === "View") {
                    icon = "eye";
                }
                var viewOrEdit = '<li class="tag">\
                    <a href="' + accessLink[0] + '">\
                        <span data-feather="' + icon + '" aria-hidden="true"></span>\
                        <span>' + accessLink[1] + '</span>\
                    </a>\
                </li>';

                var deleteLink = "";
                var deleteLinkTemplate = doaj.publisherApplicationsSearchConfig.deleteLinkTemplate;
                var deleteLinkUrl = deleteLinkTemplate.replace("__application_id__", resultobj.id);
                var deleteClass = edges.css_classes(this.namespace, "delete", this);
                if (resultobj.es_type === "draft_application" ||
                        resultobj.admin.application_status === "update_request") {
                    deleteLink = '<li class="tag">\
                        <a href="' + deleteLinkUrl + '"  data-toggle="modal" data-target="#modal-delete-application" class="' + deleteClass + '"\
                            data-title="' + titleText + '">\
                            <span data-feather="trash-2" aria-hidden="true"></span>\
                            <span>Delete</span>\
                        </a>\
                    </li>';
                }

                var frag = '<li class="card search-results__record">\
                    <article class="row">\
                      <div class="col-sm-4 search-results__main">\
                        <header>\
                          <h3 class="search-results__heading">\
                            ' + title + '\
                            ' + subtitle + '\
                          </h3>\
                        </header>\
                      </div>\
                      <aside class="col-sm-4 search-results__aside">\
                        <h4 class="label">Status</h4>\
                        <ul>\
                          <li>\
                            <strong>' + status + '</strong>\
                          </li>\
                          ' + completion + '\
                          <li>\
                            ' + last_updated + '\
                          </li>\
                        </ul>\
                      </aside>\
                      <div class="col-sm-4 search-results__aside">\
                        <h4 class="label">Actions</h4>\
                        <ul class="tags">\
                            ' + viewOrEdit + '\
                            ' + deleteLink + '\
                        </ul>\
                      </div>\
                    </article>\
                  </li>';

                return frag;
            };
        },

        newPublisherUpdateRequestRenderer : function(params) {
            return edges.instantiate(doaj.renderers.PublisherUpdateRequestRenderer, params, edges.newRenderer);
        },
        PublisherUpdateRequestRenderer : function(params) {

            this.actions = edges.getParam(params.actions, []);

            this.namespace = "doaj-publisher-update-request";

            this.statusMap = {
                "accepted" : "Accepted to DOAJ",
                "rejected" : "Application rejected",
                "update_request" : "Pending",
                "revisions_required" : "Revisions Required",
                "pending" : "Pending",
                "in progress" : "Under review by an editor",
                "completed" : "Under review by an editor",
                "on hold" : "Under review by an editor",
                "ready" : "Under review by an editor"
            };

            this.draw = function () {
                var frag = "You do not have any update requests yet";
                if (this.component.results === false) {
                    frag = "";
                }

                var results = this.component.results;
                if (results && results.length > 0) {
                    // now call the result renderer on each result to build the records
                    frag = "";
                    for (var i = 0; i < results.length; i++) {
                        frag += this._renderResult(results[i]);
                    }

                    var deleteTitleClass = edges.css_classes(this.namespace, "delete-title", this);
                    var deleteLinkClass = edges.css_classes(this.namespace, "delete-link", this);

                    frag += '<section class="modal in" id="modal-delete-update-request" tabindex="-1" role="dialog" style="display: none;"> \
                        <div class="modal__dialog" role="document">\
                            <header class="flex-space-between modal__heading">\
                              <h2 class="modal__title">Delete this update request</h2>\
                              <span type="button" data-dismiss="modal" class="type-01"><span class="sr-only">Close</span>&times;</span>\
                            </header>\
                            <p>Are you sure you want to delete your update request for <strong><span class="' + deleteTitleClass + '"></span></strong>?</p> \
                            <a href="#" class="button button--primary ' + deleteLinkClass + '" role="button">Yes, delete it</a> <button class="button button--tertiary" data-dismiss="modal" class="modal__close">No</button>\
                        </div>\
                    </section>';
                }

                this.component.context.html(frag);
                feather.replace();

                // bindings for delete link handling
                var deleteSelector = edges.css_class_selector(this.namespace, "delete", this);
                edges.on(deleteSelector, "click", this, "deleteLinkClicked");
            };

            this._renderResult = function(resultobj) {
                var accessLink = this._accessLink(resultobj);

                var titleText = "Untitled";
                if (edges.hasProp(resultobj, "bibjson.title")) {
                    titleText = edges.escapeHtml(resultobj.bibjson.title);
                }
                var title = titleText;
                if (accessLink) {
                    title = '<a href="' + accessLink[0] + '">' + title + '</a>';
                }

                var subtitle = "";
                if (edges.hasProp(resultobj, "bibjson.alternative_title")) {
                    subtitle = '<span class="search-results__subheading">' + edges.escapeHtml(resultobj.bibjson.alternative_title) + '</span>';
                }

                var status = "";
                if (edges.hasProp(resultobj, "admin.application_status")) {
                    status = this.statusMap[resultobj.admin.application_status];
                    if (!status) {
                        status = "Status is unspecified";
                    }
                } else {
                    status = "Not yet submitted";
                }

                var completion = "";
                if (resultobj.es_type === "draft_application") {
                    // FIXME: how do we calculate completion
                }

                var last_updated = "Last updated ";
                last_updated += doaj.humanDate(resultobj.last_updated);

                /*
                var icon = "edit-3";
                if (accessLink[1] === "View") {
                    icon = "eye";
                }
                var viewOrEdit = '<li class="tag">\
                    <a href="' + accessLink[0] + '">\
                        <span data-feather="' + icon + '" aria-hidden="true"></span>\
                        <span>' + accessLink[1] + '</span>\
                    </a>\
                </li>';
                 */

                var deleteLink = "";
                var deleteLinkTemplate = doaj.publisherUpdatesSearchConfig.deleteLinkTemplate;
                var deleteLinkUrl = deleteLinkTemplate.replace("__application_id__", resultobj.id);
                var deleteClass = edges.css_classes(this.namespace, "delete", this);
                if (resultobj.es_type === "draft_application" ||
                    resultobj.admin.application_status === "update_request") {
                    deleteLink = '<li class="tag">\
                        <a href="' + deleteLinkUrl + '"  data-toggle="modal" data-target="#modal-delete-update-request" class="' + deleteClass + '"\
                            data-title="' + titleText + '">\
                            <span data-feather="trash-2" aria-hidden="true"></span>\
                            <span>Delete</span>\
                        </a>\
                    </li>';
                }

                var actions = "";
                if (this.actions.length > 0) {
                    actions = '<h4 class="label">Actions</h4><ul class="tags">';
                    for (var i = 0; i < this.actions.length; i++) {
                        var act = this.actions[i];
                        var actSettings = act(resultobj);
                        if (actSettings) {
                            actions += '<li class="tag">\
                                <a href="' + actSettings.link + '">' + actSettings.label + '</a>\
                            </li>';
                        }
                    }
                    actions += deleteLink;
                    actions += '</ul>';
                }



                var frag = '<li class="card search-results__record">\
                    <article class="row">\
                      <div class="col-sm-4 search-results__main">\
                        <header>\
                          <h3 class="search-results__heading">\
                            ' + title + '\
                            ' + subtitle + '\
                          </h3>\
                        </header>\
                      </div>\
                      <aside class="col-sm-4 search-results__aside">\
                        <h4 class="label">Status</h4>\
                        <ul>\
                          <li>\
                            <strong>' + status + '</strong>\
                          </li>\
                          ' + completion + '\
                          <li>\
                            ' + last_updated + '\
                          </li>\
                        </ul>\
                      </aside>\
                      <div class="col-sm-4 search-results__aside">\
                        ' + actions + '\
                      </div>\
                    </article>\
                  </li>';

                return frag;
            };

            this.deleteLinkClicked = function(element) {
                var deleteTitleSelector = edges.css_class_selector(this.namespace, "delete-title", this);
                var deleteLinkSelector = edges.css_class_selector(this.namespace, "delete-link", this);

                var el = $(element);
                var href = el.attr("href");
                var title = el.attr("data-title");

                this.component.jq(deleteTitleSelector).html(title);
                this.component.jq(deleteLinkSelector).attr("href", href);
            };

            this._accessLink = function(resultobj) {
                var status = resultobj.admin.application_status;

                // if it's an accepted application, link to the ToC
                if (status === "accepted") {
                    var issn = resultobj.bibjson.pissn;
                    if (!issn) {
                        issn = resultobj.bibjson.eissn;
                    }
                    if (issn) {
                        issn = edges.escapeHtml(issn);
                    }
                    return [doaj.publisherUpdatesSearchConfig.tocUrl + issn, "View"];
                    // otherwise just link to the view page
                } else {
                    return [doaj.publisherUpdatesSearchConfig.journalReadOnlyUrl + resultobj['id'], "View"];
                }
            };

            this._renderPublicJournal = function(resultobj) {
                var seal = "";
                if (edges.objVal("admin.seal", resultobj, false)) {
                    seal = '<a href="/apply/seal" class="tag tag--featured" target="_blank">\
                            <span data-feather="check-circle" aria-hidden="true"></span>\
                            DOAJ Seal\
                          </a>';
                }
                var issn = resultobj.bibjson.pissn;
                if (!issn) {
                    issn = resultobj.bibjson.eissn;
                }
                if (issn) {
                    issn = edges.escapeHtml(issn);
                }

                var subtitle = "";
                if (edges.hasProp(resultobj, "bibjson.alternative_title")) {
                    subtitle = '<span class="search-results__subheading">' + edges.escapeHtml(resultobj.bibjson.alternative_title) + '</span>';
                }

                var published = "";
                if (edges.hasProp(resultobj, "bibjson.publisher")) {
                    var name = "";
                    var country = "";
                    if (resultobj.bibjson.publisher.name) {
                        name = 'by <em>' + edges.escapeHtml(resultobj.bibjson.publisher.name) + '</em>';
                    }
                    if (resultobj.bibjson.publisher.country && edges.hasProp(resultobj, "index.country")) {
                        country = 'in <strong>' + edges.escapeHtml(resultobj.index.country) + '</strong>';
                    }
                    published = 'Published ' + name + " " + country;
                }

                // add the subjects
                var subjects = "";
                if (edges.hasProp(resultobj, "index.classification_paths") && resultobj.index.classification_paths.length > 0) {
                    subjects = "<li>" + resultobj.index.classification_paths.join("</li><li>") + "</li>";
                }

                var update_or_added = "";
                if (resultobj.last_manual_update && resultobj.last_manual_update !== '1970-01-01T00:00:00Z') {
                    update_or_added = 'Last updated on ' + doaj.humanDate(resultobj.last_manual_update);
                } else {
                    update_or_added = 'Added on ' + doaj.humanDate(resultobj.created_date);
                }

                // FIXME: this is to present the number of articles indexed, which is not information we currently possess
                // at search time
                var articles = "";

                var apcs = '<li>';
                if (edges.hasProp(resultobj, "bibjson.apc.max") && resultobj.bibjson.apc.max.length > 0) {
                    apcs += "APCs: ";
                    let length = resultobj.bibjson.apc.max.length;
                    for (var i = 0; i < length; i++) {
                        apcs += "<strong>";
                        var apcRecord = resultobj.bibjson.apc.max[i];
                        if (apcRecord.hasOwnProperty("price")) {
                            apcs += edges.escapeHtml(apcRecord.price);
                        }
                        if (apcRecord.currency) {
                            apcs += ' (' + edges.escapeHtml(apcRecord.currency) + ')';
                        }
                        if (i < length - 1) {
                            apcs += ', ';
                        }
                        apcs += "</strong>";
                    }
                } else {
                    apcs += "<strong>No</strong> charges";
                }
                apcs += '</li>';

                var licenses = "";
                if (resultobj.bibjson.license && resultobj.bibjson.license.length > 0) {
                    var terms_url = resultobj.bibjson.ref.license_terms;
                    for (var i = 0; i < resultobj.bibjson.license.length; i++) {
                        var lic = resultobj.bibjson.license[i];
                        var license_url = lic.url || terms_url;
                        licenses += '<a href="' + license_url + '" target="_blank" rel="noopener">' + edges.escapeHtml(lic.type) + '</a>';
                    }
                }

                var language = "";
                if (resultobj.index.language && resultobj.index.language.length > 0) {
                    language = '<li>\
                              Accepts manuscripts in <strong>' + resultobj.index.language.join(", ") + '</strong>\
                            </li>';
                }

                var actions = "";
                if (this.actions.length > 0) {
                    actions = '<h4 class="label">Actions</h4><ul class="tags">';
                    for (var i = 0; i < this.actions.length; i++) {
                        var act = this.actions[i];
                        var actSettings = act(resultobj);
                        if (actSettings) {
                            actions += '<li class="tag">\
                                <a href="' + actSettings.link + '">' + actSettings.label + '</a>\
                            </li>';
                        }
                    }
                    actions += '</ul>';
                }

                var frag = '<li class="card search-results__record">\
                    <article class="row">\
                      <div class="col-sm-8 search-results__main">\
                        <header>\
                          ' + seal + '\
                          <h3 class="search-results__heading">\
                            <a href="/toc/' + issn + '">\
                              ' + edges.escapeHtml(resultobj.bibjson.title) + '\
                            </a>\
                            ' + subtitle + '\
                          </h3>\
                        </header>\
                        <div class="search-results__body">\
                          <ul class="inlined-list">\
                            <li>\
                              ' + published + '\
                            </li>\
                            ' + language + '\
                          </ul>\
                          <ul>\
                            ' + subjects + '\
                          </ul>\
                        </div>\
                      </div>\
                      <aside class="col-sm-4 search-results__aside">\
                        <ul>\
                          <li>\
                            ' + update_or_added + '\
                          </li>\
                          ' + articles + '\
                          <li>\
                            <a href="' + resultobj.bibjson.ref.journal + '" target="_blank" rel="noopener">Website <span data-feather="external-link" aria-hidden="true"></span></a>\
                          </li>\
                          <li>\
                            ' + apcs + '\
                          </li>\
                          <li>\
                            ' + licenses + '\
                          </li>\
                        </ul>\
                        ' + actions + '\
                      </aside>\
                    </article>\
                  </li>';

                return frag;
            };
        },
        newSortRenderer: function (params) {
            return edges.instantiate(doaj.renderers.SortRenderer, params, edges.newRenderer);
        },
        SortRenderer: function (params) {

            this.prefix = edges.getParam(params.prefix, "");

            // should the direction switcher be rendered?  If not, then it's wise to set "dir" on the components
            // sortOptions, so that the correct dir is used
            this.dirSwitcher = edges.getParam(params.dirSwitcher, true);

            this.namespace = "doaj-sort-renderer";

            this.draw = function () {
                var comp = this.component;

                // if sort options are provided render the orderer and the order by
                var sortOptions = "";
                if (comp.sortOptions && comp.sortOptions.length > 0) {
                    // classes that we'll use
                    var directionClass = edges.css_classes(this.namespace, "direction", this);
                    var sortFieldClass = edges.css_classes(this.namespace, "sortby", this);
                    var prefixClass = edges.css_classes(this.namespace, "prefix", this);

                    var selectName = edges.css_id(this.namespace, "select", this);

                    var label = '<label class="' + prefixClass + '" for="' + selectName + '">' + this.prefix + '</label>';

                    var direction = "";
                    if (this.dirSwitcher) {
                        direction = '<span class="input-group-btn"> \
                            <button type="button" class="btn btn-default btn-sm ' + directionClass + '" title="" href="#"></button> \
                        </span>';
                    }

                    sortOptions = label + '\
                        ' + direction + ' \
                        <select name="' + selectName + '" class="form-control input-sm ' + sortFieldClass + '" id="' + selectName + '"> \
                            <option value="_score">Relevance</option>';

                    for (var i = 0; i < comp.sortOptions.length; i++) {
                        var field = comp.sortOptions[i].field;
                        var display = comp.sortOptions[i].display;
                        var dir = comp.sortOptions[i].dir;
                        if (dir === undefined) {
                            dir = "";
                        }
                        dir = " " + dir;
                        sortOptions += '<option value="' + field + '' + dir + '">' + edges.escapeHtml(display) + '</option>';
                    }

                    sortOptions += ' </select>';
                }

                // assemble the final fragment and render it into the component's context
                var frag = '{{SORT}}';
                frag = frag.replace(/{{SORT}}/g, sortOptions);

                comp.context.html(frag);

                // now populate all the dynamic bits
                if (comp.sortOptions && comp.sortOptions.length > 0) {
                    if (this.dirSwitcher) {
                        this.setUISortDir();
                    }
                    this.setUISortField();
                }

                // attach all the bindings
                if (comp.sortOptions && comp.sortOptions.length > 0) {
                    var directionSelector = edges.css_class_selector(this.namespace, "direction", this);
                    var sortSelector = edges.css_class_selector(this.namespace, "sortby", this);
                    edges.on(directionSelector, "click", this, "changeSortDir");
                    edges.on(sortSelector, "change", this, "changeSortBy");
                }
            };

            //////////////////////////////////////////////////////
            // functions for setting UI values

            this.setUISortDir = function () {
                // get the selector we need
                var directionSelector = edges.css_class_selector(this.namespace, "direction", this);
                var el = this.component.jq(directionSelector);
                if (this.component.sortDir === 'asc') {
                    el.html('sort <i class="glyphicon glyphicon-arrow-up"></i> by');
                    el.attr('title', 'Current order ascending. Click to change to descending');
                } else {
                    el.html('sort <i class="glyphicon glyphicon-arrow-down"></i> by');
                    el.attr('title', 'Current order descending. Click to change to ascending');
                }
            };

            this.setUISortField = function () {
                if (!this.component.sortBy) {
                    return;
                }
                // get the selector we need
                var sortSelector = edges.css_class_selector(this.namespace, "sortby", this);
                var el = this.component.jq(sortSelector);

                // find out the available value options
                var options = el.find("option");
                var vals = [];
                for (var i = 0; i < options.length; i++) {
                    vals.push($(options[i]).attr("value"));
                }

                // sort out the value we want to set
                var fieldVal = this.component.sortBy;
                var fullVal = this.component.sortBy + " " + this.component.sortDir;

                // choose the first value which matches an actual option
                var setVal = false;
                if ($.inArray(fieldVal, vals) > -1) {
                    setVal = fieldVal;
                } else if ($.inArray(fullVal, vals) > -1) {
                    setVal = fullVal;
                }

                if (setVal !== false) {
                    el.val(setVal);
                }
            };

            ////////////////////////////////////////
            // event handlers

            this.changeSortDir = function (element) {
                this.component.changeSortDir();
            };

            this.changeSortBy = function (element) {
                var val = this.component.jq(element).val();
                var bits = val.split(" ");
                var field = bits[0];
                var dir = false;
                if (bits.length === 2) {
                    dir = bits[1];
                }
                this.component.setSort({field: field, dir: dir});
            };
        }
    },

    fieldRender: {
        titleField : function (val, resultobj, renderer) {
            var field = '<h3>';
            if (resultobj.bibjson.title) {
                if (resultobj.es_type === "journal") {
                    var display = edges.escapeHtml(resultobj.bibjson.title);
                    if (resultobj.admin.in_doaj) {
                        display =  "<a href='/toc/" + doaj.journal_toc_id(resultobj) + "'>" + display + "</a>";
                    }
                    field += display;
                } else {
                    field += edges.escapeHtml(resultobj.bibjson.title);
                }
                if (resultobj.admin && resultobj.admin.seal) {
                    field += "<p><span class='tag tag--featured'>\
                              <span data-feather='check-circle' aria-hidden='true'></span>\
                              DOAJ Seal</span></p>​​";
                }
                return field + "</h3>"
            } else {
                return false;
            }
        },

        authorPays : function(val, resultobj, renderer) {
            var field = "";
            if (edges.hasProp(resultobj, "bibjson.apc.max") && resultobj.bibjson.apc.max.length > 0) {
                field += 'Has charges';
            } else if (edges.hasProp(resultobj, "bibjson.other_charges.has_other_charges") && resultobj.bibjson.other_charges.has_other_charges) {
                field += 'Has charges';
            }
            if (field === "") {
                field = 'No charges';
            }

            var urls = [];
            if (edges.hasProp(resultobj, "bibjson.apc.url")) {
                urls.push(resultobj.bibjson.apc.url);
            }
            if (edges.hasProp(resultobj, "bibjson.has_other_charges.url")) {
                urls.push(resultobj.bibjson.has_other_charges.url)
            }

            if (urls.length > 0) {
                field += ' (see ';
                for (var i = 0; i < urls.length; i++) {
                    field += '<a href="' + urls[i] + '">' + urls[i] + '</a>';
                }
                field += ')';
            }

            return field ? field : false;
        },

        abstract : function (val, resultobj, renderer) {
            if (resultobj['bibjson']['abstract']) {
                var result = '<a class="abstract_action" href="#" rel="';
                result += resultobj['id'];
                result += '">(show/hide)</a> <span class="abstract_text" style="display:none" rel="';
                result += resultobj['id'];
                result += '">' + '<br>';
                result += edges.escapeHtml(resultobj['bibjson']['abstract']);
                result += '</span>';
                return result;
            }
            return false;
        },

        journalLicense : function (val, resultobj, renderer) {
            var titles = [];
            if (resultobj.bibjson && resultobj.bibjson.journal && resultobj.bibjson.journal.license) {
                var lics = resultobj["bibjson"]["journal"]["license"];
                var titles = lics.map(function(x) { return x.type });
            }
            else if (resultobj.bibjson && resultobj.bibjson.license) {
                var lics = resultobj["bibjson"]["license"];
                titles = lics.map(function(x) { return x.type });
            }

            var links = [];
            if (titles.length > 0) {
                for (var i = 0; i < titles.length; i++) {
                    var title = titles[i];
                    if (doaj.licenceMap[title]) {
                        var urls = doaj.licenceMap[title];
                        // i know i know, i'm not using styles.  the attrs still work and are easier.
                        links.push("<a href='" + urls[1] + "' title='" + title + "' target='blank'><img src='" + urls[0] + "' width='80' height='15' valign='middle' alt='" + title + "'></a>");
                    } else {
                        links.push(title);
                    }
                }
                return links.join(" ");
            }

            return false;
        },

        doiLink : function (val, resultobj, renderer) {
            if (resultobj.bibjson && resultobj.bibjson.identifier) {
                var ids = resultobj.bibjson.identifier;
                for (var i = 0; i < ids.length; i++) {
                    if (ids[i].type === "doi") {
                        var doi = ids[i].id;
                        var tendot = doi.indexOf("10.");
                        var url = "https://doi.org/" + doi.substring(tendot);
                        return "<a href='" + url + "'>" + edges.escapeHtml(doi.substring(tendot)) + "</a>"
                    }
                }
            }
            return false
        },

        links : function (val, resultobj, renderer) {
            if (resultobj.bibjson && resultobj.bibjson.ref) {
                var urls = [];
                var ls = Object.keys(resultobj.bibjson.ref);
                for (var i = 0; i < ls.length; i++) {
                    if (ls[i] === "journal") {
                        var url = resultobj.bibjson.ref[ls[i]];
                        urls.push("<strong>Home page</strong>: <a href='" + url + "'>" + edges.escapeHtml(url) + "</a>")
                    }
                }
                return urls.join("<br>");
            }
            if (resultobj.bibjson && resultobj.bibjson.link) {
                var ls = resultobj.bibjson.link;
                for (var i = 0; i < ls.length; i++) {
                    var t = ls[i].type;
                    var label = '';
                    if (t === 'fulltext') {
                        label = 'Full text'
                    } else {
                        label = t.substring(0, 1).toUpperCase() + t.substring(1)
                    }
                    return "<strong>" + label + "</strong>: <a href='" + ls[i].url + "'>" + edges.escapeHtml(ls[i].url) + "</a>"
                }
            }
            return false;
        },

        issns : function (val, resultobj, renderer) {
            if (resultobj.bibjson && (resultobj.bibjson.pissn || resultobj.bibjson.eissn)) {
                var issn = resultobj.bibjson.pissn;
                var eissn = resultobj.bibjson.eissn;
                var issns = [];
                if (issn) {
                    issns.push(edges.escapeHtml(issn));
                }
                if (eissn) {
                    issns.push(edges.escapeHtml(eissn));
                }
                return issns.join(", ")
            }
            return false
        },

        countryName : function (val, resultobj, renderer) {
            if (resultobj.index && resultobj.index.country) {
                return edges.escapeHtml(resultobj.index.country);
            }
            return false
        },

        inDoaj : function(val, resultobj, renderer) {
            var mapping = {
                "false": {"text": "No", "class": "red"},
                "true": {"text": "Yes", "class": "green"}
            };
            var field = "";
            if (resultobj.admin && resultobj.admin.in_doaj !== undefined) {
                if(mapping[resultobj['admin']['in_doaj']]) {
                    var result = '<span class=' + mapping[resultobj['admin']['in_doaj']]['class'] + '>';
                    result += mapping[resultobj['admin']['in_doaj']]['text'];
                    result += '</span>';
                    field += result;
                } else {
                    field += resultobj['admin']['in_doaj'];
                }
                if (field === "") {
                    return false
                }
                return field
            }
            return false;
        },

        owner : function (val, resultobj, renderer) {
            if (resultobj.admin && resultobj.admin.owner !== undefined && resultobj.admin.owner !== "") {
                var own = resultobj.admin.owner;
                return '<a href="/account/' + own + '">' + edges.escapeHtml(own) + '</a>'
            }
            return false
        },

        createdDateWithTime : function (val, resultobj, renderer) {
            return doaj.iso_datetime2date_and_time(resultobj['created_date']);
        },

        lastManualUpdate : function (val, resultobj, renderer) {
            var man_update = resultobj['last_manual_update'];
            if (man_update === '1970-01-01T00:00:00Z')
            {
                return 'Never'
            } else {
                return doaj.iso_datetime2date_and_time(man_update);
            }
        },

        suggestedOn : function (val, resultobj, renderer) {
            if (resultobj && resultobj['admin'] && resultobj['admin']['date_applied']) {
                return doaj.iso_datetime2date_and_time(resultobj['admin']['date_applied']);
            } else {
                return false;
            }
        },

        applicationStatus : function(val, resultobj, renderer) {
            return doaj.valueMaps.applicationStatus[resultobj['admin']['application_status']];
        },

        editSuggestion : function(params) {
            return function (val, resultobj, renderer) {
                if (resultobj.es_type === "application") {
                    // determine the link name
                    var linkName = "Review application";
                    if (resultobj.admin.application_status === 'accepted' || resultobj.admin.application_status === 'rejected') {
                        linkName = "View finished application";
                        if (resultobj.admin.related_journal) {
                            linkName = "View finished update";
                        }
                    } else if (resultobj.admin.current_journal) {
                        linkName = "Review update";
                    }

                    var result = '<p><a class="edit_suggestion_link button" href="';
                    result += params.editUrl;
                    result += resultobj['id'];
                    result += '" target="_blank"';
                    result += '>' + linkName + '</a></p>';
                    return result;
                }
                return false;
            }
        },

        readOnlyJournal : function(params) {
            return function (val, resultobj, renderer) {
                if (resultobj.admin && resultobj.admin.current_journal) {
                    var result = '<br/><p><a class="readonly_journal_link button" href="';
                    result += params.readOnlyJournalUrl;
                    result += resultobj.admin.current_journal;
                    result += '" target="_blank"';
                    result += '>View journal being updated</a></p>';
                    return result;
                }
                return false;
            }
        },

        editJournal : function(params) {
            return function (val, resultobj, renderer) {
                if (!resultobj.suggestion && !resultobj.bibjson.journal) {
                    // if it's not a suggestion or an article .. (it's a
                    // journal!)
                    // we really need to expose _type ...
                    var result = '<p><a class="edit_journal_link button button--tertiary" href="';
                    result += params.editUrl;
                    result += resultobj['id'];
                    result += '" target="_blank"';
                    result += '>Edit this journal</a></p>';
                    return result;
                }
                return false;
            }
        },
    }

});

$.extend(true, edges, {
    bs3 : {
        newResultCountRenderer: function (params) {
            if (!params) {params = {}}
            edges.bs3.ResultCountRenderer.prototype = edges.newRenderer(params);
            return new edges.bs3.ResultCountRenderer(params);
        },
        ResultCountRenderer: function (params) {

            this.prefix = edges.getParam(params.prefix, "");

            this.suffix = edges.getParam(params.suffix, "");

            this.countFormat = edges.getParam(params.countFormat, false);

            this.htmlContainerWrapper = edges.getParam(params.htmlContainerWrapper, true);

            ////////////////////////////////////////
            // state variables

            this.namespace = "edges-bs3-result-count";

            this.draw = function () {
                // classes we'll need
                var containerClass = edges.css_classes(this.namespace, "container", this);
                var totalClass = edges.css_classes(this.namespace, "total", this);
                var prefixClass = edges.css_classes(this.namespace, "prefix", this);
                var suffixClass = edges.css_classes(this.namespace, "suffix", this);

                var total = this.component.total;
                if (!total) {
                    total = 0;
                }
                if (this.countFormat) {
                    total = this.countFormat(total);
                }
                total = '<span class="' + totalClass + '">' + total + '</span>';

                var prefix = "";
                if (this.prefix !== "") {
                    prefix = '<span class="' + prefixClass + '">' + this.prefix + '</span>';
                }

                var suffix = "";
                if (this.suffix !== "") {
                    suffix = '<span class="' + suffixClass + '">' + this.suffix + '</span>';
                }


                // the total number of records found
                var recordCount = prefix + total + suffix;

                var frag = recordCount;
                if (this.htmlContainerWrapper) {
                    frag = '<div class="' + containerClass + '"><div class="row"><div class="col-md-12">{{COUNT}}</div></div></div>';
                    frag = frag.replace(/{{COUNT}}/g, recordCount);
                }

                this.component.context.html(frag);
            };
        }
    }
});
$.extend(true, edges, {
    bs3 : {
        newPagerRenderer: function (params) {
            if (!params) {
                params = {}
            }
            edges.bs3.PagerRenderer.prototype = edges.newRenderer(params);
            return new edges.bs3.PagerRenderer(params);
        },
        PagerRenderer: function (params) {

            this.scroll = edges.getParam(params.scroll, true);

            this.scrollSelector = edges.getParam(params.scrollSelector, "body");

            this.showSizeSelector = edges.getParam(params.showSizeSelector, true);

            this.sizeOptions = edges.getParam(params.sizeOptions, [10, 25, 50, 100]);

            this.sizePrefix = edges.getParam(params.sizePrefix, "");

            this.sizeSuffix = edges.getParam(params.sizeSuffix, " per page");

            this.showRecordCount = edges.getParam(params.showRecordCount, true);

            this.showPageNavigation = edges.getParam(params.showPageNavigation, true);

            this.numberFormat = edges.getParam(params.numberFormat, false);

            this.namespace = "edges-bs3-pager";

            this.draw = function () {
                if (this.component.total === false || this.component.total === 0) {
                    this.component.context.html("");
                    return;
                }

                // classes we'll need
                var containerClass = edges.css_classes(this.namespace, "container", this);
                var totalClass = edges.css_classes(this.namespace, "total", this);
                var navClass = edges.css_classes(this.namespace, "nav", this);
                var firstClass = edges.css_classes(this.namespace, "first", this);
                var prevClass = edges.css_classes(this.namespace, "prev", this);
                var pageClass = edges.css_classes(this.namespace, "page", this);
                var nextClass = edges.css_classes(this.namespace, "next", this);
                var sizeSelectClass = edges.css_classes(this.namespace, "size", this);

                // the total number of records found
                var recordCount = "";
                if (this.showRecordCount) {
                    var total = this.component.total;
                    if (this.numberFormat) {
                        total = this.numberFormat(total);
                    }
                    recordCount = '<span class="' + totalClass + '">' + total + '</span> results found';
                }

                // the number of records per page
                var sizer = "";
                if (this.showSizeSelector) {
                    var sizer = '<div class="form-inline">' + recordCount + this.sizePrefix + '<div class="form-group"><select class="form-control input-sm ' + sizeSelectClass + '" name="' + this.component.id + '-page-size">{{SIZES}}</select></div>' + this.sizeSuffix + '</div>';
                    var sizeopts = "";
                    var optarr = this.sizeOptions.slice(0);
                    if ($.inArray(this.component.pageSize, optarr) === -1) {
                        optarr.push(this.component.pageSize)
                    }
                    optarr.sort(function (a, b) {
                        return a - b
                    });  // sort numerically
                    for (var i = 0; i < optarr.length; i++) {
                        var so = optarr[i];
                        var selected = "";
                        if (so === this.component.pageSize) {
                            selected = "selected='selected'";
                        }
                        sizeopts += '<option name="' + so + '" ' + selected + '>' + so + '</option>';
                    }
                    sizer = sizer.replace(/{{SIZES}}/g, sizeopts);
                }

                var nav = "";
                if (this.showPageNavigation) {
                    var first = '<a href="#" class="' + firstClass + '">First</a>';
                    var prev = '<a href="#" class="' + prevClass + '">Prev</a>';
                    if (this.component.page === 1) {
                        first = '<span class="' + firstClass + ' disabled">First</span>';
                        prev = '<span class="' + prevClass + ' disabled">Prev</span>';
                    }

                    var next = '<a href="#" class="' + nextClass + '">Next</a>';
                    if (this.component.page === this.component.totalPages) {
                        next = '<span class="' + nextClass + ' disabled">Next</a>';
                    }

                    var pageNum = this.component.page;
                    var totalPages = this.component.totalPages;
                    if (this.numberFormat) {
                        pageNum = this.numberFormat(pageNum);
                        totalPages = this.numberFormat(totalPages);
                    }
                    nav = '<div class="' + navClass + '">' + first + prev +
                        '<span class="' + pageClass + '">Page ' + pageNum + ' of ' + totalPages + '</span>' +
                        next + "</div>";
                }

                var frag = "";
                if (this.showSizeSelector && !this.showPageNavigation) {
                    frag = '<div class="' + containerClass + '"><div class="row"><div class="col-md-12">{{COUNT}}</div></div></div>';
                } else if (!this.showSizeSelector && this.showPageNavigation) {
                    frag = '<div class="' + containerClass + '"><div class="row"><div class="col-md-12">{{NAV}}</div></div></div>';
                } else {
                    frag = '<div class="' + containerClass + '"><div class="row"><div class="col-md-6">{{COUNT}}</div><div class="col-md-6">{{NAV}}</div></div></div>';
                }
                frag = frag.replace(/{{COUNT}}/g, sizer).replace(/{{NAV}}/g, nav);

                this.component.context.html(frag);

                // now create the selectors for the functions
                if (this.showPageNavigation) {
                    var firstSelector = edges.css_class_selector(this.namespace, "first", this);
                    var prevSelector = edges.css_class_selector(this.namespace, "prev", this);
                    var nextSelector = edges.css_class_selector(this.namespace, "next", this);

                    // bind the event handlers
                    if (this.component.page !== 1) {
                        edges.on(firstSelector, "click", this, "goToFirst");
                        edges.on(prevSelector, "click", this, "goToPrev");
                    }
                    if (this.component.page !== this.component.totalPages) {
                        edges.on(nextSelector, "click", this, "goToNext");
                    }
                }

                if (this.showSizeSelector) {
                    var sizeSelector = edges.css_class_selector(this.namespace, "size", this);
                    edges.on(sizeSelector, "change", this, "changeSize");
                }
            };

            this.doScroll = function () {
                $("html, body").animate({
                    scrollTop: $(this.scrollSelector).offset().top
                }, 1);
            };

            this.goToFirst = function (element) {
                if (this.scroll) {
                    this.doScroll();
                }
                this.component.setFrom(1);
            };

            this.goToPrev = function (element) {
                if (this.scroll) {
                    this.doScroll();
                }
                this.component.decrementPage();
            };

            this.goToNext = function (element) {
                if (this.scroll) {
                    this.doScroll();
                }
                this.component.incrementPage();
            };

            this.changeSize = function (element) {
                var size = $(element).val();
                this.component.setSize(size);
            };
        }
    }
});
