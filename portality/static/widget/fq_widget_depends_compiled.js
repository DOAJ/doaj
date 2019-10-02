/******************************************************************
 * ELASTICSEARCH INTEGRATION
 *****************************************************************/

// The reserved characters in elasticsearch query strings
// Note that the "\" has to go first, as when these are substituted, that character
// will get introduced as an escape character
var esSpecialChars = ["\\", "+", "-", "=", "&&", "||", ">", "<", "!", "(", ")", "{", "}", "[", "]", "^", '"', "~", "*", "?", ":", "/"];

// the reserved special character set with * and " removed, so that users can do quote searches and wildcards
// if they want
var esSpecialCharsSubSet = ["\\", "+", "-", "=", "&&", "||", ">", "<", "!", "(", ")", "{", "}", "[", "]", "^", "~", "?", ":", "/"];

// values that have to be in even numbers in the query or they will be escaped
var esPairs = ['"'];

// FIXME: esSpecialChars is not currently used for encoding, but it would be worthwhile giving the facetview an option
// to allow/disallow specific values, but that requires a much better (automated) understanding of the
// query DSL

var elasticsearch_distance_units = ["km", "mi", "miles", "in", "inch", "yd", "yards", "kilometers", "mm", "millimeters", "cm", "centimeters", "m", "meters"]

function optionsFromQuery(query) {

    function stripDistanceUnits(val) {
        for (var i=0; i < elasticsearch_distance_units.length; i=i+1) {
            var unit = elasticsearch_distance_units[i];
            if (endsWith(val, unit)) {
                return val.substring(0, val.length - unit.length)
            }
        }
        return val
    }

    function unescapeQueryString(val) {
        function escapeRegExp(string) {
            return string.replace(/([.*+?^=!:${}()|\[\]\/\\])/g, "\\$1");
        }

        function unReplaceAll(string, find) {
            return string.replace(new RegExp("\\\\(" + escapeRegExp(find) + ")", 'g'), "$1");
        }

        // Note we use the full list of special chars
        for (var i = 0; i < esSpecialChars.length; i++) {
            var char = esSpecialChars[i];
            val = unReplaceAll(val, char)
        }

        return val;
    }
    
    var opts = {};

    // FIXME: note that fields are not supported here

    // from position
    if (query.hasOwnProperty("from")) { opts["from"] = query.from }
    
    // page size
    if (query.size) { opts["page_size"] = query.size }
    
    if (query["sort"]) { opts["sort"] = query["sort"] }
    
    // get hold of the bool query if it is there
    // and get hold of the query string and default operator if they have been provided
    if (query.query) {
        var sq = query.query;
        var must = [];
        var qs = undefined;
        
        // if this is a filtered query, pull must and qs out of the filter
        // otherwise the root of the query is the query_string object
        if (sq.filtered) {
            must = sq.filtered.filter.bool.must;
            qs = sq.filtered.query
        } else {
            qs = sq
        }
        
        // go through each clause in the must and pull out the options
        if (must.length > 0) {
            opts["_active_filters"] = {};
            opts["_selected_operators"] = {}
        }
        for (var i = 0; i < must.length; i++) {
            var clause = must[i];
            
            // could be a term query (implies AND on this field)
            if ("term" in clause) {
                for (var field in clause.term) {
                    if (clause.term.hasOwnProperty(field)) {
                        opts["_selected_operators"][field] = "AND";
                        var value = clause.term[field];
                        if (!(field in opts["_active_filters"])) {
                            opts["_active_filters"][field] = []
                        }
                        opts["_active_filters"][field].push(value)
                    }
                }
            }
            
            // could be a terms query (implies OR on this field)
            if ("terms" in clause) {
                for (var field=0; field < clause.terms.length; field=field+1) {
                    opts["_selected_operators"][field] = "OR";
                    var values = clause.terms[field];
                    if (!(field in opts["_active_filters"])) {
                        opts["_active_filters"][field] = []
                    }
                    opts["_active_filters"][field] = opts["_active_filters"][field].concat(values)
                }
            }
            
            // could be a range query (which may in turn be a range or a date histogram facet)
            if ("range" in clause) {
                // get the field that we're ranging on
                var r = clause.range;
                var fields = Object.keys(r);
                var field = false;
                if (fields.length > 0) {
                    field = fields[0];
                }

                if (field) {
                    var rparams = r[field];
                    var range = {};
                    if ("lt" in rparams) { range["to"] = rparams.lt }
                    if ("gte" in rparams) { range["from"] = rparams.gte }
                    opts["_active_filters"][field] = range;
                }
            }
            
            // cound be a geo distance query
            if ("geo_distance_range" in clause) {
                var gdr = clause.geo_distance_range;
                
                // the range is defined at the root of the range filter
                var range = {};
                if ("lt" in gdr) { range["to"] = stripDistanceUnits(gdr.lt) }
                if ("gte" in gdr) { range["from"] = stripDistanceUnits(gdr.gte) }
                
                // FIXME: at some point we may need to make this smarter, if we start including other data
                // in the geo_distance_range filter definition
                // then we have to go looking for the field name
                for (var field=0; field < gdr.length; field=field+1) {
                    if (field === "lt" || field === "gte") { continue }
                    opts["_active_filters"][field] = range
                    break
                }
            }

            // FIXME: support for statistical facet and terms_stats facet
        }
        
        if (qs) {
            if (qs.query_string) {
                var string = unescapeQueryString(qs.query_string.query);
                var field = qs.query_string.default_field;
                var op = qs.query_string.default_operator;
                if (string) { opts["q"] = string }
                if (field) { opts["searchfield"] = field }
                if (op) { opts["default_operator"] = op }
            } else if (qs.match_all) {
                opts["q"] = ""
            }
        }
        
        return opts
    }
}

function getFilters(params) {
    var options = params.options;

    // function to get the right facet from the options, based on the name
    function selectFacet(name) {
        for (var i = 0; i < options.facets.length; i++) {
            var item = options.facets[i];
            if ('field' in item) {
                if (item['field'] === name) {
                    return item
                }
            }
        }
    }

    function termsFilter(facet, filter_list) {
        if (facet.logic === "AND") {
            var filters = [];
            for (var i=0; i < filter_list.length; i=i+1) {
                var value = filter_list[i];
                var tq = {"term" : {}};
                tq["term"][facet.field] = value;
                filters.push(tq);
            }
            return filters;
        } else if (facet.logic === "OR") {
            var tq = {"terms" : {}};
            tq["terms"][facet.field] = filter_list;
            return [tq];
        }
    }

    function rangeFilter(facet, value) {
        var rq = {"range" : {}};
        rq["range"][facet.field] = {};
        if (value.to) { rq["range"][facet.field]["lt"] = value.to }
        if (value.from) { rq["range"][facet.field]["gte"] = value.from }
        return rq
    }

    function geoFilter(facet, value) {
        var gq = {"geo_distance_range" : {}};
        if (value.to) { gq["geo_distance_range"]["lt"] = value.to + facet.unit }
        if (value.from) { gq["geo_distance_range"]["gte"] = value.from + facet.unit }
        gq["geo_distance_range"][facet.field] = [facet.lon, facet.lat]; // note the order of lon/lat to comply with GeoJSON
        return gq
    }

    function dateHistogramFilter(facet, value) {
        var rq = {"range" : {}};
        rq["range"][facet.field] = {};
        if (value.to) { rq["range"][facet.field]["lt"] = value.to }
        if (value.from) { rq["range"][facet.field]["gte"] = value.from }
        return rq
    }

    // function to make the relevant filters from the filter definition
    function makeFilters(filter_definition) {
        var filters = [];
        for (var field in filter_definition) {
            if (filter_definition.hasOwnProperty(field)) {
                var facet = selectFacet(field);

                // FIXME: is this the right behaviour?
                // ignore any filters from disabled facets
                if (facet.disabled) { continue }

                var filter_list = filter_definition[field];

                if (facet.type === "terms") {
                    filters = filters.concat(termsFilter(facet, filter_list)); // Note this is a concat not a push, unlike the others
                } else if (facet.type === "range") {
                    filters.push(rangeFilter(facet, filter_list))
                } else if (facet.type === "geo_distance") {
                    filters.push(geoFilter(facet, filter_list))
                } else if (facet.type == "date_histogram") {
                    filters.push(dateHistogramFilter(facet, filter_list))
                }
            }
        }
        return filters
    }

    // read any filters out of the options and create an array of "must" queries which
    // will constrain the search results
    var filter_must = [];
    if (options.active_filters) {
        filter_must = filter_must.concat(makeFilters(options.active_filters))
    }
    if (options.predefined_filters) {
        filter_must = filter_must.concat(makeFilters(options.predefined_filters))
    }
    if (options.fixed_filters) {
        filter_must = filter_must.concat(options.fixed_filters)
    }

    return filter_must
}

function elasticSearchQuery(params) {
    // break open the parameters
    var options = params.options;
    var include_facets = "include_facets" in params ? params.include_facets : true;
    var include_fields = "include_fields" in params ? params.include_fields : true;

    var filter_must = getFilters({"options" : options});

    // search string and search field produce a query_string query element
    var querystring = options.q;
    var searchfield = options.searchfield;
    var default_operator = options.default_operator;
    var ftq = undefined;
    if (querystring) {
        ftq = {'query_string' : { 'query': fuzzify(querystring, options.default_freetext_fuzzify) }};
        if (searchfield) {
            ftq.query_string["default_field"] = searchfield
        }
        if (default_operator) {
            ftq.query_string["default_operator"] = default_operator
        }
    } else {
        ftq = {"match_all" : {}}
    }
    
    // if there are filter constraints (filter_must) then we create a filtered query,
    // otherwise make a normal query
    var qs = undefined;
    if (filter_must.length > 0) {
        qs = {"query" : {"filtered" : {"filter" : {"bool" : {"must" : filter_must}}}}};
        qs.query.filtered["query"] = ftq;
    } else {
        qs = {"query" : ftq}
    }
    
    // sort order and direction
    options.sort && options.sort.length > 0 ? qs['sort'] = options.sort : "";
    
    // fields and partial fields
    if (include_fields) {
        options.fields ? qs['fields'] = options.fields : "";
        options.partial_fields ? qs['partial_fields'] = options.partial_fields : "";
        options.script_fields ? qs["script_fields"] = options.script_fields : "";
    }
    
    // paging (number of results, and start cursor)
    if (options.from !== undefined) {
        qs["from"] = options.from
    }
    if (options.page_size !== undefined) {
        qs["size"] = options.page_size
    }
    
    // facets
    if (include_facets) {
        qs['facets'] = {};
        for (var item = 0; item < options.facets.length; item++) {
            var defn = options.facets[item];
            if (defn.disabled) { continue }

            var size = defn.size;
            
            // add a bunch of extra values to the facets to deal with the shard count issue
            size += options.elasticsearch_facet_inflation 
            
            var facet = {};
            if (defn.type === "terms") {
                facet["terms"] = {"field" : defn["field"], "size" : size, "order" : defn["order"]}
            } else if (defn.type === "range") {
                var ranges = [];
                for (var r=0; r < defn["range"].length; r=r+1) {
                    var def = defn["range"][r];
                    var robj = {};
                    if (def.to) { robj["to"] = def.to }
                    if (def.from) { robj["from"] = def.from }
                    ranges.push(robj)
                }
                facet["range"] = { };
                facet["range"][defn.field] = ranges
            } else if (defn.type === "geo_distance") {
                facet["geo_distance"] = {}
                facet["geo_distance"][defn["field"]] = [defn.lon, defn.lat]; // note that the order is lon/lat because of GeoJSON
                facet["geo_distance"]["unit"] = defn.unit;
                var ranges = [];
                for (var r=0; r < defn["distance"].length; r=r+1) {
                    var def = defn["distance"][r];
                    var robj = {};
                    if (def.to) { robj["to"] = def.to }
                    if (def.from) { robj["from"] = def.from }
                    ranges.push(robj)
                }
                facet["geo_distance"]["ranges"] = ranges
            } else if (defn.type === "statistical") {
                facet["statistical"] = {"field" : defn["field"]}
            } else if (defn.type === "terms_stats") {
                facet["terms_stats"] = {key_field : defn["field"], value_field: defn["value_field"], size : size, order : defn["order"]}
            } else if (defn.type === "date_histogram") {
                facet["date_histogram"] = {field : defn["field"], interval : defn["interval"]}
            }
            qs["facets"][defn["field"]] = facet
        }
        
        // and any extra facets
        // NOTE: this does not include any treatment of the facet size inflation that may be required
        if (options.extra_facets) {
            $.extend(true, qs['facets'], options.extra_facets );
        }
    }
    
    return qs
}

function fuzzify(querystr, default_freetext_fuzzify) {
    var rqs = querystr;
    if (default_freetext_fuzzify !== undefined) {
        if (default_freetext_fuzzify == "*" || default_freetext_fuzzify == "~") {
            if (querystr.indexOf('*') === -1 && querystr.indexOf('~') === -1 && querystr.indexOf(':') === -1) {
                var optparts = querystr.split(' ');
                pq = "";
                for ( var oi = 0; oi < optparts.length; oi++ ) {
                    var oip = optparts[oi];
                    if ( oip.length > 0 ) {
                        oip = oip + default_freetext_fuzzify;
                        default_freetext_fuzzify == "*" ? oip = "*" + oip : false;
                        pq += oip + " ";
                    }
                }
                rqs = pq;
            }
        }
    }
    return rqs;
}

function jsonStringEscape(key, value) {

    function escapeRegExp(string) {
        return string.replace(/([.*+?^=!:${}()|\[\]\/\\])/g, "\\$1");
    }

    function replaceAll(string, find, replace) {
      return string.replace(new RegExp(escapeRegExp(find), 'g'), replace);
    }

    function paired(string, pair) {
        var matches = (string.match(new RegExp(escapeRegExp(pair), "g"))) || []
        return matches.length % 2 === 0;
    }

    // if we are looking at the query string, make sure that it is escaped
    // (note that this precludes the use of queries like "name:bob", as the ":" would
    // get escaped)
    if (key === "query" && typeof(value) === 'string') {

        var scs = esSpecialCharsSubSet.slice(0);

        // first check for pairs
        for (var i = 0; i < esPairs.length; i++) {
            var char = esPairs[i];
            if (!paired(value, char)) {
                scs.push(char);
            }
        }

        for (var i = 0; i < scs.length; i++) {
            var char = scs[i];
            value = replaceAll(value, char, "\\" + char);
        }

    }

    return value;
}

function serialiseQueryObject(qs) {
    return JSON.stringify(qs, jsonStringEscape);
}

// closure for elastic search success, which ultimately calls
// the user's callback
function elasticSearchSuccess(callback) {
    return function(data) {
        var resultobj = {
            "records" : [],
            "start" : "",
            "found" : data.hits.total,
            "facets" : {}
        };
        
        // load the results into the records part of the result object
        for (var item = 0; item < data.hits.hits.length; item++) {
            var res = data.hits.hits[item];
            if ("fields" in res) {
                // partial_fields and script_fields are also included here - no special treatment
                resultobj.records.push(res.fields)
            } else {
                resultobj.records.push(res._source)
            }
        }
        
        for (var item in data.facets) {
            if (data.facets.hasOwnProperty(item)) {
                var facet = data.facets[item];

                // handle any terms facets
                if ("terms" in facet) {
                    var terms = facet["terms"];
                    resultobj["facets"][item] = terms;
                // handle any range/geo_distance_range facets
                } else if ("ranges" in facet) {
                    var range = facet["ranges"];
                    resultobj["facets"][item] = range;
                // handle statistical facets
                } else if (facet["_type"] === "statistical") {
                    resultobj["facets"][item] = facet;
                // handle terms_stats
                } else if (facet["_type"] === "terms_stats") {
                    var terms = facet["terms"];
                    resultobj["facets"][item] = terms
                } else if (facet["_type"] === "date_histogram") {
                    var entries = facet["entries"]
                    resultobj["facets"][item] = entries
                }
            }
        }
            
        callback(data, resultobj)
    }
}

function doElasticSearchQuery(params) {
    // extract the parameters of the request
    var success_callback = params.success;
    var complete_callback = params.complete;
    var search_url = params.search_url;
    var queryobj = params.queryobj;
    var datatype = params.datatype;
    
    // serialise the query
    var querystring = serialiseQueryObject(queryobj);
    
    // make the call to the elasticsearch web service
    $.ajax({
        type: "get",
        url: search_url,
        data: {source: querystring},
        dataType: datatype,
        success: elasticSearchSuccess(success_callback),
        complete: complete_callback
    });
}


function escapeHtml(unsafe, def) {
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
}

/******************************************************************
 * DEFAULT RENDER FUNCTIONS
 *****************************************************************/

function theFacetview(options) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * id: facetview - main div in which the facetview functionality goes
     * id: facetview_filters - div where the facet filters will be displayed
     * id: facetview_rightcol - the main window for result display (doesn't have to be on the right)
     * class: facetview_search_options_container - where the search bar and main controls will go
     * id : facetview_selectedfilters - where we summarise the filters which have been selected
     * class: facetview_metadata - where we want paging to go
     * id: facetview_results - the table id for where the results actually go
     * id: facetview_searching - where the loading notification can go
     *
     * Should respect the following configs
     *
     * options.debug - is this a debug enabled facetview.  If so, put a debug textarea somewhere
     */

    // the facet view object to be appended to the page
    var thefacetview = '<div id="facetview"><div class="row-fluid">';

    // if there are facets, give them span3 to exist, otherwise, take up all the space
    var showfacets = false
    for (var i = 0; i < options.facets.length; i++) {
        var f = options.facets[i]
        if (!f.hidden) {
            showfacets = true;
            break;
        }
    }
    if (showfacets) {
        thefacetview += '<div class="span3"><div id="facetview_filters" style="padding-top:45px;"></div></div>';
        thefacetview += '<div class="span9" id="facetview_rightcol">';
    } else {
        thefacetview += '<div class="span12" id="facetview_rightcol">';
    }

    // make space for the search options container at the top
    thefacetview += '<div class="facetview_search_options_container"></div>';

    // make space for the selected filters
    thefacetview += '<div style="clear:both;" class="btn-toolbar" id="facetview_selectedfilters"></div>';

    // make space at the top for the pager
    thefacetview += '<div class="facetview_metadata" style="margin-top:20px;"></div>';

    // insert loading notification
    thefacetview += '<div class="facetview_searching" style="display:none"></div>'

    // insert the table within which the results actually will go
    thefacetview += '<table class="table table-striped table-bordered" id="facetview_results" dir="auto"></table>'

    // make space at the bottom for the pager
    thefacetview += '<div class="facetview_metadata"></div>';

    // debug window near the bottom
    if (options.debug) {
        thefacetview += '<div class="facetview_debug" style="display:none"><textarea style="width: 95%; height: 300px"></textarea></div>'
    }

    // close off all the big containers and return
    thefacetview += '</div></div></div>';
    return thefacetview
}

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

    // share and save link
    if (options.sharesave_link) {
        thefacetview += '<a class="btn facetview_sharesave" title="share a link to this search" style="margin:0 5px 21px 0px;" href="">share <i class="icon icon-share"></i></a>';
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
            thefacetview += " <a href='#' class='facetview_shorten_url btn btn-mini' style='margin-left: 30px'><i class='icon-white icon-resize-small'></i> shorten url</a>";
            thefacetview += " <a href='#' class='facetview_lengthen_url btn btn-mini' style='display: none; margin-left: 30px'><i class='icon-white icon-resize-full'></i> original url</a>";
        }

        thefacetview += '</p> \
            <textarea class="facetview_sharesaveurl" style="width:100%">' + shareableUrl(options) + '</textarea> \
            </div>';
    }

    return thefacetview
}

function facetList(options) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * none - no requirements for specific classes and ids
     *
     * should (not must) respect the following config
     *
     * options.facet[x].hidden - whether the facet should be displayed in the UI or not
     * options.render_terms_facet - renders a term facet into the list
     * options.render_range_facet - renders a range facet into the list
     * options.render_geo_facet - renders a geo distance facet into the list
     */
    if (options.facets.length > 0) {
        var filters = options.facets;
        var thefilters = '';
        for (var idx = 0; idx < filters.length; idx++) {
            var facet = filters[idx]
            // if the facet is hidden do not include it in this list
            if (facet.hidden) {
                continue;
            }

            // note that we do render disabled facets, so that they are available for enabling/disabling
            // by callbacks

            var type = facet.type ? facet.type : "terms"
            if (type === "terms") {
                thefilters += options.render_terms_facet(facet, options)
            } else if (type === "range") {
                thefilters += options.render_range_facet(facet, options)
            } else if (type === "geo_distance") {
                thefilters += options.render_geo_facet(facet, options)
            } else if (type == "date_histogram") {
                thefilters += options.render_date_histogram_facet(facet, options)
            }
            // FIXME: statistical facet and terms_stats facet?
        };
        return thefilters
    };
    return ""
};

function renderTermsFacet(facet, options) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * id: facetview_filter_<safe filtername> - table for the specific filter
     * class: facetview_morefacetvals - for increasing the size of the facet
     * id: facetview_facetvals_<safe filtername> - id of anchor for changing facet vals
     * class: facetview_sort - for changing the facet ordering
     * id: facetview_sort_<safe filtername> - id of anchor for changing sorting
     * class: facetview_or - for changing the default operator
     * id: facetview_or_<safe filtername> - id of anchor for changing AND/OR operator
     *
     * each anchor must also have href="<filtername>"
     *
     * should (not must) respect the following config
     *
     * facet.controls - whether the size/sort/bool controls should be shown
     */

    // full template for the facet - we'll then go on and do some find and replace
    var filterTmpl = '<table id="facetview_filter_{{FILTER_NAME}}" class="facetview_filters table table-bordered table-condensed table-striped" data-href="{{FILTER_EXACT}}"> \
        <tr><td><a class="facetview_filtershow" title="filter by {{FILTER_DISPLAY}}" \
        style="color:#333; font-weight:bold;" href="{{FILTER_EXACT}}"><i class="icon-plus"></i> {{FILTER_DISPLAY}} \
        </a>';

    if (facet.tooltip) {
        var linktext = facet.tooltip_text ? facet.tooltip_text : "learn more";
        filterTmpl += '<div class="facetview_tooltip" style="display:none"><a href="#" class="facetview_tooltip_more" data-field="{{FILTER_NAME}}">' + linktext + '</a></div>';
        filterTmpl += '<div class="facetview_tooltip_value" style="display:none">' + facet.tooltip + '<br><a href="#" class="facetview_tooltip_less" data-field="{{FILTER_NAME}}">less</a></div>';
    }

    if (facet.controls) {
        filterTmpl += '<div class="btn-group facetview_filteroptions" style="display:none; margin-top:5px;"> \
            <a class="btn btn-small facetview_morefacetvals" id="facetview_facetvals_{{FILTER_NAME}}" title="filter list size" href="{{FILTER_EXACT}}">0</a> \
            <a class="btn btn-small facetview_sort" id="facetview_sort_{{FILTER_NAME}}" title="filter value order" href="{{FILTER_EXACT}}"></a> \
            <a class="btn btn-small facetview_or" id="facetview_or_{{FILTER_NAME}}" href="{{FILTER_EXACT}}">OR</a> \
        </div>';
    }

    filterTmpl += '</td></tr> \
        </table>';

    // put the name of the field into FILTER_NAME and FILTER_EXACT
    filterTmpl = filterTmpl.replace(/{{FILTER_NAME}}/g, safeId(facet['field'])).replace(/{{FILTER_EXACT}}/g, facet['field']);

    // set the display name of the facet in FILTER_DISPLAY
    if ('display' in facet) {
        filterTmpl = filterTmpl.replace(/{{FILTER_DISPLAY}}/g, facet['display']);
    } else {
        filterTmpl = filterTmpl.replace(/{{FILTER_DISPLAY}}/g, facet['field']);
    };

    return filterTmpl
}

function renderRangeFacet(facet, options) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * id: facetview_filter_<safe filtername> - table for the specific filter
     *
     * each anchor must also have href="<filtername>"
     */

    // full template for the facet - we'll then go on and do some find and replace
    var filterTmpl = '<table id="facetview_filter_{{FILTER_NAME}}" class="facetview_filters table table-bordered table-condensed table-striped" data-href="{{FILTER_EXACT}}"> \
        <tr><td><a class="facetview_filtershow" title="filter by {{FILTER_DISPLAY}}" \
        style="color:#333; font-weight:bold;" href="{{FILTER_EXACT}}"><i class="icon-plus"></i> {{FILTER_DISPLAY}} \
        </a> \
        </td></tr> \
        </table>';

    // put the name of the field into FILTER_NAME and FILTER_EXACT
    filterTmpl = filterTmpl.replace(/{{FILTER_NAME}}/g, safeId(facet['field'])).replace(/{{FILTER_EXACT}}/g, facet['field']);

    // set the display name of the facet in FILTER_DISPLAY
    if ('display' in facet) {
        filterTmpl = filterTmpl.replace(/{{FILTER_DISPLAY}}/g, facet['display']);
    } else {
        filterTmpl = filterTmpl.replace(/{{FILTER_DISPLAY}}/g, facet['field']);
    };

    return filterTmpl
}

function renderGeoFacet(facet, options) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * id: facetview_filter_<safe filtername> - table for the specific filter
     *
     * each anchor must also have href="<filtername>"
     */
     // full template for the facet - we'll then go on and do some find and replace
    var filterTmpl = '<table id="facetview_filter_{{FILTER_NAME}}" class="facetview_filters table table-bordered table-condensed table-striped" data-href="{{FILTER_EXACT}}"> \
        <tr><td><a class="facetview_filtershow" title="filter by {{FILTER_DISPLAY}}" \
        style="color:#333; font-weight:bold;" href="{{FILTER_EXACT}}"><i class="icon-plus"></i> {{FILTER_DISPLAY}} \
        </a> \
        </td></tr> \
        </table>';

    // put the name of the field into FILTER_NAME and FILTER_EXACT
    filterTmpl = filterTmpl.replace(/{{FILTER_NAME}}/g, safeId(facet['field'])).replace(/{{FILTER_EXACT}}/g, facet['field']);

    // set the display name of the facet in FILTER_DISPLAY
    if ('display' in facet) {
        filterTmpl = filterTmpl.replace(/{{FILTER_DISPLAY}}/g, facet['display']);
    } else {
        filterTmpl = filterTmpl.replace(/{{FILTER_DISPLAY}}/g, facet['field']);
    };

    return filterTmpl
}

function renderDateHistogramFacet(facet, options) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * id: facetview_filter_<safe filtername> - table for the specific filter
     *
     * each anchor must also have href="<filtername>"
     */

    // full template for the facet - we'll then go on and do some find and replace
    var filterTmpl = '<table id="facetview_filter_{{FILTER_NAME}}" class="facetview_filters table table-bordered table-condensed table-striped" data-href="{{FILTER_EXACT}}"> \
        <tbody><tr><td><a class="facetview_filtershow" title="filter by {{FILTER_DISPLAY}}" \
        style="color:#333; font-weight:bold;" href="{{FILTER_EXACT}}"><i class="icon-plus"></i> {{FILTER_DISPLAY}} \
        </a> \
        </td></tr></tbody> \
        </table>';

    // put the name of the field into FILTER_NAME and FILTER_EXACT
    filterTmpl = filterTmpl.replace(/{{FILTER_NAME}}/g, safeId(facet['field'])).replace(/{{FILTER_EXACT}}/g, facet['field']);

    // set the display name of the facet in FILTER_DISPLAY
    if ('display' in facet) {
        filterTmpl = filterTmpl.replace(/{{FILTER_DISPLAY}}/g, facet['display']);
    } else {
        filterTmpl = filterTmpl.replace(/{{FILTER_DISPLAY}}/g, facet['field']);
    };

    return filterTmpl
}

function renderTermsFacetValues(options, facet) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * class: facetview_filtervalue - wrapper element for any value included in the list
     * class: facetview_filterselected - for any anchors around selected filters
     * class: facetview_clear - for any link which should remove a filter (must also provide data-field and data-value)
     * class: facetview_filterchoice - tags the anchor wrapped around the name of the (unselected) field
     *
     * should (not must) respect the following config
     *
     * options.selected_filters_in_facet - whether to show selected filters in the facet pull-down (if that's your idiom)
     * options.render_facet_result - function which renders the individual facets
     * facet.value_function - the value function to be applied to all displayed values
     */
    var selected_filters = options.active_filters[facet.field]
    var frag = ""

    // first render the active filters
    if (options.selected_filters_in_facet) {
        if (selected_filters) {
            for (var i=0; i < selected_filters.length; i=i+1) {
                var value = selected_filters[i]
                if (facet.value_function) {
                    value = facet.value_function(value)
                }
                var sf = '<tr class="facetview_filtervalue" style="display:none;"><td>'
                sf += "<strong>" + value + "</strong> "
                sf += '<a class="facetview_filterselected facetview_clear" data-field="' + facet.field + '" data-value="' + escapeHtml(value) + '" href="' + escapeHtml(value) + '"><i class="icon-black icon-remove" style="margin-top:1px;"></i></a>'
                sf += "</td></tr>"
                frag += sf
            }
        }
    }

    // is there a pre-defined filter on this facet?
    var predefined = facet.field in options.predefined_filters ? options.predefined_filters[facet.field] : []

    // then render the remaining selectable facets
    for (var i=0; i < facet["values"].length; i=i+1) {
        var f = facet["values"][i]
        if (options.exclude_predefined_filters_from_facets && $.inArray(f.term, predefined) > -1) { // note that the datatypes have to match
            continue
        }
        if ($.inArray(f.term.toString(), selected_filters) === -1) { // the toString helps us with non-string filters (e.g integers)
            var append = options.render_terms_facet_result(options, facet, f, selected_filters)
            frag += append
        }
    }

    return frag
}

function renderRangeFacetValues(options, facet) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * class: facetview_filtervalue - wrapper element for any value included in the list
     * class: facetview_filterselected - for any anchors around selected filters
     * class: facetview_clear - for any link which should remove a filter (must also provide data-field and data-value)
     * class: facetview_filterchoice - tags the anchor wrapped around the name of the (unselected) field
     *
     * should (not must) respect the following config
     *
     * options.selected_filters_in_facet - whether to show selected filters in the facet pull-down (if that's your idiom)
     * options.render_facet_result - function which renders the individual facets
     */

    function getValueForRange(range, values) {
        for (var i=0; i < values.length; i=i+1) {
            var value = values[i]

            // the "to"s match if they both value and range have a "to" and they are the same, or if neither have a "to"
            var match_to = (value.to && range.to && value.to === range.to) || (!value.to && !range.to)

            // the "from"s match if they both value and range have a "from" and they are the same, or if neither have a "from"
            var match_from = (value.from && range.from && value.from === range.from) || (!value.from && !range.from)

            if (match_to && match_from) {
                return value
            }
        }
    }

    function getRangeForValue(value, facet) {
        for (var i=0; i < facet.range.length; i=i+1) {
            var range = facet.range[i]

            // the "to"s match if they both value and range have a "to" and they are the same, or if neither have a "to"
            var match_to = (value.to && range.to && value.to === range.to.toString()) || (!value.to && !range.to)

            // the "from"s match if they both value and range have a "from" and they are the same, or if neither have a "from"
            var match_from = (value.from && range.from && value.from === range.from.toString()) || (!value.from && !range.from)

            if (match_to && match_from) {
                return range
            }
        }
    }

    var selected_range = options.active_filters[facet.field]
    var frag = ""

    // render the active filter if there is one
    if (options.selected_filters_in_facet && selected_range) {
        var range = getRangeForValue(selected_range, facet)
        var already_selected = true

        var data_to = range.to ? " data-to='" + range.to + "' " : ""
        var data_from = range.from ? " data-from='" + range.from + "' " : ""

        var sf = '<tr class="facetview_filtervalue" style="display:none;"><td>'
        sf += "<strong>" + range.display + "</strong> "
        sf += '<a class="facetview_filterselected facetview_clear" data-field="' + facet.field + '" ' + data_to + data_from + ' href="#"><i class="icon-black icon-remove" style="margin-top:1px;"></i></a>'
        sf += "</td></tr>"
        frag += sf

        // if a range is already selected, we don't render any more
        return frag
    }

    // then render the remaining selectable facets if necessary
    for (var i=0; i < facet["range"].length; i=i+1) {
        var r = facet["range"][i]
        var f = getValueForRange(r, facet["values"])
        if (f) {
            if (f.count === 0 && facet.hide_empty_range) {
                continue
            }
            var append = options.render_range_facet_result(options, facet, f, r)
            frag += append
        }
    }

    return frag
}

function renderGeoFacetValues(options, facet) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * class: facetview_filtervalue - wrapper element for any value included in the list
     * class: facetview_filterselected - for any anchors around selected filters
     * class: facetview_clear - for any link which should remove a filter (must also provide data-field and data-value)
     * class: facetview_filterchoice - tags the anchor wrapped around the name of the (unselected) field
     *
     * should (not must) respect the following config
     *
     * options.selected_filters_in_facet - whether to show selected filters in the facet pull-down (if that's your idiom)
     * options.render_facet_result - function which renders the individual facets
     */

    function getValueForRange(range, values) {
        for (var i=0; i < values.length; i=i+1) {
            var value = values[i]

            // the "to"s match if they both value and range have a "to" and they are the same, or if neither have a "to"
            var match_to = (value.to && range.to && value.to === range.to) || (!value.to && !range.to)

            // the "from"s match if they both value and range have a "from" and they are the same, or if neither have a "from"
            var match_from = (value.from && range.from && value.from === range.from) || (!value.from && !range.from)

            if (match_to && match_from) {
                return value
            }
        }
    }

    function getRangeForValue(value, facet) {
        for (var i=0; i < facet.distance.length; i=i+1) {
            var range = facet.distance[i]

            // the "to"s match if they both value and range have a "to" and they are the same, or if neither have a "to"
            var match_to = (value.to && range.to && value.to === range.to.toString()) || (!value.to && !range.to)

            // the "from"s match if they both value and range have a "from" and they are the same, or if neither have a "from"
            var match_from = (value.from && range.from && value.from === range.from.toString()) || (!value.from && !range.from)

            if (match_to && match_from) {
                return range
            }
        }
    }

    var selected_geo = options.active_filters[facet.field]
    var frag = ""

    // render the active filter if there is one
    if (options.selected_filters_in_facet && selected_geo) {
        var range = getRangeForValue(selected_geo, facet)
        var already_selected = true

        var data_to = range.to ? " data-to='" + range.to + "' " : ""
        var data_from = range.from ? " data-from='" + range.from + "' " : ""

        var sf = '<tr class="facetview_filtervalue" style="display:none;"><td>'
        sf += "<strong>" + range.display + "</strong> "
        sf += '<a class="facetview_filterselected facetview_clear" data-field="' + facet.field + '" ' + data_to + data_from + ' href="#"><i class="icon-black icon-remove" style="margin-top:1px;"></i></a>'
        sf += "</td></tr>"
        frag += sf

        // if a range is already selected, we don't render any more
        return frag
    }

    // then render the remaining selectable facets if necessary
    for (var i=0; i < facet["distance"].length; i=i+1) {
        var r = facet["distance"][i]
        var f = getValueForRange(r, facet["values"])
        if (f) {
            if (f.count === 0 && facet.hide_empty_distance) {
                continue
            }
            var append = options.render_geo_facet_result(options, facet, f, r)
            frag += append
        }
    }

    return frag
}

function renderDateHistogramValues(options, facet) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * class: facetview_filtervalue - wrapper element for any value included in the list
     * class: facetview_filterselected - for any anchors around selected filters
     * class: facetview_clear - for any link which should remove a filter (must also provide data-field and data-value)
     * class: facetview_filterchoice - tags the anchor wrapped around the name of the (unselected) field
     *
     * should (not must) respect the following config
     *
     * options.selected_filters_in_facet - whether to show selected filters in the facet pull-down (if that's your idiom)
     * options.render_facet_result - function which renders the individual facets
     */

    var selected_range = options.active_filters[facet.field];
    var frag = "";

    // render the active filter if there is one
    if (options.selected_filters_in_facet && selected_range) {
        var from = selected_range.from;
        var data_from = " data-from='" + from + "' ";
        var display = from;
        if (facet.value_function) {
            display = facet.value_function(display);
        }

        var sf = '<tr class="facetview_filtervalue" style="display:none;"><td>';
        sf += "<strong>" + display + "</strong> ";
        sf += '<a class="facetview_filterselected facetview_clear" data-field="' + facet.field + '" '+ data_from + ' href="#"><i class="icon-black icon-remove" style="margin-top:1px;"></i></a>';
        sf += "</td></tr>";
        frag += sf;

        // if a range is already selected, we don't render any more
        return frag
    }

    // then render the remaining selectable facets if necessary

    // get the facet values in the right order for display
    var values = facet["values"];
    if (facet.sort === "desc") {
        values.reverse()
    }

    var full_frag = "<tbody class='facetview_date_histogram_full table-striped-inverted' style='display: none'>";
    var short_frag = "<tbody class='facetview_date_histogram_short table-striped-inverted'>";

    for (var i = 0; i < values.length; i++) {
        var f = values[i];
        if (f) {
            if (f.count === 0 && facet.hide_empty_date_bin) {
                continue
            }

            var next = false;
            if (facet.sort === "asc") {
                if (i + 1 < values.length) {
                    next = values[i + 1]
                }
            } else if (facet.sort === "desc") {
                if (i - 1 >= 0) {
                    next = values[i - 1];
                }
            }

            var append = options.render_date_histogram_result(options, facet, f, next);

            full_frag += append;
            if (!facet["short_display"]) {
                short_frag += append;
            }
            else if (facet["short_display"] && i < facet["short_display"]) {
                short_frag += append;
            }
        }
    }

    full_frag += '<tr class="facetview_filtervalue" style="display:none;"><td><a href="#" class="facetview_date_histogram_showless" data-facet="' + facet['field'] + '">show less</a></td></tr>';
    full_frag += "</tbody>";

    if (facet["short_display"] && values.length > facet["short_display"]) {
        short_frag += '<tr class="facetview_filtervalue" style="display:none;"><td><a href="#" class="facetview_date_histogram_showall" data-facet="' + facet['field'] + '">show all</a></td></tr>';
    }
    short_frag += "</tbody>";

    return short_frag + full_frag;
}

function renderTermsFacetResult(options, facet, result, selected_filters) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * class: facetview_filtervalue - tags the top level element as being a facet result
     * class: facetview_filterchoice - tags the anchor wrapped around the name of the field
     *
     * should (not must) respect the following configuration:
     *
     * facet.value_function - the value function to be applied to all displayed values
     */

    var display = result.term
    if (facet.value_function) {
        display = facet.value_function(display)
    }
    var append = '<tr class="facetview_filtervalue" style="display:none;"><td><a class="facetview_filterchoice' +
                '" data-field="' + facet['field'] + '" data-value="' + escapeHtml(result.term) + '" href="' + escapeHtml(result.term) +
                '"><span class="facetview_filterchoice_text" dir="auto">' + display + '</span>' +
                '<span class="facetview_filterchoice_count" dir="ltr"> (' + result.count + ')</span></a></td></tr>';
    return append
}

function renderRangeFacetResult(options, facet, result, range) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * class: facetview_filtervalue - tags the top level element as being a facet result
     * class: facetview_filterchoice - tags the anchor wrapped around the name of the field
     */
    var data_to = range.to ? " data-to='" + range.to + "' " : ""
    var data_from = range.from ? " data-from='" + range.from + "' " : ""

    var append = '<tr class="facetview_filtervalue" style="display:none;"><td><a class="facetview_filterchoice' +
                '" data-field="' + facet['field'] + '" ' + data_to + data_from + ' href="#"><span class="facetview_filterchoice_text" dir="auto">' + range.display + '</span>' +
                '<span class="facetview_filterchoice_count" dir="ltr"> (' + result.count + ')</span></a></td></tr>';
    return append
}

function renderGeoFacetResult(options, facet, result, range) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * class: facetview_filtervalue - tags the top level element as being a facet result
     * class: facetview_filterchoice - tags the anchor wrapped around the name of the field
     */
    var data_to = range.to ? " data-to='" + range.to + "' " : ""
    var data_from = range.from ? " data-from='" + range.from + "' " : ""

    var append = '<tr class="facetview_filtervalue" style="display:none;"><td><a class="facetview_filterchoice' +
                '" data-field="' + facet['field'] + '" ' + data_to + data_from + ' href="#"><span class="facetview_filterchoice_text" dir="auto">' + range.display + '</span>' +
                '<span class="facetview_filterchoice_count" dir="ltr"> (' + result.count + ')</span></a></td></tr>';
    return append
}

function renderDateHistogramResult(options, facet, result, next) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * class: facetview_filtervalue - tags the top level element as being a facet result
     * class: facetview_filterchoice - tags the anchor wrapped around the name of the field
     */

    var data_from = result.time ? " data-from='" + result.time + "' " : "";
    var data_to = next ? " data-to='" + next.time + "' " : "";

    var display = result.time;
    if (facet.value_function) {
        display = facet.value_function(display)
    }

    var append = '<tr class="facetview_filtervalue" style="display:none;"><td><a class="facetview_filterchoice' +
                '" data-field="' + facet['field'] + '" ' + data_to + data_from + ' href="#"><span class="facetview_filterchoice_text" dir="auto">' + escapeHtml(display) + '</span>' +
                '<span class="facetview_filterchoice_count" dir="ltr"> (' + result.count + ')</span></a></td></tr>';
    return append
}

function searchingNotification(options) {
    return "SEARCHING..."
}

function basicPager(options) {
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
    var from = parseInt(options.from)
    var size = parseInt(options.page_size)

    // calculate the human readable values we want
    var to = from + size
    from = from + 1 // zero indexed
    if (options.data.found < to) { to = options.data.found }
    var total = options.data.found

    // forward and back-links, taking into account start and end boundaries
    var backlink = '<a class="facetview_decrement">&laquo; back</a>'
    if (from < size) { backlink = "<a class='facetview_decrement facetview_inactive_link'>..</a>" }

    var nextlink = '<a class="facetview_increment">next &raquo;</a>'
    if (options.data.found <= to) { nextlink = "<a class='facetview_increment facetview_inactive_link'>..</a>" }

    var meta = '<div class="pagination"><ul>'
    meta += '<li class="prev">' + backlink + '</li>'
    meta += '<li class="active"><a>' + from + ' &ndash; ' + to + ' of ' + total + '</a></li>'
    meta += '<li class="next">' + nextlink + '</li>'
    meta += "</ul></div>"

    return meta
}

function pageSlider(options) {
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

    // forward and back-links, taking into account start and end boundaries
    var backlink = '<a alt="previous" title="previous" class="facetview_decrement" style="color:#333;float:left;padding:0 40px 20px 20px;"><span class="icon icon-arrow-left"></span></a>'
    if (from < size) {
        backlink = '<a class="facetview_decrement facetview_inactive_link" style="color:#333;float:left;padding:0 40px 20px 20px;">&nbsp;</a>'
    }

    var nextlink = '<a alt="next" title="next" class="facetview_increment" style="color:#333;float:right;padding:0 20px 20px 40px;"><span class="icon icon-arrow-right"></span></a>'
    if (options.data.found <= to) {
        nextlink = '<a class="facetview_increment facetview_inactive_link" style="color:#333;float:right;padding:0 20px 20px 40px;">&nbsp;</a>'
    }

    var meta = '<div style="font-size:20px;font-weight:bold;margin:5px 0 10px 0;padding:5px 0 5px 0;border:1px solid #eee;border-radius:5px;-moz-border-radius:5px;-webkit-border-radius:5px;">'
    meta += backlink
    meta += '<span style="margin:30%;">' + from + ' &ndash; ' + to + ' of ' + total + '</span>'
    meta += nextlink
    meta += '</div>'

    return meta
}

function renderNotFound() {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * class: facetview_not_found - the id of the top level element containing the not found message
     */
    return "<tr class='facetview_not_found'><td>No results found</td></tr>"
}

function renderResultRecord(options, record) {
    /*****************************************
     * overrides must provide the following classes and ids
     *
     * none - no specific requirements
     *
     * should (not must) use the config
     *
     * options.resultwrap_start - starting elements for any result object
     * options.resultwrap_end - closing elements for any result object
     * options.result_display - line-by-line display commands for the result object
     */

    // get our custom configuration out of the options
    var result = options.resultwrap_start;
    var display = options.result_display;

    // build up a full string representing the object
    var lines = '';
    for (var lineitem = 0; lineitem < display.length; lineitem++) {
        var line = "";
        for (var object = 0; object < display[lineitem].length; object++) {
            var thekey = display[lineitem][object]['field'];
            var thevalue = "";
            if (typeof options.results_render_callbacks[thekey] == 'function') {
                // a callback is defined for this field so just call it
                thevalue = options.results_render_callbacks[thekey].call(this, record);
            } else {
                // split the key up into its parts, and work our way through the
                // tree until we get to the node to display.  Note that this will only
                // work with a string hierarchy of dicts - it can't have lists in it
                var parts = thekey.split('.');
                var res = record;
                for (var i = 0; i < parts.length; i++) {
                    if (res) {
                        res = res[parts[i]]
                    } else {
                        continue
                    }
                }

                // just get a string representation of the object
                if (res) {
                    if ($.isArray(res)) {
                        thevalue = res.join(", ")
                    } else {
                        thevalue = res.toString()
                    }
                }

                thevalue = escapeHtml(thevalue);
            }

            // if we have a value to display, sort out the pre-and post- stuff and build the new line
            if (thevalue && thevalue.toString().length) {
                if (display[lineitem][object]['pre']) {
                    line += display[lineitem][object]['pre']
                }
                line += thevalue;

                if (display[lineitem][object]['post']) {
                    line += display[lineitem][object]['post'];
                } else if(!display[lineitem][object]['notrailingspace']) {
                    line += ' ';
                }
            }
        }

        // if we have a line, append it to the full lines and add a line break
        if (line) {
            lines += line.replace(/^\s/,'').replace(/\s$/,'').replace(/\,$/,'') + "<br />";
        }
    }

    // if we have the lines, append them to the result wrap start
    if (lines) {
        result += lines
    }

    // close off the result with the ending strings, and then return
    result += options.resultwrap_end;
    return result;
}

function renderActiveTermsFilter(options, facet, field, filter_list) {
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
        frag += '<i class="icon-white icon-remove" style="margin-top:1px;"></i>';
        frag += "</a>";

        if (i !== filter_list.length - 1 && options.show_filter_logic) {
            frag += '<span class="facetview_filterselected_text">&nbsp;<strong>' + logic + '</strong>&nbsp;</span>';
        }
    }
    frag += "</div>";

    return frag
}

function renderActiveRangeFilter(options, facet, field, value) {
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

    function getRangeForValue(value, facet) {
        for (var i=0; i < facet.range.length; i=i+1) {
            var range = facet.range[i];

            // the "to"s match if they both value and range have a "to" and they are the same, or if neither have a "to"
            var match_to = (value.to && range.to && value.to === range.to.toString()) || (!value.to && !range.to);

            // the "from"s match if they both value and range have a "from" and they are the same, or if neither have a "from"
            var match_from = (value.from && range.from && value.from === range.from.toString()) || (!value.from && !range.from);

            if (match_to && match_from) {
                return range
            }
        }
    }

    var clean = safeId(field);
    var display = facet.display ? facet.display : facet.field;

    var frag = "<div id='facetview_filter_group_" + clean + "' class='btn-group'>";

    if (options.show_filter_field) {
        frag += '<span class="facetview_filterselected_text"><strong>' + display + ':</strong>&nbsp;</span>';
    }

    var range = getRangeForValue(value, facet);

    var data_to = value.to ? " data-to='" + value.to + "' " : "";
    var data_from = value.from ? " data-from='" + value.from + "' " : "";

    frag += '<span class="facetview_filterselected_text">' + range.display + '</span>&nbsp;';
    frag += '<a class="facetview_filterselected facetview_clear" data-field="' + field + '" ' + data_to + data_from +
            ' alt="remove" title="Remove" href="#">';
    frag += '<i class="icon-white icon-remove" style="margin-top:1px;"></i>';
    frag += "</a>";

    frag += "</div>";

    return frag
}

function renderActiveGeoFilter(options, facet, field, value) {
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

    function getRangeForValue(value, facet) {
        for (var i=0; i < facet.distance.length; i=i+1) {
            var range = facet.distance[i];

            // the "to"s match if they both value and range have a "to" and they are the same, or if neither have a "to"
            var match_to = (value.to && range.to && value.to === range.to.toString()) || (!value.to && !range.to);

            // the "from"s match if they both value and range have a "from" and they are the same, or if neither have a "from"
            var match_from = (value.from && range.from && value.from === range.from.toString()) || (!value.from && !range.from);

            if (match_to && match_from) {
                return range
            }
        }
    }

    var clean = safeId(field);
    var display = facet.display ? facet.display : facet.field;

    var frag = "<div id='facetview_filter_group_" + clean + "' class='btn-group'>";

    if (options.show_filter_field) {
        frag += '<span class="facetview_filterselected_text"><strong>' + display + ':</strong>&nbsp;</span>';
    }

    var range = getRangeForValue(value, facet);

    var data_to = value.to ? " data-to='" + value.to + "' " : "";
    var data_from = value.from ? " data-from='" + value.from + "' " : "";

    frag += '<span class="facetview_filterselected_text">' + range.display + '</span>&nbsp;';
    frag += '<a class="facetview_filterselected facetview_clear" data-field="' + field + '" ' + data_to + data_from +
            ' alt="Remove" title="remove" href="#">';
    frag += '<i class="icon-white icon-remove" style="margin-top:1px;"></i>';
    frag += "</a>";

    frag += "</div>";

    return frag
}

function renderActiveDateHistogramFilter(options, facet, field, value) {
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
    frag += '<i class="icon-white icon-remove" style="margin-top:1px;"></i>';
    frag += "</a>";

    frag += "</div>";

    return frag
}

/////////////////////////////////////////////////////////////////////////////////////////////
// Alternative active filter renderers which use buttons - deprecated due to usability/ux concerns

function renderActiveTermsFilterButton(options, facet, field, filter_list) {
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
    var clean = safeId(field)
    var display = facet.display ? facet.display : facet.field
    var logic = facet.logic ? facet.logic : options.default_facet_operator

    var frag = "<div id='facetview_filter_group_" + clean + "' class='btn-group'>";

    if (options.show_filter_field) {
        frag += '<a class="btn btn-info facetview_inactive_link facetview_filterselected" href="' + field + '">'
        frag += '<span class="facetview_filterselected_text"><strong>' + display + '</strong></span>'
        frag += "</a>"
    }

    for (var i = 0; i < filter_list.length; i++) {
        var value = filter_list[i]
        if (facet.value_function) {
            value = facet.value_function(value)
        }

        frag += '<a class="facetview_filterselected facetview_clear btn btn-info" data-field="' + field + '" data-value="' + escapeHtml(value) + '" alt="remove" title="remove" href="' + escapeHtml(value) + '">'
        frag += '<span class="facetview_filterselected_text">' + escapeHtml(value) + '</span> <i class="icon-white icon-remove" style="margin-top:1px;"></i>'
        frag += "</a>"

        if (i !== filter_list.length - 1 && options.show_filter_logic) {
            frag += '<a class="btn btn-info facetview_inactive_link facetview_filterselected" href="' + field + '">'
            frag += '<span class="facetview_filterselected_text"><strong>' + logic + '</strong></span>'
            frag += "</a>"
        }
    }
    frag += "</div>"

    return frag
}

function renderActiveRangeFilterButton(options, facet, field, value) {
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

    function getRangeForValue(value, facet) {
        for (var i=0; i < facet.range.length; i=i+1) {
            var range = facet.range[i]

            // the "to"s match if they both value and range have a "to" and they are the same, or if neither have a "to"
            var match_to = (value.to && range.to && value.to === range.to.toString()) || (!value.to && !range.to)

            // the "from"s match if they both value and range have a "from" and they are the same, or if neither have a "from"
            var match_from = (value.from && range.from && value.from === range.from.toString()) || (!value.from && !range.from)

            if (match_to && match_from) {
                return range
            }
        }
    }

    var clean = safeId(field)
    var display = facet.display ? facet.display : facet.field

    var frag = "<div id='facetview_filter_group_" + clean + "' class='btn-group'>"

    if (options.show_filter_field) {
        frag += '<a class="btn btn-info facetview_inactive_link facetview_filterselected" href="' + field + '">'
        frag += '<span class="facetview_filterselected_text"><strong>' + display + '</strong></span>'
        frag += "</a>"
    }

    var range = getRangeForValue(value, facet)

    var data_to = value.to ? " data-to='" + value.to + "' " : ""
    var data_from = value.from ? " data-from='" + value.from + "' " : ""

    frag += '<a class="facetview_filterselected facetview_clear btn btn-info" data-field="' + field + '" ' + data_to + data_from +
            ' alt="remove" title="remove" href="#">'
    frag += '<span class="facetview_filterselected_text">' + range.display + '</span> <i class="icon-white icon-remove" style="margin-top:1px;"></i>'
    frag += "</a>"

    frag += "</div>"

    return frag
}

function renderActiveGeoFilterButton(options, facet, field, value) {
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

    function getRangeForValue(value, facet) {
        for (var i=0; i < facet.distance.length; i=i+1) {
            var range = facet.distance[i]

            // the "to"s match if they both value and range have a "to" and they are the same, or if neither have a "to"
            var match_to = (value.to && range.to && value.to === range.to.toString()) || (!value.to && !range.to)

            // the "from"s match if they both value and range have a "from" and they are the same, or if neither have a "from"
            var match_from = (value.from && range.from && value.from === range.from.toString()) || (!value.from && !range.from)

            if (match_to && match_from) {
                return range
            }
        }
    }

    var clean = safeId(field)
    var display = facet.display ? facet.display : facet.field

    var frag = "<div id='facetview_filter_group_" + clean + "' class='btn-group'>"

    if (options.show_filter_field) {
        frag += '<a class="btn btn-info facetview_inactive_link facetview_filterselected" href="' + field + '">'
        frag += '<span class="facetview_filterselected_text"><strong>' + display + '</strong></span>'
        frag += "</a>"
    }

    var range = getRangeForValue(value, facet)

    var data_to = value.to ? " data-to='" + value.to + "' " : ""
    var data_from = value.from ? " data-from='" + value.from + "' " : ""

    frag += '<a class="facetview_filterselected facetview_clear btn btn-info" data-field="' + field + '" ' + data_to + data_from +
            ' alt="remove" title="remove" href="#">'
    frag += '<span class="facetview_filterselected_text">' + range.display + '</span> <i class="icon-white icon-remove" style="margin-top:1px;"></i>'
    frag += "</a>"

    frag += "</div>"

    return frag
}

function renderActiveDateHistogramFilterButton(options, facet, field, value) {
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

    var clean = safeId(field);
    var display = facet.display ? facet.display : facet.field;

    var frag = "<div id='facetview_filter_group_" + clean + "' class='btn-group'>";

    if (options.show_filter_field) {
        frag += '<a class="btn btn-info facetview_inactive_link facetview_filterselected" href="' + field + '">';
        frag += '<span class="facetview_filterselected_text"><strong>' + display + '</strong></span>';
        frag += "</a>"
    }

    var data_from = value.from ? " data-from='" + value.from + "' " : "";

    var valdisp = value.from;
    if (facet.value_function) {
        valdisp = facet.value_function(valdisp);
    }

    frag += '<a class="facetview_filterselected facetview_clear btn btn-info" data-field="' + field + '" ' + data_from +
            ' alt="remove" title="remove" href="#">'
    frag += '<span class="facetview_filterselected_text">' + escapeHtml(valdisp) + '</span> <i class="icon-white icon-remove" style="margin-top:1px;"></i>'
    frag += "</a>"

    frag += "</div>"

    return frag
}

/////////////////////////////////////////////////////////////////////////////////////////////

///// behaviour functions //////////////////////////

// called when searching begins.  Use it to show the loading bar, or something
function showSearchingNotification(options, context) {
    $(".facetview_searching", context).show()
}

// called when searching completes.  Use it to hide the loading bar
function hideSearchingNotification(options, context) {
    $(".facetview_searching", context).hide()
}

// called once facet has been populated.  Visibility is calculated for you
// so just need to disable/hide the facet depending on the facet.hide_inactive
// configuration
function setFacetVisibility(options, context, facet, visible) {
    var el = context.find("#facetview_filter_" + safeId(facet.field))
    el.find('.facetview_filtershow').css({'color':'#333','font-weight':'bold'}).children('i').show();
    if (visible) {
        el.show();
    } else {
        if (facet.hide_inactive) {
            el.hide();
        }
        el.find('.facetview_filtershow').css({'color':'#ccc','font-weight':'normal'}).children('i').hide();
    };
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
        el.find(".facetview_filtervalue").show()
    } else {
        el.find(".facetview_filtershow").find("i").removeClass("icon-minus");
        el.find(".facetview_filtershow").find("i").addClass("icon-plus");
        el.find(".facetview_tooltip").hide();
        el.find(".facetview_tooltip_value").hide();
        el.find(".facetview_filteroptions").hide();
        el.find(".facetview_filtervalue").hide()
    }
}

// set the UI to present the given ordering
function setResultsOrder(options, context, order) {
    if (order === 'asc') {
        $('.facetview_order', context).html('<i class="icon-arrow-up"></i>');
        $('.facetview_order', context).attr('href','asc');
        $('.facetview_order', context).attr('title','current order ascending. Click to change to descending');
    } else {
        $('.facetview_order', context).html('<i class="icon-arrow-down"></i>');
        $('.facetview_order', context).attr('href','desc');
        $('.facetview_order', context).attr('title','current order descending. Click to change to ascending');
    }
}

// set the UI to present the given page size
function setUIPageSize(options, context, params) {
    var size = params.size;
    $('.facetview_pagesize', context).html(size);
}

// set the UI to present the given ordering
function setUIOrder(options, context, params) {
    var order = params.order;
    options.behaviour_results_ordering(options, context, order)
}

// set the UI to present the order by field
function setUIOrderBy(options, context, params) {
    var orderby = params.orderby;
    $(".facetview_orderby", context).val(orderby)
}

function setUISearchField(options, context, params) {
    var field = params.field;
    $(".facetview_searchfield", context).val(field)
}

function setUISearchString(options, context, params) {
    var q = params.q;
    $(".facetview_freetext", context).val(q)
}

function setUIFacetSize(options, context, params) {
    var facet = params.facet;
    var el = facetElement("#facetview_facetvals_", facet["field"], context);
    el.html(facet.size)
}

function setUIFacetSort(options, context, params) {
    var facet = params.facet
    var el = facetElement("#facetview_sort_", facet["field"], context);
    if (facet.order === "reverse_term") {
        el.html('a-z <i class="icon-arrow-up"></i>');
    } else if (facet.order === "count") {
        el.html('count <i class="icon-arrow-down"></i>');
    } else if (facet.order === "reverse_count") {
        el.html('count <i class="icon-arrow-up"></i>');
    } else if (facet.order === "term") {
        el.html('a-z <i class="icon-arrow-down"></i>');
    }
}

function setUIFacetAndOr(options, context, params) {
    var facet = params.facet
    var el = facetElement("#facetview_or_", facet["field"], context);
    if (facet.logic === "OR") {
        el.css({'color':'#333'});

        // FIXME: resolve this when we get to the filter display
        $('.facetview_filterselected[rel="' + $(this).attr('href') + '"]', context).addClass('facetview_logic_or');
    } else {
        el.css({'color':'#aaa'});

        // FIXME: resolve this when we got to the filter display
        $('.facetview_filterselected[rel="' + $(this).attr('href') + '"]', context).removeClass('facetview_logic_or');
    }
}

function setUISelectedFilters(options, context) {
    var frag = "";
    for (var field in options.active_filters) {
        if (options.active_filters.hasOwnProperty(field)) {
            var filter_list = options.active_filters[field];
            var facet = selectFacet(options, field);
            if (facet.type === "terms") {
                frag += options.render_active_terms_filter(options, facet, field, filter_list)
            } else if (facet.type === "range") {
                frag += options.render_active_range_filter(options, facet, field, filter_list)
            } else if (facet.type === "geo_distance") {
                frag += options.render_active_geo_filter(options, facet, field, filter_list)
            } else if (facet.type === "date_histogram") {
                frag += options.render_active_date_histogram_filter(options, facet, field, filter_list)
            }
            // FIXME: statistical facet?
        }
    }
    $('#facetview_selectedfilters', context).html(frag);
}

function setUIShareUrlChange(options, context) {
    if (options.current_short_url && options.show_short_url) {
        $(".facetview_shorten_url", context).hide();
        $(".facetview_lengthen_url", context).show();
    } else {
        $(".facetview_shorten_url", context).show();
        $(".facetview_lengthen_url", context).hide();
    }
}

function dateHistogramShowAll(options, context, facet) {
    var el = context.find("#facetview_filter_" + safeId(facet.field));
    el.find(".facetview_date_histogram_short").hide();
    el.find(".facetview_date_histogram_full").show();
}

function dateHistogramShowLess(options, context, facet) {
    var el = context.find("#facetview_filter_" + safeId(facet.field));
    el.find(".facetview_date_histogram_full").hide();
    el.find(".facetview_date_histogram_short").show();
}
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

/*
 * jquery.facetview2.js
 *
 * displays faceted browse results by querying a specified elasticsearch index
 *
 * http://cottagelabs.com
 *
 */

/*****************************************************************************
 * JAVASCRIPT PATCHES
 ****************************************************************************/

// Deal with indexOf issue in <IE9
// provided by commentary in repo issue - https://github.com/okfn/facetview/issues/18
if (!Array.prototype.indexOf) {
    Array.prototype.indexOf = function(searchElement /*, fromIndex */ ) {
        "use strict";
        if (this == null) {
            throw new TypeError();
        }
        var t = Object(this);
        var len = t.length >>> 0;
        if (len === 0) {
            return -1;
        }
        var n = 0;
        if (arguments.length > 1) {
            n = Number(arguments[1]);
            if (n != n) { // shortcut for verifying if it's NaN
                n = 0;
            } else if (n != 0 && n != Infinity && n != -Infinity) {
                n = (n > 0 || -1) * Math.floor(Math.abs(n));
            }
        }
        if (n >= len) {
            return -1;
        }
        var k = n >= 0 ? n : Math.max(len - Math.abs(n), 0);
        for (; k < len; k++) {
            if (k in t && t[k] === searchElement) {
                return k;
            }
        }
        return -1;
    }
}

/*****************************************************************************
 * UTILITIES
 ****************************************************************************/

// first define the bind with delay function from (saves loading it separately) 
// https://github.com/bgrins/bindWithDelay/blob/master/bindWithDelay.js
(function($) {
    $.fn.bindWithDelay = function( type, data, fn, timeout, throttle ) {
        var wait = null;
        var that = this;

        if ( $.isFunction( data ) ) {
            throttle = timeout;
            timeout = fn;
            fn = data;
            data = undefined;
        }

        function cb() {
            var e = $.extend(true, { }, arguments[0]);
            var throttler = function() {
                wait = null;
                fn.apply(that, [e]);
            };

            if (!throttle) { clearTimeout(wait); }
            if (!throttle || !wait) { wait = setTimeout(throttler, timeout); }
        }

        return this.bind(type, data, cb);
    };
})(jQuery);

function safeId(s) {
    return s.replace(/\./gi,'_').replace(/\:/gi,'_')
}

// get the right facet element from the page
function facetElement(prefix, name, context) {
    return $(prefix + safeId(name), context)
}

// get the right facet from the options, based on the name
function selectFacet(options, name) {
    for (var i = 0; i < options.facets.length; i++) {
        var item = options.facets[i];
        if ('field' in item) {
            if (item['field'] === name) {
                return item
            }
        }
    }
}

function endsWith(str, suffix) {
    return str.indexOf(suffix, str.length - suffix.length) !== -1;
}

function ie8compat(o) {
    // Clean up all array options
    // IE8 interprets trailing commas as introducing an undefined
    // object, e.g. ["a", "b", "c",] means ["a", "b", "c", undefined]
    // in IE8. And maybe in older IE-s. So the user loading
    // facetview might have put trailing commas in their config, but
    // this will cause facetview to break in IE8 - so clean up!

    function delete_last_element_of_array_if_undefined(array, recurse) {
        var recurse = recurse || false;
        if ($.type(array) == 'array') {
            // delete the last item if it's undefined
            if (array.length > 0 && $.type(array[array.length - 1]) == 'undefined') {
                array.splice(array.length - 1, 1);
            }
        }
        if (recurse) {
            for ( var each = 0; each < array.length; each++ ) {
                if ($.type(array[each]) == 'array') {
                    delete_last_element_of_array_if_undefined(array[each], true);
                }
            }
        }
    }

    // first see if this clean up is necessary at all
    var test = ["a", "b", "c", ];  // note trailing comma, will produce ["a", "b", "c", undefined] in IE8 and ["a", "b", "c"] in every sane browser
    if ($.type(test[test.length - 1]) == 'undefined') {
        // ok, cleanup is necessary, go
        for (var key in o) {
            if (o.hasOwnProperty(key)) {
                var option = o[key];
                delete_last_element_of_array_if_undefined(option, true);
            }
        }
    }
}

/******************************************************************
 * DEFAULT CALLBACKS
 *****************************************************************/
 
///// the lifecycle callbacks ///////////////////////
function postInit(options, context) {}
function preSearch(options, context) {}
function postSearch(options, context) {}
function preRender(options, context) {}
function postRender(options, context) {}

/******************************************************************
 * URL MANAGEMENT
 *****************************************************************/

function shareableUrl(options, query_part_only, include_fragment) {
    var source = elasticSearchQuery({"options" : options, "include_facets" : options.include_facets_in_url, "include_fields" : options.include_fields_in_url})
    var querypart = "?source=" + encodeURIComponent(serialiseQueryObject(source))
    include_fragment = include_fragment === undefined ? true : include_fragment
    if (include_fragment) {
        var fragment_identifier = options.url_fragment_identifier ? options.url_fragment_identifier : "";
        querypart += fragment_identifier
    }
    if (query_part_only) {
        return querypart
    }
    return 'http://' + window.location.host + window.location.pathname + querypart
}

function getUrlVars() {
    var params = new Object;
    var url = window.location.href;
    var anchor = undefined;
    if (url.indexOf("#") > -1) {
        anchor = url.slice(url.indexOf('#'));
        url = url.substring(0, url.indexOf('#'));
    }
    var hashes = url.slice(window.location.href.indexOf('?') + 1).split('&');
    for (var i = 0; i < hashes.length; i++) {
        var hash = hashes[i].split('=');
        if (hash.length > 1) {
            var newval = decodeURIComponent(hash[1]);
            if (newval[0] == "[" || newval[0] == "{") {
                // if it looks like a JSON object in string form...
                // remove " (double quotes) at beginning and end of string to make it a valid 
                // representation of a JSON object, or the parser will complain
                newval = newval.replace(/^"/,"").replace(/"$/,"");
                var newval = JSON.parse(newval);
            }
            params[hash[0]] = newval;
        }
    }
    if (anchor) {
        params['url_fragment_identifier'] = anchor;
    }
    
    return params;
}
 
/******************************************************************
 * FACETVIEW ITSELF
 *****************************************************************/

(function($){
    $.fn.facetview = function(options) {
    
        /**************************************************************
         * handle the incoming options, default options and url parameters
         *************************************************************/
         
        // all of the possible options that will be used in the facetview lifecycle
        // along with their documentation
        var defaults = {
            ///// elasticsearch parameters /////////////////////////////
            
            // the base search url which will respond to elasticsearch queries.  Generally ends with _search
            "search_url" : "http://localhost:9200/_search",
            
            // datatype for ajax requests to use - overall recommend using jsonp
            "datatype" : "jsonp",
            
            // if set, should be either * or ~
            // if *, * will be prepended and appended to each string in the freetext search term
            // if ~, ~ then ~ will be appended to each string in the freetext search term. 
            // If * or ~ or : are already in the freetext search term, no action will be taken. 
            "default_freetext_fuzzify": false, // or ~ or *
            
            // due to a bug in elasticsearch's clustered node facet counts, we need to inflate
            // the number of facet results we need to ensure that the results we actually want are
            // accurate.  This option tells us by how much.
            "elasticsearch_facet_inflation" : 100,
            
            ///// query aspects /////////////////////////////
            
            // list of fields to be returned by the elasticsearch query.  If omitted, full result set is returned
            "fields" : false, // or an array of field names
            
            // list of partial fields to be returned by the elasticsearch query.  If omitted, full result set is returned
            "partial_fields" : false, // or an array of partial fields

            // list of script fields to be executed.  Note that you should, in general, not pass actual scripts but
            // references to stored scripts in the back-end ES.  If not false, then an object corresponding to the
            // ES script_fields structure
            "script_fields" : false,
            
            // number of results to display per page (i.e. to retrieve per query)
            "page_size" : 10,
            
            // cursor position in the elasticsearch result set
            "from" : 0,
            
            // list of fields and directions to sort in.  Note that the UI only supports single value sorting
            "sort" : [], // or something like [ {"title" : {"order" : "asc"}} ]
            
            // field on which to focus the freetext search
            "searchfield" : "", // e.g. title.exact
            
            // freetext search string
            "q" : "",
            
            ///// facet aspects /////////////////////////////
            
            // The list of facets to be displayed and used to seed the filtering processes.
            // Facets are complex fields which can look as follows:
            /*
            {
                "field" : "<elasticsearch field>"                                   // field upon which to facet
                "display" : "<display name>",                                       // display name for the UI
                "type": "terms|range|geo_distance|statistical|date_histogram",      // the kind of facet this will be
                "open" : true|false,                                                // whether the facet should be open or closed (initially)
                "hidden" : true|false                                               // whether the facet should be displayed at all (e.g. you may just want the data for a callback)
                "disabled" : true|false                                             // whether the facet should be acted upon in any way.  This might be useful if you want to enable/disable facets under different circumstances via a callback
                "tooltip" : "<html to be displayed under the facet's tool tip>"     // if present the facet will present a link with the tooltip_text which would give the user some text or other functionality
                "tooltip_text" : "<text to use to open the tooltip>",               // sets the text of the tooltip link

                // terms facet only
                
                "size" : <num>,                                                     // how many terms should the facet limit to
                "logic" : "AND|OR",                                                 // Whether to AND or OR selected facets together when filtering
                "order" : "count|reverse_count|term|reverse_term",                  // which standard ordering to use for facet values
                "deactivate_threshold" : <num>,                                     // number of facet terms below which the facet is disabled
                "hide_inactive" : true|false,                                       // whether to hide or just disable the facet if below deactivate threshold
                "value_function" : <function>,                                      // function to be called on each value before display
                "controls" : true|false                                             // should the facet sort/size/bool controls be shown?
                "ignore_empty_string" : true|false                                  // should the terms facet ignore empty strings in display
                
                // range facet only
                
                "range" : [                                                         // list of ranges (in order) which define the filters
                    {"from" : <num>, "to" : <num>, "display" : "<display name>"}    // from = lower bound (inclusive), to = upper boud (exclusive)
                ],                                                                  // display = display name for this range
                "hide_empty_range" : true|false,                                    // if there are no results for a given range, should it be hidden
                
                // geo distance facet only
                
                "distance" : [                                                      // list of distances (in order) which define the filters
                    {"from" : <num>, "to" : <num>, "display" : "<display name>"}    // from = lower bound (inclusive), to = upper boud (exclusive)
                ],                                                                  // display = display name for this distance
                "hide_empty_distance" : true|false,                                 // if there are no results for a given distance, should it be hidden
                "unit" : "<unit of distance, e.g. km or mi>"                        // unit to calculate distances in (e.g. km or mi)
                "lat" : <latitude>                                                  // latitude from which to measure distances
                "lon" : <longitude>                                                 // longitude from which to measure distances

                // date histogram facet only
                "interval" : "year, quarter, month, week, day, hour, minute ,second"  // period to use for date histogram
                "sort" : "asc|desc",                                                // which ordering to use for date histogram
                "hide_empty_date_bin" : true|false                                  // whether to suppress display of date range with no values
                "short_display" : <number to display initially>                     // the number of values to show initially (note you should set size=false)

                // admin use only
                
                "values" : <object>                                                 // the values associated with a successful query on this facet
            }
            */
            "facets" : [],
            
            // user defined extra facets.  These must be pre-formatted for elasticsearch, and they will
            // simply be added to the query at query-time.
            "extra_facets": {},
            
            // default settings for each of the facet properties above.  If a facet lacks a property, it will
            // be initialised to the default
            "default_facet_type" : "terms",
            "default_facet_open" : false,
            "default_facet_hidden" : false,
            "default_facet_size" : 10,
            "default_facet_operator" : "AND",  // logic
            "default_facet_order" : "count",
            "default_facet_hide_inactive" : false,
            "default_facet_deactivate_threshold" : 0, // equal to or less than this number will deactivate the facet
            "default_facet_controls" : true,
            "default_hide_empty_range" : true,
            "default_hide_empty_distance" : true,
            "default_distance_unit" : "km",
            "default_distance_lat" : 51.4768,       // Greenwich meridian (give or take a few decimal places)
            "default_distance_lon" : 0.0,           //
            "default_date_histogram_interval" : "year",
            "default_hide_empty_date_bin" : true,
            "default_date_histogram_sort" : "asc",
            "default_short_display" : false,
            "default_ignore_empty_string" : false,      // because filtering out empty strings is less performant
            "default_tooltip" : false,
            "default_tooltip_text" : "learn more",


            ///// search bar configuration /////////////////////////////
            
            // list of options by which the search results can be sorted
            // of the form of a list of: { 'display' : '<display name>', 'field' : '<field to sort by>'},
            "search_sortby" : [],
            
            // list of options for fields to which free text search can be constrained
            // of the form of a list of: { 'display' : '<display name>', 'field' : '<field to search on>'},
            "searchbox_fieldselect" : [],
            
            // enable the share/save link feature
            "sharesave_link" : true,

            // provide a function which will do url shortening for the sharesave_link box
            "url_shortener" : false,
            
            // on free-text search, default operator for the elasticsearch query system to use
            "default_operator" : "OR",
            
            // enable the search button
            "search_button" : false,
            
            // amount of time between finishing typing and when a query is executed from the search box
            "freetext_submit_delay" : 500,
            
            ///// url configuration /////////////////////////////
            
            // FIXME: should we read in facets from urls, and if we do, what should we do about them?
            // should facets be included in shareable urls.  Turning this on makes them very long, and currently
            // facetview does not read those facets back in if the URLs are parsed
            "include_facets_in_url" : false,
            
            // FIXME: should we read in fields from urls, and if we do, what should we do about them?
            // should fields be included in shareable urls.  Turning this on makes them very long, and currently
            // facetview does not read those fields back in if the URLs are parsed
            "include_fields_in_url" : false,
            
            ///// selected filters /////////////////////////////
            
            // should the facet navigation show filters alongside other facet results which have not been selected
            "selected_filters_in_facet" : true,
            
            // should the "selected filters" area show the name of the facet from which the filter was selected
            "show_filter_field" : true,
            
            // should the "selected filters" area show the boolean logic used by the filter (taken from the facet.logic configuration)
            "show_filter_logic" : true,
            
            // FIXME: add support for pre-defined range filters
            // a set of pre-defined filters which will always be applied to the search.
            // Has the following structure, and works for terms filters only
            // { "<field>" : ["<list of values>"] }
            // requires a facet for the given field to be defined
            "predefined_filters" : {},
            
            // exclude any values that appear in pre-defined filters from any facets
            // This prevents configuration-set filters from ever being seen in a facet, but ensures that
            // they are always included when the search is carried out
            "exclude_predefined_filters_from_facets" : true,
            
            // current active filters
            // DO NOT USE - this is for tracking internal state ONLY
            "active_filters" : {},
            
            ///// general behaviour /////////////////////////////
            
            // after initialisation, begin automatically with a search
            "initialsearch" : true,
            
            // enable debug.  If debug is enabled, some technical information will be dumped to a 
            // visible textarea on the screen
            "debug" : false,
            
            // after search, the results will fade in over this number of milliseconds
            "fadein" : 800,
            
            // should the search url be synchronised with the browser's url bar after search
            // NOTE: does not work in some browsers.  See also share/save link option.
            "pushstate" : true,
            
            ///// render functions /////////////////////////////
            
            // for each render function, see the reference implementation for documentation on how they should work
            
            // render the frame within which the facetview sits
            "render_the_facetview" : theFacetview,
            
            // render the search options - containing freetext search, sorting, etc
            "render_search_options" : searchOptions,
            
            // render the list of available facets.  This will in turn call individual render methods
            // for each facet type
            "render_facet_list" : facetList,
            
            // render the terms facet, the list of values, and the value itself
            "render_terms_facet" : renderTermsFacet,                 // overall framework for a terms facet
            "render_terms_facet_values" : renderTermsFacetValues,    // the list of terms facet values
            "render_terms_facet_result" : renderTermsFacetResult,    // individual terms facet values
            
            // render the range facet, the list of values, and the value itself
            "render_range_facet" : renderRangeFacet,                // overall framework for a range facet
            "render_range_facet_values" : renderRangeFacetValues,   // the list of range facet values
            "render_range_facet_result" : renderRangeFacetResult,   // individual range facet values
            
            // render the geo distance facet, the list of values and the value itself
            "render_geo_facet" : renderGeoFacet,                // overall framework for a geo distance facet
            "render_geo_facet_values" : renderGeoFacetValues,   // the list of geo distance facet values
            "render_geo_facet_result" : renderGeoFacetResult,   // individual geo distance facet values

            // render the date histogram facet
            "render_date_histogram_facet" : renderDateHistogramFacet,
            "render_date_histogram_values" : renderDateHistogramValues,
            "render_date_histogram_result" : renderDateHistogramResult,
            
            // render any searching notification (which will then be shown/hidden as needed)
            "render_searching_notification" : searchingNotification,
            
            // render the paging controls
            "render_results_metadata" : basicPager, // or pageSlider
            
            // render a "results not found" message
            "render_not_found" : renderNotFound,
            
            // render an individual result record
            "render_result_record" : renderResultRecord,
            
            // render a terms filter interface component (e.g. the filter name, boolean operator used, and selected values)
            "render_active_terms_filter" : renderActiveTermsFilter,
            
            // render a range filter interface component (e.g. the filter name and the human readable description of the selected range)
            "render_active_range_filter" : renderActiveRangeFilter,
            
            // render a geo distance filter interface component (e.g. the filter name and the human readable description of the selected range)
            "render_active_geo_filter" : renderActiveGeoFilter,

            // render a date histogram/range interface component (e.g. the filter name and the human readable description of the selected range)
            "render_active_date_histogram_filter" : renderActiveDateHistogramFilter,
            
            ///// configs for standard render functions /////////////////////////////
            
            // if you provide your own render functions you may or may not want to re-use these
            "resultwrap_start":"<tr><td>",
            "resultwrap_end":"</td></tr>",
            "result_display" : [ [ {"pre" : "<strong>ID</strong>:", "field": "id", "post" : "<br><br>"} ] ],
            "results_render_callbacks" : {},
            
            ///// behaviour functions /////////////////////////////
            
            // called at the start of searching to display the searching notification
            "behaviour_show_searching" : showSearchingNotification,
            
            // called at the end of searching to hide the searching notification
            "behaviour_finished_searching" : hideSearchingNotification,
            
            // called after rendering a facet to determine whether it is visible/disabled
            "behaviour_facet_visibility" : setFacetVisibility,
            
            // called after rendering a facet to determine whether it should be open or closed
            "behaviour_toggle_facet_open" : setFacetOpenness,
            
            // called after changing the result set order to update the search bar
            "behaviour_results_ordering" : setResultsOrder,

            // called when the page size is changed
            "behaviour_set_page_size" : setUIPageSize,

            // called when the page order is changed
            "behaviour_set_order" : setUIOrder,

            // called when the field we order by is changed
            "behaviour_set_order_by" : setUIOrderBy,

            // called when the search field is changed
            "behaviour_set_search_field" : setUISearchField,

            // called when the search string is set or updated
            "behaviour_set_search_string" : setUISearchString,

            // called when the facet size has been changed
            "behaviour_set_facet_size" : setUIFacetSize,

            // called when the facet sort order has changed
            "behaviour_set_facet_sort" : setUIFacetSort,

            // called when the facet And/Or setting has been changed
            "behaviour_set_facet_and_or" : setUIFacetAndOr,

            // called when the selected filters have changed
            "behaviour_set_selected_filters" : setUISelectedFilters,

            // called when the share url is shortened/lengthened
            "behaviour_share_url" : setUIShareUrlChange,

            "behaviour_date_histogram_showall" : dateHistogramShowAll,
            "behaviour_date_histogram_showless" : dateHistogramShowLess,
            
            ///// lifecycle callbacks /////////////////////////////
            
            // the default callbacks don't have any effect - replace them as needed
            
            "post_init_callback" : postInit,
            "pre_search_callback" : preSearch,
            "post_search_callback" : postSearch,
            "pre_render_callback" : preRender,
            "post_render_callback" : postRender,
            
            ///// internal state monitoring /////////////////////////////
            
            // these are used internally DO NOT USE
            // they are here for completeness and documentation
            
            // is a search currently in progress
            "searching" : false,
            
            // the raw query object
            "queryobj" : false,
            
            // the raw data coming back from elasticsearch
            "rawdata" : false,
            
            // the parsed data from elasticsearch
            "data" : false,

            // the short url for the current search, if it has been generated
            "current_short_url" : false,

            // should the short url or the long url be displayed to the user?
            "show_short_url" : false
        };
        
        function deriveOptions() {
            // cleanup for ie8 purposes
            ie8compat(options);
            ie8compat(defaults);
            
            // extend the defaults with the provided options
            var provided_options = $.extend(defaults, options);
            
            // deal with the options that come from the url, which require some special treatment
            var url_params = getUrlVars();
            var url_options = {};
            if ("source" in url_params) {
                url_options = optionsFromQuery(url_params["source"])
            }
            if ("url_fragment_identifier" in url_params) {
                url_options["url_fragment_identifier"] = url_params["url_fragment_identifier"]
            }
            provided_options = $.extend(provided_options, url_options);
            
            // copy the _selected_operators data into the relevant facets
            // for each pre-selected operator, find the related facet and set its "logic" property
            var so = provided_options._selected_operators ? provided_options._selected_operators : {};
            for (var field in so) {
                if (so.hasOwnProperty(field)) {
                    var operator = so[field];
                    for (var i=0; i < provided_options.facets.length; i=i+1) {
                        var facet = provided_options.facets[i];
                        if (facet.field === field) {
                            facet["logic"] = operator
                        }
                    }
                }
            }
            if ("_selected_operators" in provided_options) {
                delete provided_options._selected_operators
            }
            
            // tease apart the active filters from the predefined filters
            if (!provided_options.predefined_filters) {
                provided_options["active_filters"] = provided_options._active_filters
                delete provided_options._active_filters
            } else {
                provided_options["active_filters"] = {};
                for (var field in provided_options._active_filters) {
                    if (provided_options._active_filters.hasOwnProperty(field)) {
                        var filter_list = provided_options._active_filters[field];
                        provided_options["active_filters"][field] = [];
                        if (!(field in provided_options.predefined_filters)) {
                            provided_options["active_filters"][field] = filter_list
                        } else {
                            // FIXME: this does not support pre-defined range queries
                            var predefined_values = provided_options.predefined_filters[field];
                            for (var i=0; i < filter_list.length; i=i+1) {
                                var value = filter_list[i];
                                if ($.inArray(value, predefined_values) === -1) {
                                    provided_options["active_filters"][field].push(value)
                                }
                            }
                        }
                        if (provided_options["active_filters"][field].length === 0) {
                            delete provided_options["active_filters"][field]
                        }
                    }
                }
            }
            
            // copy in the defaults to the individual facets when they are needed
            for (var i=0; i < provided_options.facets.length; i=i+1) {
                var facet = provided_options.facets[i];
                if (!("type" in facet)) { facet["type"] = provided_options.default_facet_type }
                if (!("open" in facet)) { facet["open"] = provided_options.default_facet_open }
                if (!("hidden" in facet)) { facet["hidden"] = provided_options.default_facet_hidden }
                if (!("size" in facet)) { facet["size"] = provided_options.default_facet_size }
                if (!("logic" in facet)) { facet["logic"] = provided_options.default_facet_operator }
                if (!("order" in facet)) { facet["order"] = provided_options.default_facet_order }
                if (!("hide_inactive" in facet)) { facet["hide_inactive"] = provided_options.default_facet_hide_inactive }
                if (!("deactivate_threshold" in facet)) { facet["deactivate_threshold"] = provided_options.default_facet_deactivate_threshold }
                if (!("controls" in facet)) { facet["controls"] = provided_options.default_facet_controls }
                if (!("hide_empty_range" in facet)) { facet["hide_empty_range"] = provided_options.default_hide_empty_range }
                if (!("hide_empty_distance" in facet)) { facet["hide_empty_distance"] = provided_options.default_hide_empty_distance }
                if (!("unit" in facet)) { facet["unit"] = provided_options.default_distance_unit }
                if (!("lat" in facet)) { facet["lat"] = provided_options.default_distance_lat }
                if (!("lon" in facet)) { facet["lon"] = provided_options.default_distance_lon }
                if (!("value_function" in facet)) { facet["value_function"] = function(value) { return value } }
                if (!("interval" in facet)) { facet["interval"] = provided_options.default_date_histogram_interval }
                if (!("hide_empty_date_bin" in facet)) { facet["hide_empty_date_bin"] = provided_options.default_hide_empty_date_bin }
                if (!("sort" in facet)) { facet["sort"] = provided_options.default_date_histogram_sort }
                if (!("disabled" in facet)) { facet["disabled"] = false }   // no default setter for this - if you don't specify disabled, they are not disabled
                if (!("short_display" in facet)) { facet["short_display"] = provided_options.default_short_display }
                if (!("ignore_empty_string" in facet)) { facet["ignore_empty_string"] = provided_options.default_ignore_empty_string }
                if (!("tooltip" in facet)) { facet["tooltip"] = provided_options.default_tooltip }
                if (!("tooltip_text" in facet)) { facet["tooltip_text"] = provided_options.default_tooltip_text }
            }
            
            return provided_options
        }
        
        /******************************************************************
         * OPTIONS MANAGEMENT
         *****************************************************************/

        function uiFromOptions() {
            // set the current page size
            options.behaviour_set_page_size(options, obj, {size: options.page_size});
            
            // set the search order
            // NOTE: that this interface only supports single field ordering
            var sorting = options.sort;

            for (var i = 0; i < sorting.length; i++) {
                var so = sorting[i];
                var fields = Object.keys(so);
                for (var j = 0; j < fields.length; j++) {
                    var dir = so[fields[j]]["order"];
                    options.behaviour_set_order(options, obj, {order: dir});
                    options.behaviour_set_order_by(options, obj, {orderby: fields[j]});
                    break
                }
                break
            }
            
            // set the search field
            options.behaviour_set_search_field(options, obj, {field : options.searchfield});
            
            // set the search string
            options.behaviour_set_search_string(options, obj, {q: options.q});
            
            // for each facet, set the facet size, order and and/or status
            for (var i=0; i < options.facets.length; i=i+1) {
                var f = options.facets[i];
                if (f.hidden) {
                    continue;
                }
                options.behaviour_set_facet_size(options, obj, {facet : f});
                options.behaviour_set_facet_sort(options, obj, {facet : f});
                options.behaviour_set_facet_and_or(options, obj, {facet : f});
            }
            
            // for any existing filters, render them
            options.behaviour_set_selected_filters(options, obj);
        }
        
        function urlFromOptions() {
            
            if (options.pushstate && 'pushState' in window.history) {
                var querypart = shareableUrl(options, true, true);
                window.history.pushState("", "search", querypart);
            }

            // also set the default shareable url at this point
            setShareableUrl()
        }
        
        /******************************************************************
         * DEBUG
         *****************************************************************/

        function addDebug(msg, context) {
            $(".facetview_debug", context).show().find("textarea").append(msg + "\n\n")
        }
        
        /**************************************************************
         * functions for managing search option events
         *************************************************************/
        
        /////// paging /////////////////////////////////
        
        // adjust how many results are shown
        function clickPageSize(event) {
            event.preventDefault();
            var newhowmany = prompt('Currently displaying ' + options.page_size + 
                ' results per page. How many would you like instead?');
            if (newhowmany) {
                options.page_size = parseInt(newhowmany);
                options.from = 0;
                options.behaviour_set_page_size(options, obj, {size: options.page_size});
                doSearch();
            }
        }

        /////// start again /////////////////////////////////
        
        // erase the current search and reload the window
        function clickStartAgain(event) {
            event.preventDefault();
            var base = window.location.href.split("?")[0];
            window.location.replace(base);
        }
        
        /////// search ordering /////////////////////////////////
        
        function clickOrder(event) {
            event.preventDefault();
            
            // switch the sort options around
            if ($(this).attr('href') == 'desc') {
                options.behaviour_set_order(options, obj, {order: "asc"})
            } else {
                options.behaviour_set_order(options, obj, {order: "desc"})
            };
            
            // synchronise the new sort with the options
            saveSortOption();
            
            // reset the cursor and issue a search
            options.from = 0;
            doSearch();
        }
        
        function changeOrderBy(event) {
            event.preventDefault();
            
            // synchronise the new sort with the options
            saveSortOption();
            
            // reset the cursor and issue a search
            options.from = 0;
            doSearch();
        }

        // save the sort options from the current UI
        function saveSortOption() {
            var sortchoice = $('.facetview_orderby', obj).val();
            if (sortchoice.length != 0) {
                var sorting = [];
                if (sortchoice.indexOf('[') === 0) {
                    sort_fields = JSON.parse(sortchoice.replace(/'/g, '"'));
                    for ( var each = 0; each < sort_fields.length; each++ ) {
                        sf = sort_fields[each];
                        sortobj = {};
                        sortobj[sf] = {'order': $('.facetview_order', obj).attr('href')};
                        sorting.push(sortobj);
                    }
                } else {
                    sortobj = {};
                    sortobj[sortchoice] = {'order': $('.facetview_order', obj).attr('href')};
                    sorting.push(sortobj);
                }
                
                options.sort = sorting;
            } else {
                sortobj = {};
                sortobj["_score"] = {'order': $('.facetview_order', obj).attr('href')};
                sorting = [sortobj];
                options.sort = sorting
            }
        }
        
        /////// search fields /////////////////////////////////
        
        // adjust the search field focus
        function changeSearchField(event) {
            event.preventDefault();
            var field = $(this).val();
            options.from = 0;
            options.searchfield = field;
            doSearch();
        };
        
        // keyup in search box
        function keyupSearchText(event) {
            event.preventDefault();
            var q = $(this).val();
            options.from = 0;
            options.q = q;
            doSearch()
        }
        
        // click of the search button
        function clickSearch() {
            event.preventDefault();
            var q = $(".facetview_freetext", obj).val();
            options.from = 0;
            options.q = q;
            doSearch()
        }

        /////// share save link /////////////////////////////////
        
        // show the current url with the result set as the source param
        function clickShareSave(event) {
            event.preventDefault();
            $('.facetview_sharesavebox', obj).toggle();
        }

        function clickShortenUrl(event) {
            event.preventDefault();
            if (!options.url_shortener) {
                return;
            }

            if (options.current_short_url) {
                options.show_short_url = true;
                setShareableUrl();
                return;
            }

            function shortenCallback(short_url) {
                if (!short_url) {
                    return;
                }
                options.current_short_url = short_url;
                options.show_short_url = true;
                setShareableUrl();
            }

            var source = elasticSearchQuery({
                "options" : options,
                "include_facets" : options.include_facets_in_url,
                "include_fields" : options.include_fields_in_url
            });
            options.url_shortener(source, shortenCallback);
        }

        function clickLengthenUrl(event) {
            event.preventDefault();
            options.show_short_url = false;
            setShareableUrl();
        }

        function setShareableUrl() {
            if (options.sharesave_link) {
                if (options.current_short_url && options.show_short_url) {
                    $('.facetview_sharesaveurl', obj).val(options.current_short_url)
                } else {
                    var shareable = shareableUrl(options);
                    $('.facetview_sharesaveurl', obj).val(shareable);
                }
                options.behaviour_share_url(options, obj);
            }
        }
        
        /**************************************************************
         * functions for handling facet events
         *************************************************************/

        /////// show/hide filter values /////////////////////////////////
        
        // show the filter values
        function clickFilterShow(event) {
            event.preventDefault();
            
            var name = $(this).attr("href");
            var facet = selectFacet(options, name);
            var el = facetElement("#facetview_filter_", name, obj);
            
            facet.open = !facet.open;
            options.behaviour_toggle_facet_open(options, obj, facet)
        }
        
        /////// change facet length /////////////////////////////////
        
        // adjust how many results are shown
        function clickMoreFacetVals(event) {
            event.preventDefault();
            var morewhat = selectFacet(options, $(this).attr("href"));
            if ('size' in morewhat ) {
                var currentval = morewhat['size'];
            } else {
                var currentval = options.default_facet_size;
            }
            var newmore = prompt('Currently showing ' + currentval + '. How many would you like instead?');
            if (newmore) {
                morewhat['size'] = parseInt(newmore);
                options.behaviour_set_facet_size(options, obj, {facet: morewhat})
                doSearch();
            }
        }

        /////// sorting facets /////////////////////////////////
        
        function clickSort(event) {
            event.preventDefault();
            var sortwhat = selectFacet(options, $(this).attr('href'));
            
            var cycle = {
                "term" : "reverse_term",
                "reverse_term" : "count",
                "count" : "reverse_count",
                "reverse_count": "term"
            };
            sortwhat["order"] = cycle[sortwhat["order"]];
            options.behaviour_set_facet_sort(options, obj, {facet: sortwhat});
            doSearch();
        }
        
        /////// AND vs OR on facet selection /////////////////////////////////
        
        // function to switch filters to OR instead of AND
        function clickOr(event) {
            event.preventDefault();
            var orwhat = selectFacet(options, $(this).attr('href'));
            
            var cycle = {
                "OR" : "AND",
                "AND" : "OR"
            }
            orwhat["logic"] = cycle[orwhat["logic"]];
            options.behaviour_set_facet_and_or(options, obj, {facet: orwhat});
            options.behaviour_set_selected_filters(options, obj);
            doSearch();
        }

        ////////// All/Less date histogram values /////////////////////////////

        function clickDHAll(event) {
            event.preventDefault();
            var facet = selectFacet(options, $(this).attr('data-facet'));
            options.behaviour_date_histogram_showall(options, obj, facet);
        }

        function clickDHLess(event) {
            event.preventDefault();
            var facet = selectFacet(options, $(this).attr('data-facet'));
            options.behaviour_date_histogram_showless(options, obj, facet);
        }

        /////// facet values /////////////////////////////////
        
        function setUIFacetResults(facet) {
            var el = facetElement("#facetview_filter_", facet["field"], obj);

            // remove any stuff that is going to be overwritten
            el.find(".facetview_date_histogram_short", obj).remove();
            el.find(".facetview_date_histogram_full", obj).remove();
            el.find('.facetview_filtervalue', obj).remove();
            
            if (!("values" in facet)) {
                return
            }
            
            var frag = undefined;
            if (facet.type === "terms") {
                frag = options.render_terms_facet_values(options, facet)
            } else if (facet.type === "range") {
                frag = options.render_range_facet_values(options, facet)
            } else if (facet.type === "geo_distance") {
                frag = options.render_geo_facet_values(options, facet)
            } else if (facet.type === "date_histogram") {
                frag = options.render_date_histogram_values(options, facet)
            }
            // FIXME: how to display statistical facet?
            if (frag) {
                el.append(frag)
            }
            
            options.behaviour_toggle_facet_open(options, obj, facet);
            
            // FIXME: probably all bindings should come with an unbind first
            // enable filter selection
            $('.facetview_filterchoice', obj).unbind('click', clickFilterChoice);
            $('.facetview_filterchoice', obj).bind('click', clickFilterChoice);
            
            // enable filter removal
            $('.facetview_filterselected', obj).unbind('click', clickClearFilter);
            $('.facetview_filterselected', obj).bind('click', clickClearFilter);

            // enable all/less on date histograms
            $(".facetview_date_histogram_showless", obj).unbind("click", clickDHLess).bind("click", clickDHLess);
            $(".facetview_date_histogram_showall", obj).unbind("click", clickDHAll).bind("click", clickDHAll);

            // bind the tooltips
            $(".facetview_tooltip_more").unbind("click", clickTooltipMore).bind("click", clickTooltipMore);
            $(".facetview_tooltip_less").unbind("click", clickTooltipLess).bind("click", clickTooltipLess);
        }
        
        /////// selected filters /////////////////////////////////
        
        function clickFilterChoice(event) {
            event.preventDefault()
            
            var field = $(this).attr("data-field");
            var facet = selectFacet(options, field);
            var value = {};
            if (facet.type === "terms") {
                value = $(this).attr("data-value");
            } else if (facet.type === "range") {
                var from = $(this).attr("data-from");
                var to = $(this).attr("data-to");
                if (from) { value["from"] = from }
                if (to) { value["to"] = to }
            } else if (facet.type === "geo_distance") {
                var from = $(this).attr("data-from");
                var to = $(this).attr("data-to");
                if (from) { value["from"] = from }
                if (to) { value["to"] = to }
            } else if (facet.type === "date_histogram") {
                var from = $(this).attr("data-from");
                var to = $(this).attr("data-to");
                if (from) { value["from"] = from }
                if (to) { value["to"] = to }
            }
            // FIXME: how to handle clicks on statistical facet (if that even makes sense) or terms_stats facet
            
            // update the options and the filter display.  No need to update
            // the facet, as we'll issue a search straight away and it will
            // get updated automatically
            selectFilter(field, value);
            options.behaviour_set_selected_filters(options, obj);
            
            // reset the result set to the beginning and search again
            options.from = 0;
            doSearch();
        }
        
        function selectFilter(field, value) {
            // make space for the filter in the active filters list
            if (!(field in options.active_filters)) {
                options.active_filters[field] = []
            }
            
            var facet = selectFacet(options, field)
            
            if (facet.type === "terms") {
                // get the current values for that filter
                var filter = options.active_filters[field];
                if ($.inArray(value, filter) === -1 ) {
                    filter.push(value)
                }
            } else if (facet.type === "range") {
                // NOTE: we are implicitly stating that range filters cannot be OR'd
                options.active_filters[field] = value
            } else if (facet.type === "geo_distance") {
                // NOTE: we are implicitly stating that geo distance range filters cannot be OR'd
                options.active_filters[field] = value
            } else if (facet.type === "date_histogram") {
                // NOTE: we are implicitly stating that date histogram filters cannot be OR'd
                options.active_filters[field] = value
            }

            // FIXME: statistical facet support here?
        }
        
        function deSelectFilter(facet, field, value) {
            if (field in options.active_filters) {
                var filter = options.active_filters[field];
                if (facet.type === "terms") {
                    var index = $.inArray(value, filter);
                    filter.splice(index, 1);
                    if (filter.length === 0) {
                        delete options.active_filters[field]
                    }
                } else if (facet.type === "range") {
                    delete options.active_filters[field]
                } else if (facet.type === "geo_distance") {
                    delete options.active_filters[field]
                } else if (facet.type === "date_histogram") {
                    delete options.active_filters[field]
                }
                // FIXME: statistical facet support?
            }
        }

        function clickClearFilter(event) {
            event.preventDefault();
            if ($(this).hasClass("facetview_inactive_link")) {
                return
            }
            
            var field = $(this).attr("data-field");
            var facet = selectFacet(options, field);
            var value = {};
            if (facet.type === "terms") {
                value = $(this).attr("data-value");
            } else if (facet.type === "range") {
                var from = $(this).attr("data-from");
                var to = $(this).attr("data-to");
                if (from) { value["from"] = from }
                if (to) { value["to"] = to }
            } else if (facet.type === "geo_distance") {
                var from = $(this).attr("data-from");
                var to = $(this).attr("data-to");
                if (from) { value["from"] = from }
                if (to) { value["to"] = to }
            } else if (facet.type == "date_histogram") {
                value = $(this).attr("data-from");
            }
            // FIXMe: statistical facet
            
            deSelectFilter(facet, field, value);
            publishSelectedFilters();
            
            // reset the result set to the beginning and search again
            options.from = 0;
            doSearch();
        }

        function publishSelectedFilters() {
            options.behaviour_set_selected_filters(options, obj);

            $('.facetview_filterselected', obj).unbind('click', clickClearFilter);
            $('.facetview_filterselected', obj).bind('click', clickClearFilter);
        }
        
        function facetVisibility() {
            $('.facetview_filters', obj).each(function() {
                var facet = selectFacet(options, $(this).attr('data-href'));
                var values = "values" in facet ? facet["values"] : [];
                var visible = !facet.disabled;
                if (!facet.disabled) {
                    if (facet.type === "terms") {
                        // terms facet becomes deactivated if the number of results is less than the deactivate threshold defined
                        visible = values.length > facet.deactivate_threshold;
                    } else if (facet.type === "range") {
                        // range facet becomes deactivated if there is a count of 0 in every value
                        var view = false;
                        for (var i = 0; i < values.length; i = i + 1) {
                            var val = values[i];
                            if (val.count > 0) {
                                view = true;
                                break
                            }
                        }
                        visible = view
                    } else if (facet.type === "geo_distance") {
                        // distance facet becomes deactivated if there is a count of 0 in every value
                        var view = false;
                        for (var i = 0; i < values.length; i = i + 1) {
                            var val = values[i];
                            if (val.count > 0) {
                                view = true;
                                break
                            }
                        }
                        visible = view
                    } else if (facet.type === "date_histogram") {
                        // date histogram facet becomes deactivated if there is a count of 0 in every value
                        var view = false;
                        for (var i = 0; i < values.length; i = i + 1) {
                            var val = values[i];
                            if (val.count > 0) {
                                view = true;
                                break
                            }
                        }
                        visible = view
                    }
                    // FIXME: statistical facet?
                }

                options.behaviour_facet_visibility(options, obj, facet, visible)
            });
        }

        // select the facet tooltip
        function clickTooltipMore(event) {
            event.preventDefault();
            var field = $(this).attr("data-field");
            var el = facetElement("#facetview_filter_", field, obj);
            el.find(".facetview_tooltip").hide();
            el.find(".facetview_tooltip_value").show();
        }

        // select the facet tooltip
        function clickTooltipLess(event) {
            event.preventDefault();
            var field = $(this).attr("data-field");
            var el = facetElement("#facetview_filter_", field, obj);
            el.find(".facetview_tooltip_value").hide();
            el.find(".facetview_tooltip").show();
        }
        
        /**************************************************************
         * result metadata/paging handling
         *************************************************************/
        
        // decrement result set
        function decrementPage(event) {
            event.preventDefault();
            if ($(this).hasClass("facetview_inactive_link")) {
                return
            }
            options.from = parseInt(options.from) - parseInt(options.page_size);
            options.from < 0 ? options.from = 0 : "";
            doSearch();
        };
        
        // increment result set
        function incrementPage(event) {
            event.preventDefault();
            if ($(this).hasClass("facetview_inactive_link")) {
                return
            }
            options.from = parseInt(options.from) + parseInt(options.page_size);
            doSearch();
        };
        
        /////// display results metadata /////////////////////////////////
        
        function setUIResultsMetadata() {
            if (!options.data.found) {
                $('.facetview_metadata', obj).html("");
                return
            }
            frag = options.render_results_metadata(options);
            $('.facetview_metadata', obj).html(frag);
            $('.facetview_decrement', obj).bind('click', decrementPage);
            $('.facetview_increment', obj).bind('click', incrementPage);
        }
        
        /**************************************************************
         * result set display
         *************************************************************/
        
        function setUINotFound() {
            frag = options.render_not_found();
            $('#facetview_results', obj).html(frag);
        }
        
        function setUISearchResults() {
            var frag = ""
            for (var i = 0; i < options.data.records.length; i++) {
                var record = options.data.records[i];
                frag += options.render_result_record(options, record)
            }
            $('#facetview_results', obj).html(frag);
            $('#facetview_results', obj).children().hide().fadeIn(options.fadein);
            // FIXME: is possibly a debug feature?
            // $('.facetview_viewrecord', obj).bind('click', viewrecord);
        }
        
        /**************************************************************
         * search handling
         *************************************************************/
        
        function querySuccess(rawdata, results) {
            if (options.debug) {
                addDebug(JSON.stringify(rawdata));
                addDebug(JSON.stringify(results))
            }
            
            // record the data coming from elasticsearch
            options.rawdata = rawdata;
            options.data = results;
            
            // if a post search callback is provided, run it
            if (typeof options.post_search_callback == 'function') {
                options.post_search_callback(options, obj);
            }
            
            // if a pre-render callback is provided, run it
            if (typeof options.pre_render_callback == 'function') {
                options.pre_render_callback(options, obj);
            }
            
            // for each facet, get the results and add them to the page
            for (var each = 0; each < options.facets.length; each++) {
                // get the facet, the field name and the size
                var facet = options.facets[each];

                // no need to populate any disabled facets
                if (facet.disabled) { continue }

                var field = facet['field'];
                var size = facet.hasOwnProperty("size") ? facet["size"] : options.default_facet_size;
                
                // get the records to be displayed, limited by the size and record against
                // the options object
                var records = results["facets"][field];
                // special rule for handling statistical, range and histogram facets
                if (records.hasOwnProperty("_type") && records["_type"] === "statistical") {
                    facet["values"] = records
                } else {
                    if (!records) { records = [] }
                    if (size) { // this means you can set the size of a facet to something false (like, false, or 0, and size will be ignored)
                        if (facet.type === "terms" && facet.ignore_empty_string) {
                            facet["values"] = [];
                            for (var i = 0; i < records.length; i++) {
                                if (facet.values.length > size) {
                                    break;
                                }
                                if (records[i].term !== "") {
                                    facet["values"].push(records[i]);
                                }
                            }
                        } else {
                            facet["values"] = records.slice(0, size)
                        }
                    } else {
                        facet["values"] = records
                    }
                }

                // set the results on the page
                if (!facet.hidden) {
                    setUIFacetResults(facet)
                }
            }
            
            // set the facet visibility
            facetVisibility();
            
            // add the results metadata (paging, etc)
            setUIResultsMetadata();
            
            // show the not found notification if necessary, otherwise render the results
            if (!options.data.found) {
                setUINotFound()
            } else {
                setUISearchResults()
            }
            
            // if a post-render callback is provided, run it
            if (typeof options.post_render_callback == 'function') {
                options.post_render_callback(options, obj);
            }
        }
        
        function queryComplete(jqXHR, textStatus) {
            options.behaviour_finished_searching(options, obj);
            options.searching = false;
        }

        function pruneActiveFilters() {
            for (var i = 0; i < options.facets.length; i++) {
                var facet = options.facets[i];
                if (facet.disabled) {
                    if (facet.field in options.active_filters) {
                        delete options.active_filters[facet.field];
                    }
                }
            }
            publishSelectedFilters();
        }
        
        function doSearch() {
            // FIXME: does this have any weird side effects?
            // if a search is currently going on, don't do anything
            if (options.searching) {
                // alert("already searching")
                return
            }
            options.searching = true; // we are executing a search right now

            // invalidate the existing short url
            options.current_short_url = false;
            
            // if a pre search callback is provided, run it
            if (typeof options.pre_search_callback === 'function') {
                options.pre_search_callback(options, obj);
            }
            
            // trigger any searching notification behaviour
            options.behaviour_show_searching(options, obj);

            // remove from the active filters any whose facets are disabled
            // (this may have happened during the pre-search callback, for example)
            pruneActiveFilters();

            // make the search query
            var queryobj = elasticSearchQuery({"options" : options});
            options.queryobj = queryobj
            if (options.debug) {
                var querystring = serialiseQueryObject(queryobj);
                addDebug(querystring)
            }
            
            // augment the URL bar if possible, and the share/save link
            urlFromOptions();
            
            // issue the query to elasticsearch
            doElasticSearchQuery({
                search_url: options.search_url,
                queryobj: queryobj,
                datatype: options.datatype,
                success: querySuccess,
                complete: queryComplete
            })
        }
        
        /**************************************************************
         * build all of the fragments that we want to render
         *************************************************************/
        
        // set the externally facing facetview options
        $.fn.facetview.options = deriveOptions();
        var options = $.fn.facetview.options;
        
        // render the facetview frame which will then be populated
        var thefacetview = options.render_the_facetview(options);
        var thesearchopts = options.render_search_options(options);
        var thefacets = options.render_facet_list(options);
        var searching = options.render_searching_notification(options);
        
        // now create the plugin on the page for each div
        var obj = undefined;
        return this.each(function() {
            // get this object
            obj = $(this);
            
            // what to do when ready to go
            var whenready = function() {
                // append the facetview object to this object
                obj.append(thefacetview);
                
                // add the search controls
                $(".facetview_search_options_container", obj).html(thesearchopts);
                
                // add the facets (empty at this stage), then set their visibility, which will fall back to the
                // worst case scenario for visibility - it means facets won't disappear after the search, only reappear
                if (thefacets != "") {
                    $('#facetview_filters', obj).html(thefacets);
                    facetVisibility();
                }
                
                // add the loading notification
                if (searching != "") {
                    $(".facetview_searching", obj).html(searching)
                }
                
                // populate all the page UI framework from the options
                uiFromOptions(options);
                
                // bind the search control triggers
                $(".facetview_startagain", obj).bind("click", clickStartAgain);
                $('.facetview_pagesize', obj).bind('click', clickPageSize);
                $('.facetview_order', obj).bind('click', clickOrder);
                $('.facetview_orderby', obj).bind('change', changeOrderBy);
                $('.facetview_searchfield', obj).bind('change', changeSearchField);
                $('.facetview_sharesave', obj).bind('click', clickShareSave);
                $('.facetview_freetext', obj).bindWithDelay('keyup', keyupSearchText, options.freetext_submit_delay);
                $('.facetview_force_search', obj).bind('click', clickSearch);
                $('.facetview_shorten_url', obj).bind('click', clickShortenUrl);
                $('.facetview_lengthen_url', obj).bind('click', clickLengthenUrl);
                
                // bind the facet control triggers
                $('.facetview_filtershow', obj).bind('click', clickFilterShow);
                $('.facetview_morefacetvals', obj).bind('click', clickMoreFacetVals);
                $('.facetview_sort', obj).bind('click', clickSort);
                $('.facetview_or', obj).bind('click', clickOr);
                
                // if a post initialisation callback is provided, run it
                if (typeof options.post_init_callback === 'function') {
                    options.post_init_callback(options, obj);
                }
                
                // if an initial search is requested, then issue it
                if (options.initialsearch) { doSearch() }
            };
            whenready();
        });
    }

    // facetview options are declared as a function so that they can be retrieved
    // externally (which allows for saving them remotely etc)
    $.fn.facetview.options = {};
    
})(jQuery);

jQuery(document).ready(function($) {

    var all_facets = {
        journal_article : {
            field : "_type",
            hidden: true
        },
        subject : {
            field: 'index.classification.exact',
            hidden: true
        },
        licence : {
            field: "index.license.exact",
            hidden: true
        },
        publisher : {
            field: "index.publisher.exact",
            hidden: true
        },
        country_publisher : {
            field: "index.country.exact",
            hidden: true
        },
        language : {
            field : "index.language.exact",
            hidden: true
        },

        // journal facets
        apc : {
            field : "index.has_apc.exact",
            hidden: true
        },
        seal : {
            field : "index.has_seal.exact",
            hidden: true
        },
        peer_review : {
            field : "bibjson.editorial_review.process.exact",
            hidden: true
        },
        year_added : {
            type: "date_histogram",
            field: "created_date",
            interval: "year",
            hidden: true
        },
        archiving_policy : {
            field : "bibjson.archiving_policy.policy.exact",
            hidden: true
        },

        // article facets
        journal_title : {
            field : "bibjson.journal.title.exact",
            hidden: true
        },
        year_published_histogram : {
            type: "date_histogram",
            field: "index.date",
            interval: "year",
            hidden: true
        },

        // toc facets
        issn : {
            field: 'index.issn.exact',
            hidden: true
        },

        volume : {
            field: 'bibjson.journal.volume.exact',
            hidden: true
        },

        issue : {
            field: 'bibjson.journal.number.exact',
            hidden: true
        },

        month_published_histogram : {
            type: 'date_histogram',
            field: 'index.date_toc_fv_month',
            interval: 'month',
            hidden: true}
    };

    var facet_list = [];
    facet_list.push(all_facets.journal_article);
    facet_list.push(all_facets.subject);
    facet_list.push(all_facets.journal_title);
    facet_list.push(all_facets.apc);
    facet_list.push(all_facets.seal);
    facet_list.push(all_facets.licence);
    facet_list.push(all_facets.publisher);
    facet_list.push(all_facets.country_publisher);
    facet_list.push(all_facets.language);
    facet_list.push(all_facets.peer_review);
    facet_list.push(all_facets.year_added);
    facet_list.push(all_facets.year_published_histogram);
    facet_list.push(all_facets.archiving_policy);
    facet_list.push(all_facets.issn);
    facet_list.push(all_facets.volume);
    facet_list.push(all_facets.issue);
    facet_list.push(all_facets.month_published_histogram);

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

        // start the main box that all the details go in
        result += "<div class='span12'>";

        // add the journal icon
        result += "<div class='pull-left' style='width: 4%'>";
        result += "<i style='font-size: 24px' class='icon icon-book'></i>";
        result += "</div>";

        result += "<div class='pull-left' style='width: 93%'>";

        result += "<div class='row-fluid'><div class='span10'>";

        // set the title
        if (resultobj.bibjson.title) {
            result += "<span class='title'><a target='_top' href='"+ doaj_url + "/toc/" + journal_toc_id(resultobj) + "'>" + escapeHtml(resultobj.bibjson.title) + "</a></span><br>";
        }

        // set the alternative title
        if (resultobj.bibjson.alternative_title) {
            result += "<span class='alternative_title' style='color: #aaaaaa'>" + escapeHtml(resultobj.bibjson.alternative_title) + "</span><br>";
        }

        // set the issn
        if (resultobj.bibjson && resultobj.bibjson.identifier) {
            var ids = resultobj.bibjson.identifier;
            var pissns = [];
            var eissns = [];
            for (var i = 0; i < ids.length; i++) {
                if (ids[i].type === "pissn") {
                    pissns.push(escapeHtml(ids[i].id))
                } else if (ids[i].type === "eissn") {
                    eissns.push(escapeHtml(ids[i].id))
                }
            }
            if (pissns.length > 0 || eissns.length > 0) {
                result += "ISSN: ";
                if (pissns.length > 0) {
                    result += pissns.join(", ") + "&nbsp;(Print)";
                }
                if (eissns.length > 0) {
                    if (pissns.length > 0) {
                        result += "; ";
                    }
                    result += eissns.join(", ") + "&nbsp;(Online)";
                }
                result += "<br>";
            }
        }

        // set the homepage url
        // FIXME: how to escape the html here?
        if (resultobj.bibjson && resultobj.bibjson.link) {
            var ls = resultobj.bibjson.link;
            for (var i = 0; i < ls.length; i++) {
                var t = ls[i].type;
                if (t == 'homepage') {
                    result += "<a target='_top' href='" + ls[i].url + "'>" + ls[i].url + "</a><br>";
                }
            }
        }

        // close the main details box
        result += "</div>";

        // start the journal properties side-bar
        result += "<div class='span2' align='right'>";

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
                    result += "<a href='" + urls[1] + "' title='" + ltitle + "' target='_blank'><img src='" + doaj_url + urls[0] + "' width='80' height='15' valign='middle' alt='" + ltitle + "'></a><br>"
                } else {
                    result += "<strong>License: " + escapeHtml(ltitle) + "</strong><br>"
                }
            }
        }

        // show the seal if it's set
        if (resultobj.admin && resultobj.admin.seal) {
            result += "<img src='" + doaj_url + "/static/doaj/images/seal_short.png' title='Awarded the DOAJ Seal' alt='Seal icon: awarded the DOAJ Seal'>​​<br>";
        }

        // close the journal properties side-bar
        result += "</div>";

        // close off the result with the ending strings, and then return
        result += "</div></div>";
        result += options.resultwrap_end;
        return result;
    }

    function renderPublicArticle(options, resultobj) {

        function makeCitation(record) {
            // Journal name. YYYY;32(4):489-98

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
                        issns.push(escapeHtml(ids[i].id))
                    }
                }
            }

            var citation = "";

            // journal title
            if (ctitle) {
                if (issns.length > 0) {
                    citation += "<a target='_top' href='"+ doaj_url + "/toc/" + issns[0] + "'>" + escapeHtml(ctitle.trim()) + "</a>";
                } else {
                    citation += escapeHtml(ctitle.trim());
                }
                citation += ". ";
            }

            // year
            if (cyear) {
                // if (citation !== "") { citation += " " }
                citation += escapeHtml(cyear) + ";";
            }

            // volume
            if (cvol) {
                // if (citation !== "") { citation += "" }
                citation += escapeHtml(cvol);
            }

            if (ciss) {
                // if (citation !== "") { citation += ", " }
                citation += "(" + escapeHtml(ciss) + ")";
            }

            if (cstart || cend) {
                if (citation !== "") { citation += ":" }
                /*
                if ((cstart && !cend) || (!cstart && cend)) {
                    citation += "p ";
                } else {
                    citation += "Pp ";
                }
                */
                if (cstart) {
                    citation += escapeHtml(cstart);
                }
                if (cend) {
                    if (cstart) {
                        citation += "-"
                    }
                    citation += escapeHtml(cend);
                }
            }

            return citation;
        }

        // start off the string to be rendered
        var result = options.resultwrap_start;
        result += "<div class='row-fluid'>";

        // start the main box that all the details go in
        result += "<div class='span12'>";

        // add the article icon
        result += "<div class='pull-left' style='width: 4%'>";
        result += "<i style='font-size: 24px' class='icon icon-file'></i>";
        result += "</div>";

        result += "<div class='pull-left' style='width: 90%'>";

        // set the title
        if (resultobj.bibjson.title) {
            result += "<span class='title'><a target='_top' href='"+ doaj_url + "/article/" + resultobj.id + "'>" + escapeHtml(resultobj.bibjson.title) + "</a></span><br>";
        }

        // set the authors
        if (resultobj.bibjson && resultobj.bibjson.author && resultobj.bibjson.author.length > 0) {
            var anames = [];
            var authors = resultobj.bibjson.author;
            for (var i = 0; i < authors.length; i++) {
                var author = authors[i];
                if (author.name) {
                    anames.push(escapeHtml(author.name));
                }
            }
            result += "<em>" + anames.join(", ") + "</em><br>";
        }

        // set the citation
        var cite = makeCitation(resultobj);
        if (cite) {
            result += cite;
        }

        // set the doi
        if (resultobj.bibjson && resultobj.bibjson.identifier) {
            var ids = resultobj.bibjson.identifier;
            for (var i = 0; i < ids.length; i++) {
                if (ids[i].type === "doi") {
                    var doi = ids[i].id;
                    var tendot = doi.indexOf("10.");
                    var url = "https://doi.org/" + escapeHtml(doi.substring(tendot));
                    result += " DOI <a target='_top' href='" + url + "'>" + escapeHtml(doi.substring(tendot)) + "</a>";
                }
            }
        }

        result += "<br>";

        // extract the fulltext link if there is one
        var ftl = false;
        if (resultobj.bibjson && resultobj.bibjson.link) {
            var ls = resultobj.bibjson.link;
            for (var i = 0; i < ls.length; i++) {
                var t = ls[i].type;
                if (t == 'fulltext') {
                    ftl = ls[i].url;
                }
            }
        }

        // create the abstract section if desired
        if (resultobj.bibjson.abstract || ftl) {
            if (resultobj.bibjson.abstract) {
                result += '<a class="abstract_action" href="" rel="' + resultobj.id + '"><strong>Abstract</strong></a>';
            }
            if (ftl) {
                if (resultobj.bibjson.abstract) {
                    result += " | ";
                }
                result += "<a target='_top' href='" + ftl + "'>Full Text</a>";
            }

            if (resultobj.bibjson.abstract) {
                result += '<div class="abstract_text" rel="' + resultobj.id + '">' + escapeHtml(resultobj.bibjson.abstract) + '</div>';
            }
        }

        // close the main details box
        result += "</div></div>";

        // close off the main result
        result += "</div>";

        // close off the result and return
        result += options.resultwrap_end;
        return result;
    }

    $('.facetview.journals_and_articles').facetview($.extend({
        search_url: doaj_url + '/query/journal,article/_search?ref=fqw',
        pushstate: false,                      // Do not use the url state, this may interfere with the host website
        render_results_metadata: doajPager,
        render_result_record: publicSearchResult,
        render_search_options: $.noop,         // The fixed query widget does not require the search box or its accoutrements
        render_facet_list: $.noop,
        behaviour_set_selected_filters : $.noop,
        post_render_callback: doajFixedQueryWidgetPostRender,
        facets: facet_list,
        default_operator : "AND"              // This can be overridden by the properties we extend from widget_fv_opts

        /* The following are the user-configurable settings for the widget, bundled in widget_fv_opts via QUERY_OPTIONS
             page_size
             from
             q
             searchfield
             sort
             default_operator
             predefined_filters
        */
    }, widget_fv_opts));
});

function iso_datetime2date(isodate_str) {
    /* >>> '2003-04-03T00:00:00Z'.substring(0,10)
     * "2003-04-03"
     */
    return isodate_str.substring(0,10);
}

function iso_datetime2date_and_time(isodate_str) {
    /* >>> "2013-12-13T22:35:42Z".replace('T',' ').replace('Z','')
     * "2013-12-13 22:35:42"
     */
    if (!isodate_str) { return "" }
    return isodate_str.replace('T',' ').replace('Z','')
}

function journal_toc_id(journal) {
    // if e-issn is available, use that
    // if not, but a p-issn is available, use that
    // if neither ISSN is available, use the internal ID
    var ids = journal.bibjson.identifier;
    var pissns = [];
    var eissns = [];
    for (var i = 0; i < ids.length; i++) {
        if (ids[i].type === "pissn") {
            pissns.push(ids[i].id)
        } else if (ids[i].type === "eissn") {
            eissns.push(ids[i].id)
        }
    }

    var toc_id = undefined;
    if (eissns.length > 0) { toc_id = eissns[0]; }
    if (!toc_id && pissns.length > 0) { toc_id = pissns[0]; }
    if (!toc_id) { toc_id = journal.id; }

    return toc_id;
}

